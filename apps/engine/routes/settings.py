from fastapi import APIRouter
from pydantic import BaseModel
from db.session import SessionLocal
from models.settings import AppSettings

router = APIRouter()

class SettingsIn(BaseModel):
    provider: str = "ollama"
    base_url: str = "http://localhost:11434"
    api_key: str | None = None
    model: str = "llama3.1:8b"
    temperature: float = 0.7
    max_tokens: int = 2048

@router.get("/settings/current")
async def current_settings():
    db = SessionLocal()
    try:
        row = db.query(AppSettings).filter(AppSettings.active == True).first()
        if not row:
            return {"provider": "ollama", "base_url": "http://localhost:11434", "model": "llama3.1:8b", "temperature": 0.7, "max_tokens": 2048}
        return {"provider": row.provider, "base_url": row.base_url, "api_key": row.api_key, "model": row.model, "temperature": row.temperature, "max_tokens": row.max_tokens}
    finally:
        db.close()

@router.post("/settings/current")
async def update_settings(payload: SettingsIn):
    db = SessionLocal()
    try:
        row = db.query(AppSettings).filter(AppSettings.active == True).first()
        if not row:
            row = AppSettings(active=True, **payload.model_dump())
            db.add(row)
        else:
            row.provider = payload.provider
            row.base_url = payload.base_url
            row.api_key = payload.api_key
            row.model = payload.model
            row.temperature = payload.temperature
            row.max_tokens = payload.max_tokens
        db.commit(); db.refresh(row)
        return payload.model_dump()
    finally:
        db.close()

@router.post("/settings/test")
async def test_connection(payload: SettingsIn):
    return {"ok": True}
