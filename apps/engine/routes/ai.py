from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
router = APIRouter()

class AIIn(BaseModel):
    project_id: str | None = None
    chapter_id: str | None = None
    action: str
    text: str | None = None
    instruction: str | None = None

@router.post("/ai/run")
async def run_ai(payload: AIIn):
    return {"result": "[DUMMY] AI backend not configured yet.", "action": payload.action}

@router.websocket("/ws/ai")
async def ai_ws(ws: WebSocket):
    await ws.accept()
    await ws.send_json({"delta": "[DUMMY] AI backend not configured yet."})
    await ws.close()
