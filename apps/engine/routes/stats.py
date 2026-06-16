"""Dashboard statistics endpoint."""
from __future__ import annotations

from db.session import SessionLocal
from fastapi import APIRouter
from models.chapter import Chapter
from models.extra import Character, Lore, TimelineItem
from models.image import GeneratedImage
from models.project import Project
from sqlalchemy import func

router = APIRouter()


@router.get("/stats/dashboard")
def dashboard_stats() -> dict:
    db = SessionLocal()
    try:
        total_projects = db.query(func.count(Project.id)).scalar() or 0
        total_chapters = db.query(func.count(Chapter.id)).scalar() or 0
        total_characters = db.query(func.count(Character.id)).scalar() or 0
        total_words = db.query(func.coalesce(func.sum(Chapter.word_count), 0)).scalar() or 0
        total_images = db.query(func.count(GeneratedImage.id)).scalar() or 0
        total_lore = db.query(func.count(Lore.id)).scalar() or 0
        total_timeline = db.query(func.count(TimelineItem.id)).scalar() or 0
        return {
            "total_projects": total_projects,
            "total_chapters": total_chapters,
            "total_characters": total_characters,
            "total_words": total_words,
            "total_images": total_images,
            "total_lore": total_lore,
            "total_timeline": total_timeline,
        }
    finally:
        db.close()
