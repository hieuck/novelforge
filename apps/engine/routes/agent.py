"""AI Agent - agentic loop: plan → execute tools (with memory) → adapt → stream."""
from __future__ import annotations

import asyncio
import json
import logging
import re
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from db.session import SessionLocal
from models.chapter import Chapter
from models.extra import Character, Lore, TimelineItem
from models.project import Project
from routes.ai import _get_settings, _system_prompt
from services.context.builder import ProjectContext
from services.providers.openai_compat import build_client

logger = logging.getLogger("novelforge.agent")
router = APIRouter()

# ── Plan prompt ───────────────────────────────────────────────────────────────

PLAN_SYSTEM = """You are a novel-writing agent. Given the user task and project context, produce a JSON execution plan.
Return ONLY a valid JSON array. Each element: {"step":N,"tool":"name","description":"...","params":{}}

Available tools:
  analyze_consistency {query?, kind?(chapter|character|lore|all)}
  search_content      {query, kind?(chapter|character|lore|all)}
  create_character    {name, role, age, personality, goals, secrets, appearance}
  update_character    {character_id, name?, role?, personality?, goals?, secrets?, appearance?, notes?}
  create_lore         {name, lore_type(location|magic|organization|technology|term), description, tags:[]}
  update_lore         {lore_id, name?, description?, tags?}
  create_chapter      {title, content, scene_order}
  update_chapter      {chapter_id, title?, content?, status?}
  update_summary      {summary}
  create_timeline_event {title, event_date?, relative_order?, description, involved_characters:[]}
  read_chapter        {chapter_id}
  read_characters     {}
  read_lore           {}
  read_timeline       {}
  read_project_summary {}
  generate_text       {prompt, purpose}
  ask_user            {question}

Rules:
- Use read_* tools first when the task involves editing or improving existing content.
- Use update_chapter when the task is to revise an existing chapter.
- Use read_characters before update_character so you have the real character IDs.
- Use read_lore before update_lore so you have the real lore IDs.
- Use read_lore when the task involves referencing or extending worldbuilding.
- Use ask_user when the task is ambiguous and needs clarification before proceeding.
- Use search_content to find specific scenes, characters, or passages by keyword before read_chapter.
- Use analyze_consistency when the task involves checking plot consistency, continuity errors, or character contradictions.
- Keep plans concise (1-5 steps usually). Only include steps that are necessary.
- For multi-step tasks, use read tools early to gather IDs before write tools."""

# ── Adapt prompt (re-plan after reading data) ─────────────────────────────────

ADAPT_SYSTEM = """You are a novel-writing agent. Based on the data just read and the original task,
decide the next steps.
Return ONLY a valid JSON array of remaining steps (may be empty [] if done).
Each element: {"step":N,"tool":"name","description":"...","params":{}}

Same tools available as before. Use the actual IDs and content from the read data.
If nothing more is needed, return []."""


# ── Tool implementations ──────────────────────────────────────────────────────

def _create_char(pid: str, p: dict) -> dict:
    from services.search import index_character
    db = SessionLocal()
    try:
        c = Character(
            id=str(uuid.uuid4()), project_id=pid,
            name=p.get("name", "?"), role=p.get("role"),
            age=str(p["age"]) if p.get("age") else None,
            personality=p.get("personality"), appearance=p.get("appearance"),
            goals=p.get("goals"), secrets=p.get("secrets"),
        )
        db.add(c)
        db.commit()
        db.refresh(c)
        index_character(c.id, pid, c.name or "", c.personality or "", c.goals or "", "")
        return {"id": c.id, "name": c.name, "role": c.role}
    finally:
        db.close()


def _update_character(pid: str, p: dict) -> dict:
    from services.search import index_character
    character_id = p.get("character_id", "")
    if not character_id:
        return {"error": "character_id required"}
    db = SessionLocal()
    try:
        c = db.query(Character).filter(
            Character.id == character_id, Character.project_id == pid
        ).first()
        if not c:
            return {"error": f"Character {character_id} not found"}
        for field in ("name", "role", "personality", "appearance", "goals", "secrets", "notes"):
            if field in p:
                setattr(c, field, p[field])
        if "age" in p:
            c.age = str(p["age"])
        c.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(c)
        index_character(c.id, pid, c.name or "", c.personality or "", c.goals or "", "")
        return {"id": c.id, "name": c.name, "role": c.role, "updated": True}
    finally:
        db.close()


def _create_lore(pid: str, p: dict) -> dict:
    from services.search import index_lore
    db = SessionLocal()
    try:
        lore_obj = Lore(
            id=str(uuid.uuid4()), project_id=pid,
            name=p.get("name", "?"), lore_type=p.get("lore_type", "term"),
            description=p.get("description"), tags=p.get("tags", []),
        )
        db.add(lore_obj)
        db.commit()
        db.refresh(lore_obj)
        index_lore(lore_obj.id, pid, lore_obj.name or "", lore_obj.description or "")
        return {"id": lore_obj.id, "name": lore_obj.name, "lore_type": lore_obj.lore_type}
    finally:
        db.close()


def _create_chapter(pid: str, p: dict) -> dict:
    from services.search import index_chapter
    db = SessionLocal()
    try:
        ct = p.get("content", "")
        wc = len(ct.split())
        c = Chapter(
            id=str(uuid.uuid4()), project_id=pid,
            title=p.get("title", "Chapter"), content=ct,
            scene_order=p.get("scene_order", 0), status="draft", word_count=wc,
        )
        db.add(c)
        db.commit()
        db.refresh(c)
        index_chapter(c.id, pid, c.title or "", ct)
        return {"id": c.id, "title": c.title, "word_count": wc}
    finally:
        db.close()


def _update_chapter(pid: str, p: dict) -> dict:
    from services.search import index_chapter
    chapter_id = p.get("chapter_id", "")
    if not chapter_id:
        return {"error": "chapter_id required"}
    db = SessionLocal()
    try:
        c = db.query(Chapter).filter(
            Chapter.id == chapter_id, Chapter.project_id == pid
        ).first()
        if not c:
            return {"error": f"Chapter {chapter_id} not found"}
        if "title" in p:
            c.title = p["title"]
        if "content" in p:
            c.content = p["content"]
            c.word_count = len(p["content"].split())
        if "status" in p:
            c.status = p["status"]
        c.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(c)
        index_chapter(c.id, pid, c.title or "", c.content or "")
        return {"id": c.id, "title": c.title, "word_count": c.word_count, "updated": True}
    finally:
        db.close()


def _update_summary(pid: str, p: dict) -> dict:
    db = SessionLocal()
    try:
        proj = db.query(Project).filter(Project.id == pid).first()
        if proj:
            proj.summary = p.get("summary", "")
            proj.updated_at = datetime.now(timezone.utc)
            db.commit()
        return {"updated": True}
    finally:
        db.close()


def _analyze_consistency(pid: str) -> dict:
    """Load all chapters and return their titles + first 800 chars for LLM analysis."""
    db = SessionLocal()
    try:
        chapters = (
            db.query(Chapter)
            .filter(Chapter.project_id == pid)
            .order_by(Chapter.scene_order.asc())
            .all()
        )
        characters = (
            db.query(Character)
            .filter(Character.project_id == pid)
            .order_by(Character.name.asc())
            .all()
        )
        return {
            "chapters": [
                {
                    "id": c.id,
                    "title": c.title,
                    "scene_order": c.scene_order,
                    "preview": (c.content or "")[:800],
                }
                for c in chapters
            ],
            "characters": [
                {"id": c.id, "name": c.name, "role": c.role, "personality": c.personality}
                for c in characters[:20]
            ],
            "chapter_count": len(chapters),
            "character_count": len(characters),
        }
    finally:
        db.close()


def _search_content(pid: str, p: dict) -> dict:
    """FTS5 search across chapters, characters, and lore for the project."""
    from services.search import search_project
    query = (p.get("query") or "").strip()
    if not query:
        return {"error": "query required"}
    kind = (p.get("kind") or "all").lower()
    raw = search_project(pid, query, limit=10)
    # Filter by kind if specified
    if kind != "all":
        raw = [r for r in raw if r.get("kind") == kind]
    return {
        "query": query,
        "results": [
            {
                "id": r.get("id"),
                "title": r.get("title"),
                "kind": r.get("kind"),
                "excerpt": r.get("excerpt", ""),
            }
            for r in raw
        ],
        "count": len(raw),
    }


def _update_lore(pid: str, p: dict) -> dict:
    from services.search import index_lore
    lore_id = p.get("lore_id", "")
    if not lore_id:
        return {"error": "lore_id required"}
    db = SessionLocal()
    try:
        item = db.query(Lore).filter(
            Lore.id == lore_id, Lore.project_id == pid
        ).first()
        if not item:
            return {"error": f"Lore {lore_id} not found"}
        if "name" in p:
            item.name = p["name"]
        if "description" in p:
            item.description = p["description"]
        if "tags" in p:
            item.tags = p["tags"]
        item.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(item)
        index_lore(item.id, pid, item.name or "", item.description or "")
        return {"id": item.id, "name": item.name, "lore_type": item.lore_type, "updated": True}
    finally:
        db.close()


def _read_timeline(pid: str) -> dict:
    db = SessionLocal()
    try:
        items = (
            db.query(TimelineItem)
            .filter(TimelineItem.project_id == pid)
            .order_by(TimelineItem.created_at.asc())
            .all()
        )
        return {
            "events": [
                {
                    "id": item.id,
                    "title": item.title,
                    "event_date": item.event_date,
                    "relative_order": item.relative_order,
                    "description": item.description,
                    "involved_characters": item.involved_characters or [],
                }
                for item in items
            ],
            "count": len(items),
        }
    finally:
        db.close()


def _create_timeline_event(pid: str, p: dict) -> dict:
    db = SessionLocal()
    try:
        item = TimelineItem(
            id=str(uuid.uuid4()), project_id=pid,
            title=p.get("title", "Event"),
            event_date=p.get("event_date"),
            relative_order=p.get("relative_order"),
            description=p.get("description"),
            involved_characters=p.get("involved_characters", []),
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return {"id": item.id, "title": item.title, "event_date": item.event_date}
    finally:
        db.close()


def _read_chapter(pid: str, p: dict) -> dict:
    chapter_id = p.get("chapter_id", "")
    if not chapter_id:
        return {"error": "chapter_id required"}
    db = SessionLocal()
    try:
        c = db.query(Chapter).filter(
            Chapter.id == chapter_id, Chapter.project_id == pid
        ).first()
        if not c:
            return {"error": f"Chapter {chapter_id} not found"}
        return {
            "id": c.id,
            "title": c.title,
            "content": c.content or "",
            "word_count": c.word_count,
            "status": c.status,
            "scene_order": c.scene_order,
        }
    finally:
        db.close()


def _read_characters(pid: str) -> dict:
    db = SessionLocal()
    try:
        chars = (
            db.query(Character)
            .filter(Character.project_id == pid)
            .order_by(Character.name.asc())
            .all()
        )
        return {
            "characters": [
                {
                    "id": c.id,
                    "name": c.name,
                    "role": c.role,
                    "personality": c.personality,
                    "goals": c.goals,
                    "appearance": c.appearance,
                }
                for c in chars
            ],
            "count": len(chars),
        }
    finally:
        db.close()


def _read_lore(pid: str) -> dict:
    db = SessionLocal()
    try:
        items = (
            db.query(Lore)
            .filter(Lore.project_id == pid)
            .order_by(Lore.lore_type.asc(), Lore.name.asc())
            .all()
        )
        return {
            "lore": [
                {
                    "id": item.id,
                    "name": item.name,
                    "lore_type": item.lore_type,
                    "description": item.description,
                    "tags": item.tags or [],
                }
                for item in items
            ],
            "count": len(items),
        }
    finally:
        db.close()


def _read_project_summary(pid: str) -> dict:
    db = SessionLocal()
    try:
        proj = db.query(Project).filter(Project.id == pid).first()
        if not proj:
            return {"error": "Project not found"}
        chapters = (
            db.query(Chapter)
            .filter(Chapter.project_id == pid)
            .order_by(Chapter.scene_order.asc())
            .all()
        )
        return {
            "title": proj.title,
            "description": proj.description,
            "summary": proj.summary,
            "genre": proj.genre,
            "language": proj.language,
            "chapter_count": len(chapters),
            "chapters": [
                {"id": c.id, "title": c.title, "scene_order": c.scene_order, "status": c.status}
                for c in chapters[:20]
            ],
        }
    finally:
        db.close()


# ── Plan / adapt parsers ──────────────────────────────────────────────────────

def _parse_plan(raw: str) -> list[dict]:
    """Parse a JSON plan from LLM output, returning a list of step dicts."""
    cleaned = re.sub(r"```[a-z]*\n?", "", raw).strip()
    m = re.search(r"\[.*\]", cleaned, re.DOTALL)
    if m:
        cleaned = m.group(0)
    try:
        plan = json.loads(cleaned)
        if isinstance(plan, list):
            return plan
    except Exception:
        pass
    return [
        {
            "step": 1,
            "tool": "generate_text",
            "description": "Generate content",
            "params": {"prompt": "Help with the writing task.", "purpose": "general"},
        }
    ]


def _renumber(steps: list[dict], start: int = 1) -> list[dict]:
    """Re-number steps starting from `start`."""
    return [{**s, "step": start + i} for i, s in enumerate(steps)]


# ── Streaming helper ──────────────────────────────────────────────────────────

async def _stream_generation(
    client,
    messages: list[dict],
    send,
    check_cancel,
) -> str:
    """Stream LLM output token-by-token via chat_stream; return full text."""
    full = ""
    async for chunk in client.chat_stream(messages):
        full += chunk
        await send({"type": "text_delta", "delta": chunk})
        if await check_cancel():
            break
    return full


# ── Agent memory helpers ──────────────────────────────────────────────────────

def _tool_result_summary(tool: str, result: dict) -> str:
    """Compact human-readable summary of a tool result for injection into agent memory."""
    if result.get("error"):
        return f"[{tool}] ERROR: {result['error']}"
    if tool == "read_chapter":
        preview = (result.get("content") or "")[:600]
        return (
            f"[read_chapter] Title: {result.get('title')}, "
            f"ID: {result.get('id')}, Words: {result.get('word_count')}\n"
            f"Content: {preview}"
        )
    if tool == "read_characters":
        entries = ", ".join(
            f"{c.get('name','?')} (id={c.get('id','')})"
            for c in (result.get("characters") or [])
        )
        return f"[read_characters] Found {result.get('count', 0)}: {entries}"
    if tool == "read_lore":
        entries = ", ".join(
            f"{item.get('name','?')} ({item.get('lore_type','?')}, id={item.get('id','')})"
            for item in (result.get("lore") or [])[:20]
        )
        return f"[read_lore] Found {result.get('count', 0)}: {entries}"
    if tool == "read_project_summary":
        chaps = ", ".join(
            f'"{c.get("title","?")} (id={c.get("id","")})' 
            for c in (result.get("chapters") or [])[:10]
        )
        return (
            f"[read_project_summary] Title: {result.get('title')}, "
            f"Chapters ({result.get('chapter_count',0)}): {chaps}"
        )
    if tool == "analyze_consistency":
        preview = (result.get("report") or "")[:200]
        return (
            f"[analyze_consistency] Analyzed {result.get('chapter_count',0)} chapters. "
            f"Report preview: {preview}"
        )
    if tool == "search_content":
        hits = ", ".join(
            f"{r.get('title','?')} ({r.get('kind','?')}, id={r.get('id','')})"
            for r in (result.get("results") or [])[:8]
        )
        return f"[search_content] query='{result.get('query')}' found {result.get('count',0)}: {hits}"
    if tool == "update_lore":
        return f"[update_lore] Updated '{result.get('name')}' id={result.get('id')}"
    if tool == "read_timeline":
        entries = ", ".join(
            f"{e.get('title','?')} (id={e.get('id','')})"
            for e in (result.get("events") or [])[:10]
        )
        return f"[read_timeline] Found {result.get('count', 0)}: {entries}"
    if tool == "ask_user":
        return f"[ask_user] Asked: {result.get('question', '')} → Answer: {result.get('answer', '(no answer)')}"
    if tool == "create_character":
        return f"[create_character] Created '{result.get('name')}' id={result.get('id')}"
    if tool == "update_character":
        return f"[update_character] Updated '{result.get('name')}' id={result.get('id')}"
    if tool == "create_lore":
        return f"[create_lore] Created '{result.get('name')}' ({result.get('lore_type')}) id={result.get('id')}"
    if tool == "create_chapter":
        return f"[create_chapter] Created '{result.get('title')}' id={result.get('id')} words={result.get('word_count')}"
    if tool == "update_chapter":
        return f"[update_chapter] Updated '{result.get('title')}' id={result.get('id')} words={result.get('word_count')}"
    if tool == "update_summary":
        return "[update_summary] Project summary updated."
    if tool == "create_timeline_event":
        return f"[create_timeline_event] Created event '{result.get('title')}' id={result.get('id')}"
    return f"[{tool}] Done: {json.dumps(result, ensure_ascii=False)[:200]}"


def _extract_chapter_content_from_memory(memory: list[str], chapter_id: str) -> str | None:
    """Extract the full chapter content from memory if a read_chapter result is recorded."""
    if not chapter_id:
        return None
    for entry in memory:
        if "[read_chapter]" not in entry or chapter_id not in entry:
            continue
        # Memory entry format: "[read_chapter] Title: ..., ID: <id>, Words: ...\nContent: <content>"
        content_marker = "\nContent: "
        idx = entry.find(content_marker)
        if idx != -1:
            return entry[idx + len(content_marker):]
    return None


# ── WebSocket handler ─────────────────────────────────────────────────────────

@router.websocket("/ws/agent")
async def agent_ws(ws: WebSocket) -> None:
    await ws.accept()
    cancel = asyncio.Event()

    async def send(msg: dict) -> None:
        try:
            await ws.send_json(msg)
        except Exception:
            pass

    async def check_cancel() -> bool:
        try:
            d = await asyncio.wait_for(ws.receive_json(), timeout=0.05)
            if isinstance(d, dict) and d.get("type") == "cancel":
                cancel.set()
        except Exception:
            pass
        return cancel.is_set()

    try:
        data = await ws.receive_json()
        pid: str = data.get("project_id", "")
        task: str = data.get("task", "")
        lang: str = data.get("language", "vi")
        active_chapter_id: str = data.get("chapter_id", "")

        if not task.strip():
            await send({"type": "error", "message": "Task cannot be empty"})
            return

        settings = _get_settings()
        client = build_client(settings)

        ctx = ProjectContext(pid or None)
        if pid:
            await ctx.load()

        # Build a short project summary for planning
        ctx_summary = ""
        if ctx.project:
            ctx_summary += f"Project: {ctx.project.title}\n"
        if active_chapter_id:
            ctx_summary += f"Currently open chapter id: {active_chapter_id}\n"
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

        await send({"type": "status", "message": "Planning..."})

        # ── Planning step ──────────────────────────────────────────────────
        plan_messages: list[dict] = [
            {"role": "system", "content": PLAN_SYSTEM},
            {"role": "user", "content": f"Language: {lang}\nTask: {task}\n{ctx_summary}"},
        ]
        try:
            raw = await client.chat_messages(plan_messages)
            steps = _parse_plan(raw)
        except Exception as e:
            await send({"type": "error", "message": f"Planning failed: {e}"})
            return

        steps = _renumber(steps)
        await send({"type": "plan", "steps": steps, "total": len(steps)})

        if await check_cancel():
            await send({"type": "cancelled", "message": "Cancelled"})
            return

        # ── Execution system prompt ────────────────────────────────────────
        exec_system = _system_prompt(ctx)
        exec_system += f"\nLanguage: {lang}\n"

        # Agent memory: accumulates tool result summaries to feed into adapt calls
        memory: list[str] = []
        completed: list[dict] = []

        # ── Step execution loop ────────────────────────────────────────────
        step_index = 0
        while step_index < len(steps):
            step = steps[step_index]
            step_index += 1

            if await check_cancel():
                await send({"type": "cancelled", "message": f"Cancelled at step {step['step']}"})
                return

            tool = step.get("tool", "generate_text")
            params = step.get("params", {})
            desc = step.get("description", tool)

            await send({
                "type": "step_start",
                "step": step["step"],
                "total": len(steps),
                "tool": tool,
                "description": desc,
            })

            result: dict = {}
            is_read_tool = tool.startswith("read_")

            try:
                # ── Read tools (no LLM; trigger adaptive re-planning) ─────
                if tool == "analyze_consistency":
                    raw_data = _analyze_consistency(pid)
                    is_read_tool = True
                    # LLM analyzes the data and produces a consistency report
                    analysis_msgs: list[dict] = [
                        {"role": "system", "content": exec_system},
                        *_memory_msgs(memory),
                        {
                            "role": "user",
                            "content": (
                                f"Analyze the following project data for consistency issues "
                                f"(timeline contradictions, character behavior, plot holes).\n\n"
                                f"Chapters ({raw_data['chapter_count']}):\n"
                                + "\n".join(
                                    f"- Ch{c['scene_order']+1} '{c['title']}': {c['preview'][:300]}"
                                    for c in raw_data["chapters"]
                                )
                                + f"\n\nCharacters:\n"
                                + "\n".join(
                                    f"- {c['name']} ({c['role']}): {c['personality'] or 'no info'}"
                                    for c in raw_data["characters"]
                                )
                                + "\n\nList all inconsistencies found. If none, say 'No issues found.'"
                            ),
                        },
                    ]
                    g = await _stream_generation(client, analysis_msgs, send, check_cancel)
                    result = {"report": g, "chapter_count": raw_data["chapter_count"]}

                elif tool == "search_content":
                    result = _search_content(pid, params)
                    is_read_tool = True  # treat as read so adaptive re-plan triggers

                elif tool == "read_chapter":
                    result = _read_chapter(pid, params)

                elif tool == "read_characters":
                    result = _read_characters(pid)

                elif tool == "read_lore":
                    result = _read_lore(pid)

                elif tool == "read_timeline":
                    result = _read_timeline(pid)

                elif tool == "read_project_summary":
                    result = _read_project_summary(pid)

                # ── Write tools ───────────────────────────────────────────
                elif tool == "create_character" and pid:
                    if not params.get("personality"):
                        profile_msgs: list[dict] = [
                            {"role": "system", "content": exec_system},
                            *_memory_msgs(memory),
                            {
                                "role": "user",
                                "content": (
                                    f"Return a JSON object for character '{params.get('name', '')}' "
                                    f"role='{params.get('role', '')}'. "
                                    "Keys: personality, goals, secrets, appearance, age. JSON only."
                                ),
                            },
                        ]
                        g = await client.chat_messages(profile_msgs)
                        try:
                            cm = re.search(r"\{.*\}", re.sub(r"```[a-z]*\n?", "", g), re.DOTALL)
                            if cm:
                                extra = json.loads(cm.group(0))
                                params = {**extra, **params}
                        except Exception:
                            pass
                    result = _create_char(pid, params)

                elif tool == "update_character" and pid:
                    if not params.get("character_id"):
                        # Try to resolve character_id from memory using the name hint
                        name_hint = (params.get("name") or "").strip()
                        if name_hint:
                            for entry in memory:
                                if "[read_characters]" not in entry:
                                    continue
                                m = re.search(
                                    rf"\b{re.escape(name_hint)}\b\s*\(id=([^)]+)\)",
                                    entry,
                                    re.IGNORECASE,
                                )
                                if m:
                                    params = {**params, "character_id": m.group(1)}
                                    break
                    result = _update_character(pid, params)

                elif tool == "create_lore" and pid:
                    if not params.get("description"):
                        desc_msgs: list[dict] = [
                            {"role": "system", "content": exec_system},
                            *_memory_msgs(memory),
                            {
                                "role": "user",
                                "content": (
                                    f"Describe '{params.get('name', '')}' "
                                    f"({params.get('lore_type', 'term')}) in 2-3 vivid sentences."
                                ),
                            },
                        ]
                        g = await client.chat_messages(desc_msgs)
                        params = {**params, "description": g.strip()}
                    result = _create_lore(pid, params)

                elif tool == "update_lore" and pid:
                    if not params.get("lore_id"):
                        # Try to resolve lore_id from memory using the name hint
                        name_hint = (params.get("name") or "").strip()
                        if name_hint:
                            for entry in memory:
                                if "[read_lore]" not in entry:
                                    continue
                                m = re.search(
                                    rf"\b{re.escape(name_hint)}\b[^(]*\([^,)]+,\s*id=([^)]+)\)",
                                    entry,
                                    re.IGNORECASE,
                                )
                                if m:
                                    params = {**params, "lore_id": m.group(1)}
                                    break
                    result = _update_lore(pid, params)

                elif tool == "ask_user":
                    # Pause execution, send question to client, wait for answer
                    question = params.get("question", "")
                    await send({"type": "ask_user", "question": question, "step": step["step"]})
                    # Wait up to 120s for user reply
                    try:
                        answer_data = await asyncio.wait_for(ws.receive_json(), timeout=120.0)
                        if isinstance(answer_data, dict) and answer_data.get("type") == "cancel":
                            cancel.set()
                            answer = ""
                        else:
                            answer = answer_data.get("answer", "") if isinstance(answer_data, dict) else ""
                    except asyncio.TimeoutError:
                        await send({"type": "status", "message": "No answer received, continuing..."})
                        answer = ""
                    result = {"question": question, "answer": answer}
                    # Inject answer into task context for subsequent steps
                    if answer:
                        exec_system += f"\nUser clarification: {answer}\n"
                    if not params.get("content") or len(params.get("content", "")) < 100:
                        char_ctx = ctx.character_context()
                        chapter_msgs: list[dict] = [
                            {
                                "role": "system",
                                "content": exec_system
                                + (f"\nCharacters:\n{char_ctx[:2000]}" if char_ctx else ""),
                            },
                            *_memory_msgs(memory),
                            {
                                "role": "user",
                                "content": (
                                    f"Write chapter '{params.get('title', 'Chapter')}' "
                                    f"(scene {params.get('scene_order', 0) + 1}). "
                                    "Engaging prose, 400-600 words."
                                ),
                            },
                        ]
                        g = await _stream_generation(client, chapter_msgs, send, check_cancel)
                        params = {**params, "content": g.strip()}
                    result = _create_chapter(pid, params)

                elif tool == "update_chapter" and pid:
                    # Try to get existing content from memory first
                    chapter_id = params.get("chapter_id", "")
                    existing_content = _extract_chapter_content_from_memory(memory, chapter_id)

                    if not params.get("content"):
                        if existing_content:
                            existing_data = {
                                "title": next(
                                    (
                                        re.search(r"Title: (.+?),", e).group(1)
                                        for e in memory
                                        if "[read_chapter]" in e and chapter_id in e
                                        and re.search(r"Title: (.+?),", e)
                                    ),
                                    "Chapter",
                                ),
                                "content": existing_content,
                            }
                        else:
                            # Fetch from DB if not in memory
                            existing_data = _read_chapter(pid, params)

                        if isinstance(existing_data, dict) and "error" not in existing_data:
                            rewrite_msgs: list[dict] = [
                                {"role": "system", "content": exec_system},
                                *_memory_msgs(memory),
                                {
                                    "role": "user",
                                    "content": (
                                        f"Rewrite/improve this chapter titled '{existing_data.get('title')}'.\n"
                                        f"Original content:\n{existing_data.get('content', '')[:3000]}\n\n"
                                        f"Task: {desc}"
                                    ),
                                },
                            ]
                            g = await _stream_generation(client, rewrite_msgs, send, check_cancel)
                            params = {**params, "content": g.strip()}
                    result = _update_chapter(pid, params)

                elif tool == "update_summary" and pid:
                    if not params.get("summary"):
                        summary_msgs: list[dict] = [
                            {"role": "system", "content": exec_system},
                            *_memory_msgs(memory),
                            {
                                "role": "user",
                                "content": f"Write a 2-3 paragraph story summary for: {task}",
                            },
                        ]
                        g = await client.chat_messages(summary_msgs)
                        params = {**params, "summary": g.strip()}
                    result = _update_summary(pid, params)

                elif tool == "create_timeline_event" and pid:
                    if not params.get("description"):
                        event_msgs: list[dict] = [
                            {"role": "system", "content": exec_system},
                            *_memory_msgs(memory),
                            {
                                "role": "user",
                                "content": (
                                    f"Describe the timeline event '{params.get('title', 'Event')}' "
                                    "in 1-2 sentences, including significance to the story."
                                ),
                            },
                        ]
                        g = await client.chat_messages(event_msgs)
                        params = {**params, "description": g.strip()}
                    result = _create_timeline_event(pid, params)

                else:  # generate_text or unknown
                    gen_msgs: list[dict] = [
                        {"role": "system", "content": exec_system},
                        *_memory_msgs(memory),
                        {"role": "user", "content": params.get("prompt", desc)},
                    ]
                    g = await _stream_generation(client, gen_msgs, send, check_cancel)
                    result = {"text": g, "purpose": params.get("purpose", "")}

            except Exception as e:
                logger.error("Tool %s step %d: %s", tool, step["step"], e, exc_info=True)
                result = {"error": str(e)}
                # ── Retry once on non-read tools if error is transient ─────
                if not is_read_tool and tool != "ask_user":
                    await send({"type": "status", "message": f"Retrying step {step['step']}..."})
                    await asyncio.sleep(1.0)
                    try:
                        if tool == "create_character" and pid:
                            result = _create_char(pid, params)
                        elif tool == "update_character" and pid:
                            result = _update_character(pid, params)
                        elif tool == "create_lore" and pid:
                            result = _create_lore(pid, params)
                        elif tool == "update_lore" and pid:
                            result = _update_lore(pid, params)
                        elif tool == "create_chapter" and pid and params.get("content"):
                            # Only retry if content was already generated — avoids empty chapter
                            result = _create_chapter(pid, params)
                        elif tool == "update_chapter" and pid and params.get("content"):
                            # Only retry if content was already generated
                            result = _update_chapter(pid, params)
                        elif tool == "update_summary" and pid and params.get("summary"):
                            result = _update_summary(pid, params)
                        elif tool == "create_timeline_event" and pid:
                            result = _create_timeline_event(pid, params)
                        # generate_text: don't retry (expensive LLM call)
                    except Exception as retry_e:
                        logger.warning("Retry failed for %s step %d: %s", tool, step["step"], retry_e)
                        result = {"error": str(retry_e)}

            # ── Update memory with this step's result ──────────────────────
            memory.append(_tool_result_summary(tool, result))

            completed.append({**step, "result": result})
            await send({
                "type": "step_done",
                "step": step["step"],
                "tool": tool,
                "description": desc,
                "result": result,
            })
            await asyncio.sleep(0.05)

            # ── Adaptive re-planning after read tools ──────────────────────
            # When agent reads data, let it decide what to do next.
            if is_read_tool and "error" not in result and step_index >= len(steps):
                remaining = await _adapt_plan(
                    client=client,
                    task=task,
                    lang=lang,
                    memory=memory,
                    completed_count=len(completed),
                    send=send,
                )
                if remaining:
                    steps = steps + _renumber(remaining, start=len(steps) + 1)
                    await send({"type": "plan_update", "steps": steps, "total": len(steps)})

        # ── Completion summary ─────────────────────────────────────────────
        chars_created = [s for s in completed if s["tool"] == "create_character" and "error" not in s.get("result", {})]
        chars_updated = [s for s in completed if s["tool"] == "update_character" and s.get("result", {}).get("updated")]
        lores_created = [s for s in completed if s["tool"] == "create_lore" and "error" not in s.get("result", {})]
        lores_updated = [s for s in completed if s["tool"] == "update_lore" and s.get("result", {}).get("updated")]
        chaps = [s for s in completed if s["tool"] == "create_chapter" and "error" not in s.get("result", {})]
        upds = [s for s in completed if s["tool"] == "update_chapter" and s.get("result", {}).get("updated")]
        timeline_events = [s for s in completed if s["tool"] == "create_timeline_event" and "error" not in s.get("result", {})]
        reads = [s for s in completed if s["tool"].startswith("read_")]

        parts: list[str] = []
        if chars_created:
            parts.append(f"Created {len(chars_created)} character(s): {', '.join(s['result'].get('name', '?') for s in chars_created)}")
        if chars_updated:
            parts.append(f"Updated {len(chars_updated)} character(s): {', '.join(s['result'].get('name', '?') for s in chars_updated)}")
        if lores_created:
            parts.append(f"Created {len(lores_created)} lore item(s): {', '.join(s['result'].get('name', '?') for s in lores_created)}")
        if lores_updated:
            parts.append(f"Updated {len(lores_updated)} lore item(s): {', '.join(s['result'].get('name', '?') for s in lores_updated)}")
        if chaps:
            parts.append(f"Created {len(chaps)} chapter(s): {', '.join(s['result'].get('title', '?') for s in chaps)}")
        if upds:
            parts.append(f"Updated {len(upds)} chapter(s): {', '.join(s['result'].get('title', '?') for s in upds)}")
        if timeline_events:
            parts.append(f"Created {len(timeline_events)} timeline event(s): {', '.join(s['result'].get('title', '?') for s in timeline_events)}")
        if reads and not (chars_created or chars_updated or lores_created or lores_updated or chaps or upds or timeline_events):
            parts.append(f"Read {len(reads)} item(s) from project.")

        await send({
            "type": "done",
            "summary": ". ".join(parts) + "." if parts else "Agent completed.",
            "steps_completed": len(completed),
        })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error("Agent: %s", e, exc_info=True)
        try:
            await ws.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        try:
            await ws.close()
        except Exception:
            pass


# ── Adaptive re-planning ──────────────────────────────────────────────────────

async def _adapt_plan(
    client,
    task: str,
    lang: str,
    memory: list[str],
    completed_count: int,
    send,
) -> list[dict]:
    """Ask the agent if more steps are needed based on what was read. Returns new steps or []."""
    memory_text = "\n".join(memory)
    adapt_messages: list[dict] = [
        {"role": "system", "content": ADAPT_SYSTEM},
        {
            "role": "user",
            "content": (
                f"Language: {lang}\n"
                f"Original task: {task}\n\n"
                f"Steps completed so far ({completed_count}):\n{memory_text}\n\n"
                "What additional steps (if any) are needed to complete the task? "
                "Return [] if nothing more is needed."
            ),
        },
    ]
    try:
        await send({"type": "status", "message": "Adapting plan..."})
        raw = await client.chat_messages(adapt_messages)
        new_steps = _parse_plan(raw)
        # If the only step is generate_text with the default prompt, treat as empty
        if (
            len(new_steps) == 1
            and new_steps[0].get("tool") == "generate_text"
            and "Help with the writing task" in new_steps[0].get("params", {}).get("prompt", "")
        ):
            return []
        return new_steps
    except Exception as e:
        logger.warning("Adapt plan failed: %s", e)
        return []


# ── Memory helpers ────────────────────────────────────────────────────────────

def _memory_msgs(memory: list[str]) -> list[dict]:
    """Inject accumulated tool results as a single assistant context message."""
    if not memory:
        return []
    content = "Previous steps completed:\n" + "\n".join(memory)
    return [{"role": "assistant", "content": content}]
