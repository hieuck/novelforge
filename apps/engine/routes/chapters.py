import uuid
from datetime import UTC, datetime

from db.session import SessionLocal
from fastapi import APIRouter, HTTPException
from models.chapter import Chapter
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

router = APIRouter()


class ChapterIn(BaseModel):
    project_id: str
    title: str = Field(max_length=200)
    content: str | None = ""
    scene_order: int = 0
    status: str | None = "draft"
    summary: str | None = None
    notes: str | None = None
    illustration_url: str | None = None


class ChapterUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    content: str | None = None
    scene_order: int | None = None
    status: str | None = None
    summary: str | None = None
    notes: str | None = None
    illustration_url: str | None = None


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
        "illustration_url": c.illustration_url,
        "created_at": c.created_at.isoformat() + "Z" if c.created_at else None,
        "updated_at": c.updated_at.isoformat() + "Z" if c.updated_at else None,
    }


@router.get("/projects/{project_id}/chapters")
def list_chapters(project_id: str):
    db: Session = SessionLocal()
    try:
        items = db.query(Chapter).filter(Chapter.project_id == project_id).order_by(Chapter.scene_order).all()
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


@router.post("/chapters/{chapter_id}/duplicate", status_code=201)
def duplicate_chapter(chapter_id: str):
    db: Session = SessionLocal()
    try:
        orig = db.query(Chapter).filter(Chapter.id == chapter_id).first()
        if not orig:
            raise HTTPException(status_code=404, detail="Not found")
        new = Chapter(
            id=str(uuid.uuid4()),
            project_id=orig.project_id,
            title=(orig.title or "Untitled") + " (Copy)",
            content=orig.content or "",
            status="draft",
            word_count=orig.word_count or 0,
            scene_order=(orig.scene_order or 0) + 1,
            summary=orig.summary,
            notes=orig.notes,
            illustration_url=orig.illustration_url,
        )
        db.add(new)
        db.commit()
        db.refresh(new)
        return to_dict(new)
    finally:
        db.close()


@router.post("/chapters/{chapter_id}/move")
def move_chapter(chapter_id: str, position: int = 0):
    db: Session = SessionLocal()
    try:
        ch = db.query(Chapter).filter(Chapter.id == chapter_id).first()
        if not ch:
            raise HTTPException(status_code=404, detail="Not found")
        all_ch = db.query(Chapter).filter(Chapter.project_id == ch.project_id).order_by(Chapter.scene_order).all()
        if position < 0 or position >= len(all_ch):
            raise HTTPException(status_code=400, detail=f"Position must be between 0 and {len(all_ch) - 1}")
        current_order = ch.scene_order
        if current_order == position:
            return to_dict(ch)
        if current_order < position:
            for c in all_ch:
                if current_order < c.scene_order <= position:
                    c.scene_order -= 1
        else:
            for c in all_ch:
                if position <= c.scene_order < current_order:
                    c.scene_order += 1
        ch.scene_order = position
        ch.updated_at = datetime.now(UTC)
        db.commit()
        db.refresh(ch)
        return to_dict(ch)
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
        c.updated_at = datetime.now(UTC)
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


class ReorderIn(BaseModel):
    ordered_ids: list[str]


@router.post("/chapters/reorder", status_code=200)
def reorder_chapters(payload: ReorderIn):
    """Batch update scene_order based on the provided ID order."""
    db: Session = SessionLocal()
    try:
        for idx, ch_id in enumerate(payload.ordered_ids):
            db.query(Chapter).filter(Chapter.id == ch_id).update({"scene_order": idx, "updated_at": datetime.now(UTC)})
        db.commit()
        return {"success": True, "count": len(payload.ordered_ids)}
    finally:
        db.close()
