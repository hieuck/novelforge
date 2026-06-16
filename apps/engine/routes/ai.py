from __future__ import annotations

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from services.ai_run import run_ai
from services.ai_service import AIEngine
from services.context.builder import ProjectContext

logger = logging.getLogger("novelforge.ai.route")

router = APIRouter()


def _system_prompt(ctx: ProjectContext) -> str:
    """Build a system prompt from a loaded ProjectContext (used by agent route)."""
    from services.prompts.loader import load_prompt

    base = load_prompt("system_base.txt")
    writing = load_prompt("writing_assistant.txt")
    parts = [base, writing]
    char = ctx.character_context()
    lore = ctx.lore_context()
    timeline = ctx.timeline_context()
    style = ctx.style_context()
    if char.strip():
        parts.append(f"Character Bible:\n{char}")
    if lore.strip():
        parts.append(f"World Lore:\n{lore}")
    if timeline.strip():
        parts.append(f"Timeline:\n{timeline}")
    if style.strip():
        parts.append(f"Style guide:\n{style}")
    return "\n\n".join(parts)


class AIIn(BaseModel):
    project_id: str | None = None
    chapter_id: str | None = None
    action: str
    text: str | None = None
    instruction: str | None = None
    history: list[dict] | None = None


@router.post("/ai/run")
async def run_ai_endpoint(payload: AIIn) -> dict:
    return await run_ai(
        project_id=payload.project_id,
        action=payload.action,
        text=payload.text,
        instruction=payload.instruction,
        chapter_id=payload.chapter_id,
        history=payload.history,
    )


@router.websocket("/ws/ai")
async def ai_ws(ws: WebSocket) -> None:
    """Stream AI responses token by token over WebSocket.

    Receives:
        {
            project_id: str | null,
            chapter_id: str | null,
            action: str,
            text: str,
            instruction: str,
            history: [{role, content}, ...]
        }
    Sends:
        {"delta": "..."}          — incremental text chunk
        {"done": true, "full": "..."}  — completion signal with full text
        {"error": "..."}          — on failure
    """
    await ws.accept()
    try:
        data = await ws.receive_json()
    except Exception:
        await ws.close(code=1003)
        return

    project_id: str | None = data.get("project_id") or None
    chapter_id: str | None = data.get("chapter_id") or None
    action: str = data.get("action", "continue")
    text: str = data.get("text") or ""
    instruction: str = data.get("instruction") or ""
    history: list[dict] = data.get("history") or []

    engine = AIEngine(project_id=project_id)
    try:
        await engine.prepare()
    except Exception as exc:
        logger.error("Engine prepare failed: %s", exc)
        await ws.send_json({"error": f"Context load failed: {exc}"})
        await ws.close()
        return

    full_text = ""
    try:
        async for chunk in engine.stream(
            action=action,
            text=text,
            instruction=instruction,
            chapter_id=chapter_id,
            history=history,
        ):
            full_text += chunk
            try:
                await ws.send_json({"delta": chunk})
            except Exception:
                # Client disconnected mid-stream — stop gracefully
                return
        await ws.send_json({"done": True, "full": full_text})
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.error("AI stream error: %s", exc)
        msg = str(exc)
        err_lower = msg.lower()
        if "connect" in err_lower and (
            "refused" in err_lower or "timed out" in err_lower or "econnrefused" in err_lower
        ):
            msg = (
                f"Không thể kết nối AI provider ({msg}). "
                f"Vào Settings \u2192 AI Provider để kiểm tra cấu hình (Ollama, OpenAI, v.v.)."
            )
        elif "404" in msg:
            msg = "AI provider trả về 404 — endpoint API không đúng. Kiểm tra Base URL trong Settings → AI Provider."
        try:
            await ws.send_json({"error": msg})
        except Exception:
            pass
    finally:
        try:
            await ws.close()
        except Exception:
            pass
