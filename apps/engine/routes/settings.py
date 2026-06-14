from __future__ import annotations

import logging
import platform
import sys
from importlib.metadata import version as pkg_version

from fastapi import APIRouter, HTTPException
from httpx import AsyncClient, HTTPError, Timeout
from pydantic import BaseModel

from db.session import SessionLocal
from models.extra import AppSettings, Job, Lore, TimelineItem, Character
from models.chapter import Chapter
from models.project import Project
from models.summary import Summary
from services.search import init_fts

logger = logging.getLogger("novelforge.settings")
router = APIRouter()


class SettingsIn(BaseModel):
    provider: str = "ollama"
    base_url: str = "http://localhost:11434"
    api_key: str | None = None
    model: str = "llama3.1:8b"
    temperature: float = 0.7
    max_tokens: int = 2048


def _row_to_dict(row: AppSettings) -> dict:
    return {
        "provider": row.provider,
        "base_url": row.base_url,
        "api_key": row.api_key,
        "model": row.model,
        "temperature": row.temperature,
        "max_tokens": row.max_tokens,
    }


@router.get("/settings/current")
async def current_settings() -> dict:
    db = SessionLocal()
    try:
        row = db.query(AppSettings).filter(AppSettings.active == True).first()
        if not row:
            return {
                "provider": "ollama",
                "base_url": "http://localhost:11434",
                "api_key": None,
                "model": "llama3.1:8b",
                "temperature": 0.7,
                "max_tokens": 2048,
            }
        return _row_to_dict(row)
    finally:
        db.close()


@router.post("/settings/current")
async def update_settings(payload: SettingsIn) -> dict:
    db = SessionLocal()
    try:
        row = db.query(AppSettings).filter(AppSettings.active == True).first()
        if not row:
            row = AppSettings(id="app-settings", active=True, **payload.model_dump())
            db.add(row)
        else:
            row.provider = payload.provider
            row.base_url = payload.base_url
            row.api_key = payload.api_key
            row.model = payload.model
            row.temperature = payload.temperature
            row.max_tokens = payload.max_tokens
        db.commit()
        db.refresh(row)
        return _row_to_dict(row)
    finally:
        db.close()


@router.post("/settings/test")
async def test_connection(payload: SettingsIn) -> dict:
    """Test connectivity to the configured AI provider."""
    provider = (payload.provider or "ollama").lower()
    base_url = payload.base_url.rstrip("/")
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if payload.api_key:
        headers["Authorization"] = f"Bearer {payload.api_key}"

    timeout = Timeout(connect=5.0, read=15.0, write=5.0, pool=5.0)
    try:
        async with AsyncClient() as client:
            if provider == "ollama":
                resp = await client.get(f"{base_url}/api/tags", timeout=timeout)
            else:
                # OpenAI-compatible: list models endpoint
                resp = await client.get(
                    f"{base_url}/models",
                    headers=headers,
                    timeout=timeout,
                )
            if resp.status_code == 200:
                return {"ok": True, "response": f"HTTP {resp.status_code}"}
            return {"ok": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
    except HTTPError as exc:
        return {"ok": False, "error": str(exc)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@router.get("/settings/models")
async def list_models(
    provider: str = "ollama",
    base_url: str = "http://localhost:11434",
    api_key: str | None = None,
) -> dict:
    """Fetch available models from the configured provider."""
    _base = base_url.rstrip("/")
    headers: dict[str, str] = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    timeout = Timeout(connect=5.0, read=15.0, write=5.0, pool=5.0)
    prov = (provider or "ollama").lower()
    try:
        async with AsyncClient() as client:
            if prov == "ollama":
                resp = await client.get(f"{_base}/api/tags", timeout=timeout)
                resp.raise_for_status()
                data = resp.json()
                models = [m["name"] for m in (data.get("models") or []) if m.get("name")]
            else:
                resp = await client.get(
                    f"{_base}/models",
                    headers=headers,
                    timeout=timeout,
                )
                resp.raise_for_status()
                data = resp.json()
                models = [
                    m.get("id") or m.get("name")
                    for m in (data.get("data") or [])
                    if m.get("id") or m.get("name")
                ]
        return {"models": sorted(models)}
    except HTTPError as exc:
        return {"models": [], "error": str(exc)}
    except Exception as exc:
        return {"models": [], "error": str(exc)}


@router.post("/settings/models/pull")
async def pull_model(name: str = "") -> dict:
    """Pull an Ollama model by name."""
    import subprocess
    if not name.strip():
        raise HTTPException(status_code=400, detail="Model name required")
    try:
        result = subprocess.run(
            ["ollama", "pull", name.strip()],
            capture_output=True, text=True, timeout=300,
        )
        if result.returncode != 0:
            return {"success": False, "error": result.stderr.strip() or result.stdout.strip()}
        return {"success": True, "message": f"Pulled {name.strip()}"}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Pull timed out (5 min)"}
    except FileNotFoundError:
        return {"success": False, "error": "ollama command not found in PATH"}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


@router.delete("/settings/models/{name}")
async def delete_model(name: str) -> dict:
    """Delete an Ollama model by name."""
    import subprocess
    if not name.strip():
        raise HTTPException(status_code=400, detail="Model name required")
    try:
        result = subprocess.run(
            ["ollama", "rm", name.strip()],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            return {"success": False, "error": result.stderr.strip() or result.stdout.strip()}
        return {"success": True, "message": f"Deleted {name.strip()}"}
    except FileNotFoundError:
        return {"success": False, "error": "ollama command not found in PATH"}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


@router.get("/settings/about")
async def about() -> dict:
    """App metadata for the About tab."""
    try:
        fapi_version = pkg_version("fastapi")
    except Exception:
        fapi_version = "?"

    from _version import VERSION

    return {
        "app": "NovelForge",
        "version": VERSION,
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "platform": platform.system(),
        "fastapi": fapi_version,
        "description": "Offline-first AI writing studio",
        "repo": "https://github.com/hieuck/novelforge",
    }


@router.delete("/settings/data/all", status_code=204)
async def delete_all_data() -> None:
    """Danger zone: wipe all user data from the database and search index."""
    db = SessionLocal()
    try:
        db.query(Summary).delete()
        db.query(Job).delete()
        db.query(TimelineItem).delete()
        db.query(Lore).delete()
        db.query(Character).delete()
        db.query(Chapter).delete()
        db.query(Project).delete()
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        db.close()

    # Rebuild empty FTS tables
    try:
        import sqlite3
        from pathlib import Path
        db_path = Path(__file__).resolve().parent.parent / "novelforge.db"
        con = sqlite3.connect(str(db_path))
        con.execute("DELETE FROM fts_chapters")
        con.execute("DELETE FROM fts_lore")
        con.execute("DELETE FROM fts_characters")
        con.commit()
        con.close()
    except Exception:
        pass  # FTS clear failure is non-critical
