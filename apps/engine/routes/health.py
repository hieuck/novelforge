from __future__ import annotations

from _version import VERSION
from db.base import engine
from db.paths import get_data_dir
from fastapi import APIRouter, Request
from pydantic import BaseModel
from sqlalchemy import text

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    version: str = VERSION
    db: str = "ok"


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return HealthResponse(status="ok", version=VERSION, db="ok")
    except Exception as e:
        return HealthResponse(status="degraded", version=VERSION, db=str(e))


@router.get("/health/db")
async def health_db() -> dict:
    db_path = get_data_dir() / "novelforge.db"
    size = db_path.stat().st_size if db_path.exists() else 0
    try:
        with engine.connect() as conn:
            tables = conn.execute(text("SELECT count(*) FROM sqlite_master WHERE type='table'")).scalar() or 0
            return {
                "status": "ok",
                "size_bytes": size,
                "tables": tables,
                "db_path": str(db_path),
            }
    except Exception as e:
        return {
            "status": "degraded",
            "size_bytes": size,
            "tables": 0,
            "error": str(e),
        }


@router.api_route("/tools/echo", methods=["GET", "POST"])
async def echo(request: Request) -> dict:
    """Debug endpoint that echoes request info."""
    body = None
    if request.method == "POST":
        try:
            body = await request.json()
        except Exception:
            body = {"error": "invalid json"}
    return {
        "ok": True,
        "method": request.method,
        "path": request.url.path,
        "body": body,
    }
