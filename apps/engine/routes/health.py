from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text

from db.base import engine
from db.session import SessionLocal

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    db: str = "ok"


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return HealthResponse(status="ok", db="ok")
    except Exception as e:
        return HealthResponse(status="degraded", db=str(e))
