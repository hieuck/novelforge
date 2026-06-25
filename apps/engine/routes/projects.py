import uuid
from datetime import UTC, datetime

from db.session import SessionLocal
from fastapi import APIRouter, HTTPException
from models.chapter import Chapter
from models.extra import Character, Lore, TimelineItem
from models.image import GeneratedImage
from models.project import Project
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

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
        "created_at": p.created_at.isoformat() + "Z" if p.created_at else None,
        "updated_at": p.updated_at.isoformat() + "Z" if p.updated_at else None,
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

        total = db.query(func.coalesce(func.sum(Chapter.word_count), 0)).filter(Chapter.project_id == p.id).scalar()
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
        return to_dict_with_stats(p, db)
    finally:
        db.close()


@router.get("/projects/{project_id}/stats")
def get_project_stats(project_id: str) -> dict:
    db: Session = SessionLocal()
    try:
        p = db.query(Project).filter(Project.id == project_id).first()
        if not p:
            raise HTTPException(status_code=404, detail="Not found")
        chapters = db.query(func.count(Chapter.id)).filter(Chapter.project_id == project_id).scalar() or 0
        words = db.query(func.coalesce(func.sum(Chapter.word_count), 0)).filter(Chapter.project_id == project_id).scalar() or 0
        characters = db.query(func.count(Character.id)).filter(Character.project_id == project_id).scalar() or 0
        images = db.query(func.count(GeneratedImage.id)).filter(GeneratedImage.project_id == project_id).scalar() or 0
        lore = db.query(func.count(Lore.id)).filter(Lore.project_id == project_id).scalar() or 0
        timeline = db.query(func.count(TimelineItem.id)).filter(TimelineItem.project_id == project_id).scalar() or 0
        return {
            "chapters": chapters,
            "words": words,
            "characters": characters,
            "images": images,
            "lore": lore,
            "timeline": timeline,
        }
    finally:
        db.close()


@router.get("/projects/{project_id}/word-counts")
def get_project_word_counts(project_id: str) -> list[dict]:
    db: Session = SessionLocal()
    try:
        p = db.query(Project).filter(Project.id == project_id).first()
        if not p:
            raise HTTPException(status_code=404, detail="Not found")
        chapters = db.query(Chapter).filter(
            Chapter.project_id == project_id
        ).order_by(Chapter.scene_order).all()
        return [
            {
                "id": ch.id,
                "title": ch.title,
                "word_count": ch.word_count or 0,
                "scene_order": ch.scene_order or 0,
            }
            for ch in chapters
        ]
    finally:
        db.close()


@router.get("/projects/{project_id}/chapter-status-counts")
def get_chapter_status_counts(project_id: str) -> dict:
    db: Session = SessionLocal()
    try:
        p = db.query(Project).filter(Project.id == project_id).first()
        if not p:
            raise HTTPException(status_code=404, detail="Not found")
        from sqlalchemy import func as _func
        rows = db.query(Chapter.status, _func.count(Chapter.id)).filter(
            Chapter.project_id == project_id
        ).group_by(Chapter.status).all()
        counts = {"draft": 0, "revised": 0, "final": 0}
        total = 0
        for status, cnt in rows:
            s = status or "draft"
            if s in counts:
                counts[s] = cnt
            total += cnt
        counts["total"] = total
        return counts
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
        p.updated_at = datetime.now(UTC)
        db.add(p)
        db.commit()
        db.refresh(p)
        return to_dict(p)
    finally:
        db.close()


@router.delete("/projects/{project_id}", status_code=204)
def delete_project(project_id: str):
    from datetime import UTC, datetime

    # Auto-backup before destructive operation
    try:
        import shutil

        from db.paths import get_data_dir
        db_path = get_data_dir() / "novelforge.db"
        if db_path.exists():
            backup_dir = get_data_dir() / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            shutil.copy2(db_path, backup_dir / f"pre_delete_{ts}.db")
    except Exception:
        pass  # Backup failure should not block the delete

    from models.chapter import Chapter
    from models.extra import Character, Job, Lore, TimelineItem
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
