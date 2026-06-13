"""Bootstrap script to write all engine source files at once."""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent

def w(rel: str, content: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content.lstrip("\n"), encoding="utf-8")
    print(f"  wrote {rel}")


# ── models ────────────────────────────────────────────────────────────────────

w("models/extra.py", """
from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, Float, func, JSON
from db.base import Base


class Settings(Base):
    __tablename__ = "settings"
    id = Column(String, primary_key=True)
    active = Column(Boolean, nullable=False, default=True, index=True)
    provider = Column(String, nullable=False, default="ollama")
    base_url = Column(String, nullable=False, default="http://localhost:11434")
    api_key = Column(String, nullable=True)
    model = Column(String, nullable=False, default="llama3.1:8b")
    temperature = Column(Float, nullable=False, default=0.7)
    max_tokens = Column(Integer, nullable=False, default=2048)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


class Character(Base):
    __tablename__ = "characters"
    id = Column(String, primary_key=True)
    project_id = Column(String, nullable=True, index=True)
    name = Column(String, nullable=False)
    alias = Column(String, nullable=True)
    role = Column(String, nullable=True)
    age = Column(String, nullable=True)
    personality = Column(Text, nullable=True)
    appearance = Column(Text, nullable=True)
    goals = Column(Text, nullable=True)
    secrets = Column(Text, nullable=True)
    relationships = Column(JSON, nullable=True)
    first_appearance = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


class Lore(Base):
    __tablename__ = "lore"
    id = Column(String, primary_key=True)
    project_id = Column(String, nullable=True, index=True)
    lore_type = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)
    related_chapters = Column(JSON, nullable=True)
    related_characters = Column(JSON, nullable=True)
    lore_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


class TimelineItem(Base):
    __tablename__ = "timeline"
    id = Column(String, primary_key=True)
    project_id = Column(String, nullable=True, index=True)
    title = Column(String, nullable=False)
    event_date = Column(String, nullable=True)
    relative_order = Column(String, nullable=True)
    involved_characters = Column(JSON, nullable=True)
    related_chapters = Column(JSON, nullable=True)
    description = Column(Text, nullable=True)
    timeline_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


class Job(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True)
    project_id = Column(String, nullable=False, index=True)
    kind = Column(String, nullable=False)
    status = Column(String, nullable=False, default="queued")
    params = Column(JSON, nullable=True)
    result = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
""")

w("models/__init__.py", """
from db.base import Base
from models.project import Project
from models.chapter import Chapter
from models.extra import Character, Lore, TimelineItem, Settings, Job
from models.summary import Summary

__all__ = ["Base", "Project", "Chapter", "Character", "Lore", "TimelineItem", "Settings", "Job", "Summary"]
""")

w("models/summary.py", """
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, func
from db.base import Base


class Summary(Base):
    __tablename__ = "summaries"
    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, index=True)
    kind = Column(String, nullable=False)
    subject_id = Column(String, nullable=True)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
""")

w("models/base.py", """
from db.base import Base

__all__ = ["Base"]
""")

# ── routes ────────────────────────────────────────────────────────────────────

w("routes/__init__.py", """
# Routes package – routers are registered directly in app.py
""")

w("routes/health.py", """
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    version: str = "0.1.0"


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")
""")

w("routes/projects.py", """
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.session import SessionLocal
from models.project import Project

router = APIRouter()


class ProjectIn(BaseModel):
    title: str
    description: str | None = None
    genre: str | None = None
    language: str = "vi"
    style_guide: str | None = None
    summary: str | None = None


class ProjectUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    genre: str | None = None
    language: str | None = None
    style_guide: str | None = None
    summary: str | None = None


def _to_dict(p: Project) -> dict:
    return {
        "id": p.id,
        "title": p.title,
        "description": p.description,
        "genre": p.genre,
        "language": p.language,
        "style_guide": p.style_guide,
        "summary": p.summary,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    }


@router.get("/")
def list_projects() -> list:
    db: Session = SessionLocal()
    try:
        items = db.query(Project).order_by(Project.updated_at.desc()).all()
        return [_to_dict(p) for p in items]
    finally:
        db.close()


@router.post("/", status_code=201)
def create_project(payload: ProjectIn) -> dict:
    db: Session = SessionLocal()
    try:
        p = Project(id=str(uuid.uuid4()), **payload.model_dump())
        db.add(p)
        db.commit()
        db.refresh(p)
        return _to_dict(p)
    finally:
        db.close()


@router.get("/{project_id}")
def get_project(project_id: str) -> dict:
    db: Session = SessionLocal()
    try:
        p = db.query(Project).filter(Project.id == project_id).first()
        if not p:
            raise HTTPException(status_code=404, detail="Project not found")
        return _to_dict(p)
    finally:
        db.close()


@router.patch("/{project_id}")
def update_project(project_id: str, payload: ProjectUpdate) -> dict:
    db: Session = SessionLocal()
    try:
        p = db.query(Project).filter(Project.id == project_id).first()
        if not p:
            raise HTTPException(status_code=404, detail="Project not found")
        for k, v in payload.model_dump(exclude_unset=True).items():
            setattr(p, k, v)
        p.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(p)
        return _to_dict(p)
    finally:
        db.close()


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: str) -> None:
    db: Session = SessionLocal()
    try:
        p = db.query(Project).filter(Project.id == project_id).first()
        if not p:
            raise HTTPException(status_code=404, detail="Project not found")
        db.delete(p)
        db.commit()
    finally:
        db.close()
""")

w("routes/chapters.py", """
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.session import SessionLocal
from models.chapter import Chapter

router = APIRouter()


class ChapterIn(BaseModel):
    project_id: str
    title: str
    content: str = ""
    scene_order: int = 0
    status: str = "draft"
    summary: str | None = None
    notes: str | None = None


class ChapterUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    scene_order: int | None = None
    status: str | None = None
    summary: str | None = None
    notes: str | None = None


def _count_words(text: str) -> int:
    return len(text.split()) if text else 0


def _to_dict(c: Chapter) -> dict:
    return {
        "id": c.id,
        "project_id": c.project_id,
        "title": c.title,
        "content": c.content,
        "scene_order": c.scene_order,
        "status": c.status,
        "word_count": c.word_count,
        "summary": c.summary,
        "notes": c.notes,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }


@router.post("/", status_code=201)
def create_chapter(payload: ChapterIn) -> dict:
    db: Session = SessionLocal()
    try:
        c = Chapter(
            id=str(uuid.uuid4()),
            project_id=payload.project_id,
            title=payload.title,
            content=payload.content,
            scene_order=payload.scene_order,
            status=payload.status,
            word_count=_count_words(payload.content),
            summary=payload.summary,
            notes=payload.notes,
        )
        db.add(c)
        db.commit()
        db.refresh(c)
        return _to_dict(c)
    finally:
        db.close()


@router.get("/{chapter_id}")
def get_chapter(chapter_id: str) -> dict:
    db: Session = SessionLocal()
    try:
        c = db.query(Chapter).filter(Chapter.id == chapter_id).first()
        if not c:
            raise HTTPException(status_code=404, detail="Chapter not found")
        return _to_dict(c)
    finally:
        db.close()


@router.patch("/{chapter_id}")
def update_chapter(chapter_id: str, payload: ChapterUpdate) -> dict:
    db: Session = SessionLocal()
    try:
        c = db.query(Chapter).filter(Chapter.id == chapter_id).first()
        if not c:
            raise HTTPException(status_code=404, detail="Chapter not found")
        data = payload.model_dump(exclude_unset=True)
        for k, v in data.items():
            setattr(c, k, v)
        if "content" in data:
            c.word_count = _count_words(data["content"])
        c.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(c)
        return _to_dict(c)
    finally:
        db.close()


@router.delete("/{chapter_id}", status_code=204)
def delete_chapter(chapter_id: str) -> None:
    db: Session = SessionLocal()
    try:
        c = db.query(Chapter).filter(Chapter.id == chapter_id).first()
        if not c:
            raise HTTPException(status_code=404, detail="Chapter not found")
        db.delete(c)
        db.commit()
    finally:
        db.close()
""")

w("routes/characters.py", """
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.session import SessionLocal
from models.extra import Character

router = APIRouter()


class CharacterIn(BaseModel):
    project_id: str
    name: str
    alias: str | None = None
    role: str | None = None
    age: str | None = None
    personality: str | None = None
    appearance: str | None = None
    goals: str | None = None
    secrets: str | None = None
    relationships: dict | None = None
    first_appearance: str | None = None
    notes: str | None = None
    summary: str | None = None


class CharacterUpdate(BaseModel):
    name: str | None = None
    alias: str | None = None
    role: str | None = None
    age: str | None = None
    personality: str | None = None
    appearance: str | None = None
    goals: str | None = None
    secrets: str | None = None
    relationships: dict | None = None
    first_appearance: str | None = None
    notes: str | None = None
    summary: str | None = None


def _to_dict(c: Character) -> dict:
    return {
        "id": c.id, "project_id": c.project_id, "name": c.name, "alias": c.alias,
        "role": c.role, "age": c.age, "personality": c.personality,
        "appearance": c.appearance, "goals": c.goals, "secrets": c.secrets,
        "relationships": c.relationships, "first_appearance": c.first_appearance,
        "notes": c.notes, "summary": c.summary,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }


@router.post("/", status_code=201)
def create_character(payload: CharacterIn) -> dict:
    db: Session = SessionLocal()
    try:
        c = Character(id=str(uuid.uuid4()), **payload.model_dump())
        db.add(c)
        db.commit()
        db.refresh(c)
        return _to_dict(c)
    finally:
        db.close()


@router.get("/{character_id}")
def get_character(character_id: str) -> dict:
    db: Session = SessionLocal()
    try:
        c = db.query(Character).filter(Character.id == character_id).first()
        if not c:
            raise HTTPException(status_code=404, detail="Character not found")
        return _to_dict(c)
    finally:
        db.close()


@router.patch("/{character_id}")
def update_character(character_id: str, payload: CharacterUpdate) -> dict:
    db: Session = SessionLocal()
    try:
        c = db.query(Character).filter(Character.id == character_id).first()
        if not c:
            raise HTTPException(status_code=404, detail="Character not found")
        for k, v in payload.model_dump(exclude_unset=True).items():
            setattr(c, k, v)
        c.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(c)
        return _to_dict(c)
    finally:
        db.close()


@router.delete("/{character_id}", status_code=204)
def delete_character(character_id: str) -> None:
    db: Session = SessionLocal()
    try:
        c = db.query(Character).filter(Character.id == character_id).first()
        if not c:
            raise HTTPException(status_code=404, detail="Character not found")
        db.delete(c)
        db.commit()
    finally:
        db.close()
""")

w("routes/lore.py", """
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.session import SessionLocal
from models.extra import Lore

router = APIRouter()


class LoreIn(BaseModel):
    project_id: str
    lore_type: str
    name: str
    description: str | None = None
    tags: list[str] | None = None
    related_chapters: list[str] | None = None
    related_characters: list[str] | None = None
    lore_metadata: dict | None = None


class LoreUpdate(BaseModel):
    lore_type: str | None = None
    name: str | None = None
    description: str | None = None
    tags: list[str] | None = None
    related_chapters: list[str] | None = None
    related_characters: list[str] | None = None
    lore_metadata: dict | None = None


def _to_dict(l: Lore) -> dict:
    return {
        "id": l.id, "project_id": l.project_id, "lore_type": l.lore_type,
        "name": l.name, "description": l.description, "tags": l.tags,
        "related_chapters": l.related_chapters, "related_characters": l.related_characters,
        "metadata": l.lore_metadata,
        "created_at": l.created_at.isoformat() if l.created_at else None,
        "updated_at": l.updated_at.isoformat() if l.updated_at else None,
    }


@router.post("/", status_code=201)
def create_lore(payload: LoreIn) -> dict:
    db: Session = SessionLocal()
    try:
        row = Lore(id=str(uuid.uuid4()), **payload.model_dump())
        db.add(row)
        db.commit()
        db.refresh(row)
        return _to_dict(row)
    finally:
        db.close()


@router.get("/{lore_id}")
def get_lore(lore_id: str) -> dict:
    db: Session = SessionLocal()
    try:
        row = db.query(Lore).filter(Lore.id == lore_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="Lore not found")
        return _to_dict(row)
    finally:
        db.close()


@router.patch("/{lore_id}")
def update_lore(lore_id: str, payload: LoreUpdate) -> dict:
    db: Session = SessionLocal()
    try:
        row = db.query(Lore).filter(Lore.id == lore_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="Lore not found")
        for k, v in payload.model_dump(exclude_unset=True).items():
            setattr(row, k, v)
        row.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(row)
        return _to_dict(row)
    finally:
        db.close()


@router.delete("/{lore_id}", status_code=204)
def delete_lore(lore_id: str) -> None:
    db: Session = SessionLocal()
    try:
        row = db.query(Lore).filter(Lore.id == lore_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="Lore not found")
        db.delete(row)
        db.commit()
    finally:
        db.close()
""")

w("routes/timeline.py", """
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.session import SessionLocal
from models.extra import TimelineItem

router = APIRouter()


class TimelineIn(BaseModel):
    project_id: str
    title: str
    event_date: str | None = None
    relative_order: str | None = None
    description: str | None = None
    involved_characters: list[str] | None = None
    related_chapters: list[str] | None = None
    timeline_metadata: dict | None = None


class TimelineUpdate(BaseModel):
    title: str | None = None
    event_date: str | None = None
    relative_order: str | None = None
    description: str | None = None
    involved_characters: list[str] | None = None
    related_chapters: list[str] | None = None
    timeline_metadata: dict | None = None


def _to_dict(t: TimelineItem) -> dict:
    return {
        "id": t.id, "project_id": t.project_id, "title": t.title,
        "event_date": t.event_date, "relative_order": t.relative_order,
        "description": t.description, "involved_characters": t.involved_characters,
        "related_chapters": t.related_chapters, "metadata": t.timeline_metadata,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
    }


@router.post("/", status_code=201)
def create_event(payload: TimelineIn) -> dict:
    db: Session = SessionLocal()
    try:
        row = TimelineItem(id=str(uuid.uuid4()), **payload.model_dump())
        db.add(row)
        db.commit()
        db.refresh(row)
        return _to_dict(row)
    finally:
        db.close()


@router.get("/{event_id}")
def get_event(event_id: str) -> dict:
    db: Session = SessionLocal()
    try:
        row = db.query(TimelineItem).filter(TimelineItem.id == event_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="Event not found")
        return _to_dict(row)
    finally:
        db.close()


@router.patch("/{event_id}")
def update_event(event_id: str, payload: TimelineUpdate) -> dict:
    db: Session = SessionLocal()
    try:
        row = db.query(TimelineItem).filter(TimelineItem.id == event_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="Event not found")
        for k, v in payload.model_dump(exclude_unset=True).items():
            setattr(row, k, v)
        row.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(row)
        return _to_dict(row)
    finally:
        db.close()


@router.delete("/{event_id}", status_code=204)
def delete_event(event_id: str) -> None:
    db: Session = SessionLocal()
    try:
        row = db.query(TimelineItem).filter(TimelineItem.id == event_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="Event not found")
        db.delete(row)
        db.commit()
    finally:
        db.close()
""")

w("routes/settings.py", """
from __future__ import annotations

import logging

from fastapi import APIRouter
from pydantic import BaseModel

from db.session import SessionLocal
from models.extra import Settings

logger = logging.getLogger("novelforge.settings")
router = APIRouter()

_SETTINGS_ID = "app-settings"


class SettingsIn(BaseModel):
    provider: str = "ollama"
    base_url: str = "http://localhost:11434"
    api_key: str | None = None
    model: str = "llama3.1:8b"
    temperature: float = 0.7
    max_tokens: int = 2048


def _defaults() -> dict:
    return {
        "provider": "ollama",
        "base_url": "http://localhost:11434",
        "api_key": None,
        "model": "llama3.1:8b",
        "temperature": 0.7,
        "max_tokens": 2048,
    }


def _to_dict(row: Settings) -> dict:
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
        row = db.query(Settings).filter(Settings.id == _SETTINGS_ID).first()
        return _to_dict(row) if row else _defaults()
    finally:
        db.close()


@router.post("/settings/current")
async def save_settings(payload: SettingsIn) -> dict:
    db = SessionLocal()
    try:
        row = db.query(Settings).filter(Settings.id == _SETTINGS_ID).first()
        if not row:
            row = Settings(id=_SETTINGS_ID, active=True, **payload.model_dump())
            db.add(row)
        else:
            for k, v in payload.model_dump().items():
                setattr(row, k, v)
        db.commit()
        db.refresh(row)
        return _to_dict(row)
    finally:
        db.close()


@router.post("/settings/test")
async def test_connection(payload: SettingsIn) -> dict:
    from services.providers.base import ProviderSettings
    from services.providers.openai_compat import build_client

    settings = ProviderSettings(
        provider=payload.provider,
        base_url=payload.base_url,
        api_key=payload.api_key,
        model=payload.model,
        temperature=payload.temperature,
        max_tokens=payload.max_tokens,
    )
    client = build_client(settings)
    try:
        result = await client.chat(system="Respond with the single word: OK", user="ping")
        return {"ok": True, "response": result[:200]}
    except Exception as exc:
        logger.warning("Connection test failed: %s", exc)
        return {"ok": False, "error": str(exc)}
""")

w("routes/jobs.py", """
from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.session import SessionLocal
from models.extra import Job

logger = logging.getLogger("novelforge.jobs")
router = APIRouter()

# In-memory cancel flags per job_id
_cancel_flags: dict[str, asyncio.Event] = {}


class JobIn(BaseModel):
    project_id: str
    kind: str
    params: dict[str, Any] | None = None


def _to_dict(j: Job) -> dict:
    return {
        "id": j.id,
        "project_id": j.project_id,
        "kind": j.kind,
        "status": j.status,
        "params": j.params,
        "result": j.result,
        "error": j.error,
        "created_at": j.created_at.isoformat() if j.created_at else None,
        "updated_at": j.updated_at.isoformat() if j.updated_at else None,
    }


@router.post("/jobs", status_code=201)
def create_job(payload: JobIn) -> dict:
    db: Session = SessionLocal()
    try:
        j = Job(
            id=str(uuid.uuid4()),
            project_id=payload.project_id,
            kind=payload.kind,
            status="queued",
            params=payload.params,
        )
        db.add(j)
        db.commit()
        db.refresh(j)
        _cancel_flags[j.id] = asyncio.Event()
        return _to_dict(j)
    finally:
        db.close()


@router.get("/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    db: Session = SessionLocal()
    try:
        j = db.query(Job).filter(Job.id == job_id).first()
        if not j:
            raise HTTPException(status_code=404, detail="Job not found")
        return _to_dict(j)
    finally:
        db.close()


@router.post("/jobs/{job_id}/cancel")
def cancel_job(job_id: str) -> dict:
    flag = _cancel_flags.get(job_id)
    if flag:
        flag.set()
    db: Session = SessionLocal()
    try:
        j = db.query(Job).filter(Job.id == job_id).first()
        if j and j.status in {"queued", "running"}:
            j.status = "cancelled"
            j.updated_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        db.close()
    return {"cancelled": True}


@router.websocket("/ws/jobs/{job_id}")
async def job_stream(ws: WebSocket, job_id: str) -> None:
    await ws.accept()
    try:
        for _ in range(300):
            db: Session = SessionLocal()
            try:
                j = db.query(Job).filter(Job.id == job_id).first()
                if not j:
                    await ws.send_json({"error": "Job not found"})
                    break
                await ws.send_json(_to_dict(j))
                if j.status in {"done", "failed", "cancelled"}:
                    break
            finally:
                db.close()
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass
    finally:
        try:
            await ws.close()
        except Exception:
            pass
""")

w("routes/ai.py", """
from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from db.session import SessionLocal
from models.extra import Settings
from services.providers.base import ProviderSettings
from services.providers.openai_compat import build_client
from services.context.builder import ProjectContext

logger = logging.getLogger("novelforge.ai")
router = APIRouter()


class AIRequest(BaseModel):
    project_id: str | None = None
    chapter_id: str | None = None
    action: str = "continue"
    text: str | None = None
    instruction: str | None = None


def _get_settings() -> ProviderSettings:
    db = SessionLocal()
    try:
        row = db.query(Settings).filter(Settings.id == "app-settings").first()
        if not row:
            return ProviderSettings()
        return ProviderSettings(
            provider=row.provider,
            base_url=row.base_url,
            api_key=row.api_key,
            model=row.model,
            temperature=row.temperature,
            max_tokens=row.max_tokens,
        )
    finally:
        db.close()


_ACTION_PROMPTS: dict[str, str] = {
    "continue": "Tiếp tục viết nội dung dựa trên đoạn hiện tại. Giữ văn phong, không lặp câu mở đầu.",
    "rewrite": "Viết lại đoạn sau cho rõ ràng, mượt mà hơn, giữ nguyên ý.",
    "expand": "Phát triển thêm chi tiết cho đoạn sau: bối cảnh, cảm xúc, hành động.",
    "shorten": "Rút gọn đoạn sau mà giữ nguyên thông tin chính.",
    "dialogue": "Cải thiện hội thoại cho tự nhiên, có sắc thái nhân vật.",
    "emotional": "Làm văn bản sau giàu cảm xúc và sâu sắc hơn.",
    "cinematic": "Làm văn bản mang tính điện ảnh: hình ảnh, âm thanh, chuyển động.",
    "grammar": "Sửa ngữ pháp, dấu câu, chính tả, giữ nguyên ý.",
    "summarize_chapter": "Tóm tắt chương thành 1-2 đoạn ngắn, nhấn mạnh sự kiện quan trọng.",
    "summarize_project": "Tóm tắt toàn bộ project: cốt truyện, mâu thuẫn chính, hướng đi.",
    "continuity": "Kiểm tra lỗi nhất quán: thời gian, hành động nhân vật, địa điểm, lore.",
    "plot_holes": "Liệt kê plot hole tiềm ẩn và đề xuất cách khắc phục.",
    "next_scene": "Đề xuất 3 ý cảnh tiếp theo phù hợp chương hiện tại.",
    "character": "Sinh hồ sơ nhân vật chi tiết theo yêu cầu.",
    "world": "Sinh lore/worldbuilding chi tiết theo yêu cầu.",
    "translate_vi_en": "Dịch sang tiếng Anh, giữ văn phong văn học.",
    "translate_en_vi": "Dịch sang tiếng Việt, giữ văn phong văn học.",
    "premise": "Sinh concept câu chuyện hấp dẫn.",
    "outline": "Sinh dàn ý cấu trúc truyện rõ ràng.",
}


def _system_prompt(ctx: ProjectContext) -> str:
    parts = [
        "Bạn là trợ lý viết tiểu thuyết chuyên nghiệp. Hỗ trợ tác giả viết, chỉnh sửa, tóm tắt, duy trì nhất quán cốt truyện.",
        "Phản hồi bằng ngôn ngữ mà yêu cầu sử dụng. Không thêm nội dung không được yêu cầu.",
    ]
    char_ctx = ctx.character_context()
    if char_ctx.strip():
        parts.append(f"## Nhân vật\\n{char_ctx[:3000]}")
    lore_ctx = ctx.lore_context()
    if lore_ctx.strip():
        parts.append(f"## Worldbuilding / Lore\\n{lore_ctx[:2000]}")
    timeline_ctx = ctx.timeline_context()
    if timeline_ctx.strip():
        parts.append(f"## Timeline\\n{timeline_ctx[:1000]}")
    style_ctx = ctx.style_context()
    if style_ctx.strip():
        parts.append(f"## Hướng dẫn văn phong\\n{style_ctx[:500]}")
    return "\\n\\n".join(parts)


def _user_prompt(action: str, text: str, instruction: str, chapter_context: str) -> str:
    action_text = _ACTION_PROMPTS.get(action, "Hỗ trợ viết tiểu thuyết.")
    parts = [action_text]
    if chapter_context.strip():
        parts.append(f"Context:\\n{chapter_context[:4000]}")
    if text.strip():
        parts.append(f"Input:\\n{text}")
    if instruction.strip():
        parts.append(f"Instruction:\\n{instruction}")
    return "\\n\\n".join(parts)


@router.post("/ai/run")
async def run_ai(payload: AIRequest) -> dict:
    settings = _get_settings()
    client = build_client(settings)

    ctx = ProjectContext(payload.project_id)
    if payload.project_id:
        await ctx.load()

    system = _system_prompt(ctx)
    chapter_ctx = ctx.chapter_context(payload.chapter_id) if payload.chapter_id else ""
    user = _user_prompt(
        action=payload.action,
        text=payload.text or "",
        instruction=payload.instruction or "",
        chapter_context=chapter_ctx,
    )

    try:
        result = await client.chat(system=system, user=user)
        return {"result": result, "action": payload.action}
    except Exception as exc:
        logger.error("AI error action=%s: %s", payload.action, exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"AI provider error: {exc}")


@router.websocket("/ws/ai")
async def ai_stream(ws: WebSocket) -> None:
    await ws.accept()
    try:
        data = await ws.receive_json()
        payload = AIRequest(**data)
        settings = _get_settings()
        client = build_client(settings)

        ctx = ProjectContext(payload.project_id)
        if payload.project_id:
            await ctx.load()

        system = _system_prompt(ctx)
        chapter_ctx = ctx.chapter_context(payload.chapter_id) if payload.chapter_id else ""
        user = _user_prompt(
            action=payload.action,
            text=payload.text or "",
            instruction=payload.instruction or "",
            chapter_context=chapter_ctx,
        )

        result = await client.chat(system=system, user=user)
        words = result.split(" ")
        for i, word in enumerate(words):
            chunk = word + (" " if i < len(words) - 1 else "")
            await ws.send_json({"delta": chunk, "done": False})
            await asyncio.sleep(0.015)
        await ws.send_json({"delta": "", "done": True, "full": result})
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.error("AI WS error: %s", exc)
        try:
            await ws.send_json({"error": str(exc), "done": True})
        except Exception:
            pass
    finally:
        try:
            await ws.close()
        except Exception:
            pass
""")

w("routes/export.py", """
from __future__ import annotations

import html as htmlmod
import io
import json
import zipfile
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.session import SessionLocal
from models.project import Project
from models.chapter import Chapter
from models.extra import Character, Lore, TimelineItem

router = APIRouter()


class ExportRequest(BaseModel):
    project_id: str
    fmt: str = "md"


def _safe_filename(name: str) -> str:
    return "".join(c if c.isalnum() or c in " _-" else "_" for c in (name or "export"))


def _build_markdown(project: Project, chapters: list) -> str:
    lines = [f"# {project.title}", ""]
    if project.description:
        lines += [project.description, ""]
    for ch in chapters:
        lines += [f"## {ch.title}", ""]
        if ch.content:
            lines += [ch.content, ""]
    return "\\n".join(lines)


def _build_txt(project: Project, chapters: list) -> str:
    lines = [project.title, "=" * len(project.title), ""]
    if project.description:
        lines += [project.description, ""]
    for ch in chapters:
        lines += [ch.title, "-" * len(ch.title), ""]
        if ch.content:
            lines += [ch.content, ""]
    return "\\n".join(lines)


def _build_html(project: Project, chapters: list) -> str:
    parts = [
        "<!DOCTYPE html><html><head>",
        f'<meta charset="utf-8"><title>{htmlmod.escape(project.title)}</title>',
        "<style>body{font-family:Georgia,serif;max-width:800px;margin:0 auto;padding:2em;line-height:1.8;color:#1a1a1a}</style>",
        "</head><body>",
        f"<h1>{htmlmod.escape(project.title)}</h1>",
    ]
    if project.description:
        parts.append(f"<p>{htmlmod.escape(project.description)}</p>")
    for ch in chapters:
        parts.append(f"<h2>{htmlmod.escape(ch.title)}</h2>")
        if ch.content:
            for para in ch.content.split("\\n\\n"):
                if para.strip():
                    parts.append(f"<p>{htmlmod.escape(para.strip())}</p>")
    parts.append("</body></html>")
    return "\\n".join(parts)


@router.post("/export")
async def export_project(payload: ExportRequest) -> Response:
    db: Session = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == payload.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        chapters = (
            db.query(Chapter)
            .filter(Chapter.project_id == payload.project_id)
            .order_by(Chapter.scene_order)
            .all()
        )
        fmt = payload.fmt.lower()
        name = _safe_filename(project.title)

        if fmt == "md":
            return Response(
                content=_build_markdown(project, chapters).encode("utf-8"),
                media_type="text/markdown",
                headers={"Content-Disposition": f'attachment; filename="{name}.md"'},
            )
        if fmt == "txt":
            return Response(
                content=_build_txt(project, chapters).encode("utf-8"),
                media_type="text/plain",
                headers={"Content-Disposition": f'attachment; filename="{name}.txt"'},
            )
        if fmt == "html":
            return Response(
                content=_build_html(project, chapters).encode("utf-8"),
                media_type="text/html",
                headers={"Content-Disposition": f'attachment; filename="{name}.html"'},
            )
        if fmt == "zip":
            characters = db.query(Character).filter(Character.project_id == payload.project_id).all()
            lore_items = db.query(Lore).filter(Lore.project_id == payload.project_id).all()
            timeline = db.query(TimelineItem).filter(TimelineItem.project_id == payload.project_id).all()
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.writestr("story.md", _build_markdown(project, chapters))
                zf.writestr("story.txt", _build_txt(project, chapters))
                zf.writestr("characters.json", json.dumps(
                    [{"id": c.id, "name": c.name, "role": c.role, "alias": c.alias,
                      "personality": c.personality, "goals": c.goals} for c in characters],
                    ensure_ascii=False, indent=2,
                ))
                zf.writestr("lore.json", json.dumps(
                    [{"id": l.id, "name": l.name, "type": l.lore_type, "description": l.description}
                     for l in lore_items],
                    ensure_ascii=False, indent=2,
                ))
                zf.writestr("timeline.json", json.dumps(
                    [{"id": t.id, "title": t.title, "date": t.event_date, "description": t.description}
                     for t in timeline],
                    ensure_ascii=False, indent=2,
                ))
                zf.writestr("project.json", json.dumps({
                    "id": project.id, "title": project.title,
                    "description": project.description, "genre": project.genre,
                    "language": project.language,
                    "exported_at": datetime.utcnow().isoformat(),
                }, ensure_ascii=False, indent=2))
            return Response(
                content=buf.getvalue(),
                media_type="application/zip",
                headers={"Content-Disposition": f'attachment; filename="{name}.zip"'},
            )
        raise HTTPException(status_code=400, detail=f"Unknown format: {fmt}")
    finally:
        db.close()
""")

# ── services ──────────────────────────────────────────────────────────────────

w("services/context/builder.py", """
from __future__ import annotations

import json
from typing import Any

from db.session import SessionLocal
from models.extra import Character, Lore, TimelineItem
from models.chapter import Chapter
from models.project import Project


class ProjectContext:
    def __init__(self, project_id: str | None = None) -> None:
        self.project_id = project_id
        self.project: Project | None = None
        self.chapters: list[Chapter] = []
        self.characters: list[Character] = []
        self.lore_items: list[Lore] = []
        self.timeline_items: list[TimelineItem] = []

    async def load(self) -> None:
        if not self.project_id:
            return
        db = SessionLocal()
        try:
            self.project = db.query(Project).filter(Project.id == self.project_id).first()
            self.chapters = (
                db.query(Chapter)
                .filter(Chapter.project_id == self.project_id)
                .order_by(Chapter.scene_order.asc())
                .all()
            )
            self.characters = (
                db.query(Character)
                .filter(Character.project_id == self.project_id)
                .order_by(Character.name.asc())
                .all()
            )
            self.lore_items = (
                db.query(Lore)
                .filter(Lore.project_id == self.project_id)
                .order_by(Lore.lore_type.asc(), Lore.name.asc())
                .all()
            )
            self.timeline_items = (
                db.query(TimelineItem)
                .filter(TimelineItem.project_id == self.project_id)
                .order_by(TimelineItem.created_at.asc())
                .all()
            )
        finally:
            db.close()

    def chapter_context(self, chapter_id: str | None, max_surrounding: int = 2) -> str:
        if not self.chapters:
            return ""
        target_idx = next((i for i, c in enumerate(self.chapters) if c.id == chapter_id), -1)
        if target_idx == -1:
            selected = self.chapters[:max(3, max_surrounding * 2 + 1)]
        else:
            start = max(0, target_idx - max_surrounding)
            end = min(len(self.chapters), target_idx + max_surrounding + 1)
            selected = self.chapters[start:end]

        parts: list[str] = []
        for ch in selected:
            marker = " [CURRENT]" if ch.id == chapter_id else ""
            heading = ch.title or "Chương không tên"
            summary = _clean(ch.summary)
            content = _clean(ch.content)
            parts.append(
                f"## {heading}{marker}\\n"
                + (f"{summary}\\n" if summary else "")
                + (f"{content[:1200]}\\n" if content else "")
            )
        return "\\n".join(parts)

    def character_context(self) -> str:
        if not self.characters:
            return ""
        return "\\n".join(_character_block(c) for c in self.characters[:40])

    def lore_context(self) -> str:
        if not self.lore_items:
            return ""
        grouped: dict[str, list] = {}
        order: list[str] = []
        for item in self.lore_items:
            grouped.setdefault(item.lore_type, []).append(item)
            if item.lore_type not in order:
                order.append(item.lore_type)
        parts: list[str] = []
        for lore_type in order[:20]:
            parts.append(f"### {lore_type}")
            for item in grouped[lore_type][:25]:
                parts.append(_lore_block(item))
        return "\\n".join(parts)

    def timeline_context(self) -> str:
        if not self.timeline_items:
            return ""
        return "\\n".join(
            f"- {item.title} ({item.event_date or item.relative_order or '...'}): "
            + _clean(item.description)
            for item in self.timeline_items[:50]
        )

    def style_context(self) -> str:
        return _clean(self.project.style_guide) if self.project else ""


def _clean(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _character_block(c: Character) -> str:
    lines = [f"- {c.name or 'Không tên'}"]
    if c.alias:      lines.append(f"  Bí danh: {c.alias}")
    if c.role:       lines.append(f"  Vai trò: {c.role}")
    if c.age:        lines.append(f"  Tuổi: {c.age}")
    if c.personality: lines.append(f"  Tính cách: {c.personality}")
    if c.appearance: lines.append(f"  Ngoại hình: {c.appearance}")
    if c.goals:      lines.append(f"  Mục tiêu: {c.goals}")
    if c.secrets:    lines.append(f"  Bí mật: {c.secrets}")
    if c.relationships:
        lines.append(f"  Mối quan hệ: {json.dumps(c.relationships, ensure_ascii=False)}")
    if c.summary:    lines.append(f"  Tóm tắt: {c.summary}")
    return "\\n".join(lines)


def _lore_block(item: Lore) -> str:
    lines = [f"- {item.name} ({item.lore_type})"]
    if item.description:
        lines.append(f"  {item.description}")
    if item.tags:
        lines.append(f"  Tags: {', '.join(str(t) for t in item.tags)}")
    return "\\n".join(lines)
""")

# ── app.py ────────────────────────────────────────────────────────────────────

w("app.py", """
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db.base import Base, engine
from routes import health, projects, chapters, characters, lore, timeline, settings, ai, jobs
from routes import export as export_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger("novelforge")


def create_app() -> FastAPI:
    Base.metadata.create_all(bind=engine)
    logger.info("DB tables created / verified")

    application = FastAPI(
        title="NovelForge Engine",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(health.router, prefix="/api")
    application.include_router(projects.router, prefix="/api/projects")
    application.include_router(chapters.router, prefix="/api/chapters")
    application.include_router(characters.router, prefix="/api/characters")
    application.include_router(lore.router, prefix="/api/lore")
    application.include_router(timeline.router, prefix="/api/timeline")
    application.include_router(settings.router, prefix="/api")
    application.include_router(ai.router, prefix="/api")
    application.include_router(jobs.router, prefix="/api")
    application.include_router(export_router.router, prefix="/api")

    return application


app = create_app()
""")

w("run.py", """
import uvicorn

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=9000, reload=False, log_level="info")
""")

print("All files written.")
