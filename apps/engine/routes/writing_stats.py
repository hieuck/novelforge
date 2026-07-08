"""Writing statistics endpoints for daily word-count tracking."""

from __future__ import annotations

from datetime import date, timedelta

from db.session import SessionLocal
from fastapi import APIRouter, HTTPException
from models.chapter import Chapter
from models.project import Project
from models.writing_session import WritingSession
from sqlalchemy import func
from sqlalchemy.orm import Session

router = APIRouter()


def _history(db: Session, project_id: str, days: int = 30) -> list[dict]:
    since = date.today() - timedelta(days=days - 1)
    rows = (
        db.query(WritingSession)
        .filter(WritingSession.project_id == project_id, WritingSession.date >= since)
        .order_by(WritingSession.date.desc())
        .all()
    )
    by_date = {r.date.isoformat(): r for r in rows}
    history = []
    for i in range(days - 1, -1, -1):
        d = date.today() - timedelta(days=i)
        ds = d.isoformat()
        session = by_date.get(ds)
        history.append(
            {
                "date": ds,
                "words_added": session.words_added if session else 0,
                "words_total": session.words_total if session else 0,
            }
        )
    return history


def _streak(history: list[dict], daily_goal: int) -> dict:
    """Compute current and longest streaks based on meeting the daily goal."""
    current = 0
    longest = 0
    run = 0
    # history is oldest -> newest
    for day in history:
        if day["words_added"] >= daily_goal and daily_goal > 0:
            run += 1
            current = run
            longest = max(longest, run)
        else:
            run = 0
            if day["words_added"] == 0:
                current = 0
    return {"current": current, "longest": longest}


@router.get("/projects/{project_id}/writing-stats")
def get_writing_stats(project_id: str, days: int = 30) -> dict:
    db: Session = SessionLocal()
    try:
        p = db.query(Project).filter(Project.id == project_id).first()
        if not p:
            raise HTTPException(status_code=404, detail="Not found")
        history = _history(db, project_id, max(1, min(days, 365)))
        total_words = (
            db.query(func.coalesce(func.sum(Chapter.word_count), 0)).filter(Chapter.project_id == project_id).scalar()
            or 0
        )
        today = date.today().isoformat()
        today_added = next((h["words_added"] for h in history if h["date"] == today), 0)
        goal = p.daily_goal or 0
        return {
            "project_id": project_id,
            "daily_goal": goal,
            "today_words": today_added,
            "total_words": total_words,
            "streak": _streak(history, goal),
            "history": history,
        }
    finally:
        db.close()
