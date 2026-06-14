from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from db.session import SessionLocal
from models.chapter import Chapter
import uuid
from datetime import datetime, timezone


router = APIRouter()


class ChapterIn(BaseModel):
    project_id: str
    title: str
    content: str | None = ""
    scene_order: int = 0
    status: str | None = "draft"
    summary: str | None = None
    notes: str | None = None


class ChapterUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    scene_order: int | None = None
    status: str | None = None
    summary: str | None = None
    notes: str | None = None


def count_words(text: str) -> int:
    if not text:
        return 0
    return len([w for w in text.split() if w])


def to_dict(c: Chapter):
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
        "created_at": c.created_at.isoformat()+'Z' if c.created_at else None,
        "updated_at": c.updated_at.isoformat()+'Z' if c.updated_at else None,
    }


@router.get("/projects/{project_id}/chapters")
def list_chapters(project_id: str):
    db: Session = SessionLocal()
    try:
        items = (
            db.query(Chapter)
            .filter(Chapter.project_id == project_id)
            .order_by(Chapter.scene_order)
            .all()
        )
        return [to_dict(c) for c in items]
    finally:
        db.close()


@router.post("/chapters/", status_code=201)
def create_chapter(payload: ChapterIn):
    db: Session = SessionLocal()
    try:
        c = Chapter(
            id=str(uuid.uuid4()),
            **payload.model_dump(),
            word_count=count_words(payload.content),
        )
        db.add(c)
        db.commit()
        db.refresh(c)
        return to_dict(c)
    finally:
        db.close()


@router.get("/chapters/{chapter_id}")
def get_chapter(chapter_id: str):
    db: Session = SessionLocal()
    try:
        c = db.query(Chapter).filter(Chapter.id == chapter_id).first()
        if not c:
            raise HTTPException(status_code=404, detail="Not found")
        return to_dict(c)
    finally:
        db.close()


@router.patch("/chapters/{chapter_id}")
def update_chapter(chapter_id: str, payload: ChapterUpdate):
    db: Session = SessionLocal()
    try:
        c = db.query(Chapter).filter(Chapter.id == chapter_id).first()
        if not c:
            raise HTTPException(status_code=404, detail="Not found")
        data = payload.model_dump(exclude_unset=True)
        for k, v in data.items():
            setattr(c, k, v)
        if "content" in data:
            c.word_count = count_words(data.get("content") or "")
        c.updated_at = datetime.now(timezone.utc)
        db.add(c)
        db.commit()
        db.refresh(c)
        return to_dict(c)
    finally:
        db.close()


@router.delete("/chapters/{chapter_id}", status_code=204)
def delete_chapter(chapter_id: str):
    db: Session = SessionLocal()
    try:
        c = db.query(Chapter).filter(Chapter.id == chapter_id).first()
        if not c:
            raise HTTPException(status_code=404, detail="Not found")
        db.delete(c)
        db.commit()
        # Remove from FTS index
        try:
            from services.search import remove_chapter
            remove_chapter(chapter_id)
        except Exception:
            pass
    finally:
        db.close()




