from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session
from db.session import SessionLocal
from models.project import Project
import uuid
from datetime import datetime, timezone


router = APIRouter()


class ProjectIn(BaseModel):
    title: str = Field(max_length=200)
    description: str | None = None
    genre: str | None = None
    language: str = "vi"
    style_guide: str | None = None
    summary: str | None = None


class ProjectUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    description: str | None = None
    genre: str | None = None
    language: str | None = None
    style_guide: str | None = None
    summary: str | None = None


def to_dict(p: Project):
    return {
        "id": p.id,
        "title": p.title,
        "description": p.description,
        "genre": p.genre,
        "language": p.language,
        "style_guide": p.style_guide,
        "summary": p.summary,
        "created_at": p.created_at.isoformat()+'Z' if p.created_at else None,
        "updated_at": p.updated_at.isoformat()+'Z' if p.updated_at else None,
    }

def to_dict_with_stats(p: Project, db=None):
    """Project dict with computed word_count."""
    d = to_dict(p)
    if db is None:
        db = SessionLocal()
        close_db = True
    else:
        close_db = False
    try:
        from models.chapter import Chapter
        total = db.query(func.coalesce(func.sum(Chapter.word_count), 0)).filter(
            Chapter.project_id == p.id
        ).scalar()
        d["word_count"] = total or 0
    except Exception:
        d["word_count"] = 0
    finally:
        if close_db:
            db.close()
    return d


@router.get("/projects/")
def list_projects():
    db: Session = SessionLocal()
    try:
        items = db.query(Project).order_by(Project.updated_at.desc()).all()
        return [to_dict_with_stats(p, db) for p in items]
    finally:
        db.close()


@router.post("/projects/", status_code=201)
def create_project(payload: ProjectIn):
    db: Session = SessionLocal()
    try:
        p = Project(id=str(uuid.uuid4()), **payload.model_dump())
        db.add(p)
        db.commit()
        db.refresh(p)
        return to_dict(p)
    finally:
        db.close()


@router.get("/projects/{project_id}")
def get_project(project_id: str):
    db: Session = SessionLocal()
    try:
        p = db.query(Project).filter(Project.id == project_id).first()
        if not p:
            raise HTTPException(status_code=404, detail="Not found")
        return to_dict(p)
    finally:
        db.close()


@router.patch("/projects/{project_id}")
def update_project(project_id: str, payload: ProjectUpdate):
    db: Session = SessionLocal()
    try:
        p = db.query(Project).filter(Project.id == project_id).first()
        if not p:
            raise HTTPException(status_code=404, detail="Not found")
        data = payload.model_dump(exclude_unset=True)
        for k, v in data.items():
            setattr(p, k, v)
        p.updated_at = datetime.now(timezone.utc)
        db.add(p)
        db.commit()
        db.refresh(p)
        return to_dict(p)
    finally:
        db.close()


@router.delete("/projects/{project_id}", status_code=204)
def delete_project(project_id: str):
    from models.chapter import Chapter
    from models.extra import Character, Lore, TimelineItem, Job
    from models.summary import Summary
    from services.search import remove_chapter, remove_character, remove_lore

    db: Session = SessionLocal()
    try:
        p = db.query(Project).filter(Project.id == project_id).first()
        if not p:
            raise HTTPException(status_code=404, detail="Not found")

        # Cascade delete all related data
        chapters = db.query(Chapter).filter(Chapter.project_id == project_id).all()
        chapter_ids = [c.id for c in chapters]

        db.query(Summary).filter(Summary.project_id == project_id).delete()
        db.query(Job).filter(Job.project_id == project_id).delete()
        db.query(TimelineItem).filter(TimelineItem.project_id == project_id).delete()

        lore_items = db.query(Lore).filter(Lore.project_id == project_id).all()
        lore_ids = [item.id for item in lore_items]
        db.query(Lore).filter(Lore.project_id == project_id).delete()

        characters = db.query(Character).filter(Character.project_id == project_id).all()
        char_ids = [c.id for c in characters]
        db.query(Character).filter(Character.project_id == project_id).delete()

        db.query(Chapter).filter(Chapter.project_id == project_id).delete()
        db.delete(p)
        db.commit()

        # Clean up FTS index entries
        for cid in chapter_ids:
            try:
                remove_chapter(cid)
            except Exception:
                pass
        for lid in lore_ids:
            try:
                remove_lore(lid)
            except Exception:
                pass
        for chid in char_ids:
            try:
                remove_character(chid)
            except Exception:
                pass
    finally:
        db.close()




