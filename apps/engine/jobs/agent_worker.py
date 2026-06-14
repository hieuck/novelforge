"""
Background agent worker.

Polls the `jobs` table for queued agent tasks and executes them autonomously
without a live WebSocket connection. Progress and results are written back to
the DB so the frontend can poll or stream via /ws/jobs/{id}.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from db.session import SessionLocal
from models.extra import Job
from models.chapter import Chapter
from models.extra import Character, Lore, TimelineItem
from models.project import Project

logger = logging.getLogger("novelforge.worker")

# ── Worker registry ───────────────────────────────────────────────────────────

_running: dict[str, asyncio.Task] = {}   # job_id → asyncio.Task
_cancel_flags: dict[str, asyncio.Event] = {}  # job_id → cancel event

POLL_INTERVAL = 3.0   # seconds between DB polls for new jobs
MAX_CONCURRENT = 3    # max simultaneous agent jobs


# ── Public API ────────────────────────────────────────────────────────────────

def enqueue(job_id: str) -> None:
    """Signal the worker loop to pick up a specific job immediately."""
    # Worker loop will find it on next poll; this is a no-op hint
    pass


def cancel(job_id: str) -> None:
    flag = _cancel_flags.get(job_id)
    if flag:
        flag.set()


async def start_worker_loop() -> None:
    """Long-running coroutine — attach to FastAPI lifespan."""
    logger.info("Agent worker loop started")
    while True:
        try:
            await _poll_and_dispatch()
        except Exception as exc:
            logger.error("Worker poll error: %s", exc, exc_info=True)
        await asyncio.sleep(POLL_INTERVAL)


# ── Poll & dispatch ───────────────────────────────────────────────────────────

async def _poll_and_dispatch() -> None:
    if len(_running) >= MAX_CONCURRENT:
        return  # at capacity

    db = SessionLocal()
    try:
        pending = (
            db.query(Job)
            .filter(Job.status == "queued", Job.kind == "agent")
            .order_by(Job.created_at.asc())
            .limit(MAX_CONCURRENT - len(_running))
            .all()
        )
        for job in pending:
            if job.id not in _running:
                flag = asyncio.Event()
                _cancel_flags[job.id] = flag
                task = asyncio.create_task(_run_job(job.id, flag))
                _running[job.id] = task
                task.add_done_callback(lambda t, jid=job.id: _running.pop(jid, None))
                logger.info("Dispatched job %s", job.id)
    finally:
        db.close()


# ── Job execution ─────────────────────────────────────────────────────────────

async def _run_job(job_id: str, cancel_flag: asyncio.Event) -> None:
    _update_job(job_id, status="running")
    logs: list[str] = []

    def log(msg: str) -> None:
        logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {msg}")
        _update_job(job_id, logs=logs)

    try:
        db = SessionLocal()
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return
        params: dict[str, Any] = job.params or {}
        pid: str = params.get("project_id", job.project_id)
        task_text: str = params.get("task", "")
        lang: str = params.get("language", "vi")
        db.close()

        if not task_text.strip():
            _update_job(job_id, status="failed", error="task is empty")
            return

        log(f"Starting: {task_text[:100]}")

        from routes.ai import _get_settings, _system_prompt
        from services.context.builder import ProjectContext
        from services.providers.openai_compat import build_client
        from routes.agent import (
            PLAN_SYSTEM, ADAPT_SYSTEM, _parse_plan, _renumber,
            _tool_result_summary, _memory_msgs, _adapt_plan,
            _create_char, _update_character, _create_lore, _update_lore,
            _create_chapter, _update_chapter, _update_summary,
            _create_timeline_event, _read_chapter, _read_characters,
            _read_lore, _read_timeline, _read_project_summary,
            _analyze_consistency, _search_content,
            _extract_chapter_content_from_memory,
        )

        settings = _get_settings()
        client = build_client(settings)

        ctx = ProjectContext(pid or None)
        if pid:
            await ctx.load()

        ctx_summary = ""
        if ctx.project:
            ctx_summary += f"Project: {ctx.project.title}\n"
        if ctx.characters:
            ctx_summary += (
                f"Characters ({len(ctx.characters)}): "
                + ", ".join(f"{c.name} (id={c.id})" for c in ctx.characters[:8])
                + "\n"
            )
        if ctx.chapters:
            ctx_summary += f"Chapters ({len(ctx.chapters)}): " + ", ".join(
                f'"{c.title}" (id={c.id})' for c in ctx.chapters[:5]
            ) + "\n"

        # ── Plan ──────────────────────────────────────────────────────────────
        log("Planning...")
        plan_messages = [
            {"role": "system", "content": PLAN_SYSTEM},
            {"role": "user", "content": f"Language: {lang}\nTask: {task_text}\n{ctx_summary}"},
        ]
        raw = await client.chat_messages(plan_messages)
        steps = _renumber(_parse_plan(raw))
        log(f"Plan: {len(steps)} steps — " + ", ".join(s.get("tool", "?") for s in steps))
        _update_job(job_id, logs=logs, meta={"plan": steps})

        exec_system = _system_prompt(ctx) + f"\nLanguage: {lang}\n"
        memory: list[str] = []
        completed: list[dict] = []

        # ── Execute steps ─────────────────────────────────────────────────────
        step_index = 0
        while step_index < len(steps):
            if cancel_flag.is_set():
                log("Cancelled by user.")
                _update_job(job_id, status="cancelled", logs=logs)
                return

            step = steps[step_index]
            step_index += 1
            tool = step.get("tool", "generate_text")
            p = step.get("params", {})
            desc = step.get("description", tool)

            log(f"Step {step['step']}/{len(steps)}: {tool} — {desc}")

            result: dict = {}
            is_read = tool.startswith("read_") or tool in ("analyze_consistency", "search_content")

            try:
                if tool == "analyze_consistency":
                    raw_data = _analyze_consistency(pid)
                    is_read = True
                    msgs = [
                        {"role": "system", "content": exec_system},
                        *_memory_msgs(memory),
                        {"role": "user", "content": (
                            f"Analyze project for consistency issues.\n"
                            + "\n".join(f"- Ch{c['scene_order']+1} '{c['title']}': {c['preview'][:300]}" for c in raw_data["chapters"])
                            + "\nList all issues. If none, say 'No issues found.'"
                        )},
                    ]
                    report = await client.chat_messages(msgs)
                    result = {"report": report, "chapter_count": raw_data["chapter_count"]}

                elif tool == "search_content":
                    result = _search_content(pid, p)
                    is_read = True

                elif tool == "read_chapter":
                    result = _read_chapter(pid, p)
                elif tool == "read_characters":
                    result = _read_characters(pid)
                elif tool == "read_lore":
                    result = _read_lore(pid)
                elif tool == "read_timeline":
                    result = _read_timeline(pid)
                elif tool == "read_project_summary":
                    result = _read_project_summary(pid)

                elif tool == "create_character" and pid:
                    if not p.get("personality"):
                        g = await client.chat_messages([
                            {"role": "system", "content": exec_system},
                            *_memory_msgs(memory),
                            {"role": "user", "content": (
                                f"Return JSON for character '{p.get('name','')}' role='{p.get('role','')}'. "
                                "Keys: personality, goals, secrets, appearance, age. JSON only."
                            )},
                        ])
                        try:
                            m = re.search(r"\{.*\}", re.sub(r"```[a-z]*\n?", "", g), re.DOTALL)
                            if m:
                                p = {**json.loads(m.group(0)), **p}
                        except Exception:
                            pass
                    result = _create_char(pid, p)

                elif tool == "update_character" and pid:
                    if not p.get("character_id"):
                        name_hint = (p.get("name") or "").strip()
                        if name_hint:
                            for entry in memory:
                                if "[read_characters]" not in entry:
                                    continue
                                m = re.search(rf"\b{re.escape(name_hint)}\b\s*\(id=([^)]+)\)", entry, re.IGNORECASE)
                                if m:
                                    p = {**p, "character_id": m.group(1)}
                                    break
                    result = _update_character(pid, p)

                elif tool == "create_lore" and pid:
                    if not p.get("description"):
                        g = await client.chat_messages([
                            {"role": "system", "content": exec_system},
                            *_memory_msgs(memory),
                            {"role": "user", "content": f"Describe '{p.get('name','')}' ({p.get('lore_type','term')}) in 2-3 sentences."},
                        ])
                        p = {**p, "description": g.strip()}
                    result = _create_lore(pid, p)

                elif tool == "update_lore" and pid:
                    result = _update_lore(pid, p)

                elif tool == "create_chapter" and pid:
                    if not p.get("content") or len(p.get("content", "")) < 100:
                        char_ctx = ctx.character_context()
                        g = await client.chat_messages([
                            {"role": "system", "content": exec_system + (f"\nCharacters:\n{char_ctx[:2000]}" if char_ctx else "")},
                            *_memory_msgs(memory),
                            {"role": "user", "content": f"Write chapter '{p.get('title','Chapter')}'. 400-600 words."},
                        ])
                        p = {**p, "content": g.strip()}
                    result = _create_chapter(pid, p)

                elif tool == "update_chapter" and pid:
                    chapter_id = p.get("chapter_id", "")
                    existing_content = _extract_chapter_content_from_memory(memory, chapter_id)
                    if not p.get("content"):
                        data = {"content": existing_content} if existing_content else _read_chapter(pid, p)
                        if isinstance(data, dict) and "error" not in data:
                            g = await client.chat_messages([
                                {"role": "system", "content": exec_system},
                                *_memory_msgs(memory),
                                {"role": "user", "content": (
                                    f"Rewrite chapter '{data.get('title')}'.\n"
                                    f"Original:\n{data.get('content','')[:3000]}\nTask: {desc}"
                                )},
                            ])
                            p = {**p, "content": g.strip()}
                    result = _update_chapter(pid, p)

                elif tool == "update_summary" and pid:
                    if not p.get("summary"):
                        g = await client.chat_messages([
                            {"role": "system", "content": exec_system},
                            *_memory_msgs(memory),
                            {"role": "user", "content": f"Write a 2-3 paragraph summary for: {task_text}"},
                        ])
                        p = {**p, "summary": g.strip()}
                    result = _update_summary(pid, p)

                elif tool == "create_timeline_event" and pid:
                    if not p.get("description"):
                        g = await client.chat_messages([
                            {"role": "system", "content": exec_system},
                            *_memory_msgs(memory),
                            {"role": "user", "content": f"Describe event '{p.get('title','Event')}' in 1-2 sentences."},
                        ])
                        p = {**p, "description": g.strip()}
                    result = _create_timeline_event(pid, p)

                else:  # generate_text
                    g = await client.chat_messages([
                        {"role": "system", "content": exec_system},
                        *_memory_msgs(memory),
                        {"role": "user", "content": p.get("prompt", desc)},
                    ])
                    result = {"text": g, "purpose": p.get("purpose", "")}

            except Exception as exc:
                logger.error("Worker step %s %s: %s", tool, step["step"], exc, exc_info=True)
                result = {"error": str(exc)}

            memory.append(_tool_result_summary(tool, result))
            completed.append({**step, "result": result})
            log(f"  ✓ {_tool_result_summary(tool, result)[:120]}")
            _update_job(job_id, logs=logs)

            # Adaptive re-plan after read tools when at end of plan
            if is_read and "error" not in result and step_index >= len(steps):
                memory_text = "\n".join(memory)
                adapt_msgs = [
                    {"role": "system", "content": ADAPT_SYSTEM},
                    {"role": "user", "content": (
                        f"Language: {lang}\nOriginal task: {task_text}\n\n"
                        f"Completed ({len(completed)}):\n{memory_text}\n\n"
                        "What additional steps are needed? Return [] if done."
                    )},
                ]
                try:
                    raw = await client.chat_messages(adapt_msgs)
                    new_steps = _parse_plan(raw)
                    if not (len(new_steps) == 1 and "Help with the writing task" in new_steps[0].get("params", {}).get("prompt", "")):
                        steps = steps + _renumber(new_steps, start=len(steps) + 1)
                        log(f"Adapted: {len(new_steps)} more steps added")
                        _update_job(job_id, logs=logs, meta={"plan": steps})
                except Exception:
                    pass

        # ── Build summary ─────────────────────────────────────────────────────
        parts: list[str] = []
        for kind, label in [
            ("create_character", "character(s) created"),
            ("update_character", "character(s) updated"),
            ("create_lore",      "lore item(s) created"),
            ("update_lore",      "lore item(s) updated"),
            ("create_chapter",   "chapter(s) created"),
            ("update_chapter",   "chapter(s) updated"),
            ("create_timeline_event", "timeline event(s) created"),
        ]:
            items = [s for s in completed if s["tool"] == kind and "error" not in s.get("result", {})]
            if items:
                names = ", ".join(
                    s["result"].get("name") or s["result"].get("title") or "?"
                    for s in items
                )
                parts.append(f"{len(items)} {label}: {names}")

        summary = ". ".join(parts) + "." if parts else "Completed."
        log(f"Done. {summary}")

        _update_job(
            job_id,
            status="done",
            logs=logs,
            result=json.dumps({
                "summary": summary,
                "steps_completed": len(completed),
                "plan": steps,
            }),
            meta={"plan": steps},
        )

    except asyncio.CancelledError:
        log("Task cancelled.")
        _update_job(job_id, status="cancelled", logs=logs)
    except Exception as exc:
        logger.error("Job %s failed: %s", job_id, exc, exc_info=True)
        _update_job(job_id, status="failed", error=str(exc), logs=logs)
    finally:
        _cancel_flags.pop(job_id, None)


# ── DB helpers ────────────────────────────────────────────────────────────────

def _update_job(
    job_id: str,
    *,
    status: str | None = None,
    logs: list[str] | None = None,
    result: str | None = None,
    error: str | None = None,
    meta: dict | None = None,
) -> None:
    db = SessionLocal()
    try:
        j = db.query(Job).filter(Job.id == job_id).first()
        if not j:
            return
        if status:
            j.status = status
        if logs is not None:
            # Store logs + optional meta in result field as JSON
            payload: dict = {"logs": logs}
            if meta:
                payload["meta"] = meta
            if result is not None:
                try:
                    payload["output"] = json.loads(result)
                except Exception:
                    payload["output"] = result
            j.result = json.dumps(payload, ensure_ascii=False)
        elif result is not None:
            j.result = result
        if error:
            j.error = error
        j.updated_at = datetime.now(timezone.utc)
        db.commit()
    except Exception as exc:
        logger.warning("DB update job %s failed: %s", job_id, exc)
    finally:
        db.close()
