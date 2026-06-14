from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from db.session import SessionLocal
from models.extra import TimelineItem
import uuid
from datetime import datetime, timezone


router = APIRouter()


class TimelineIn(BaseModel):
    project_id: str | None = None
    title: str
    event_date: str | None = None
    relative_order: str | None = None
    description: str | None = None
    involved_characters: list | None = None
    related_chapters: list | None = None
    metadata: dict | None = None


class TimelineUpdate(BaseModel):
    title: str | None = None
    event_date: str | None = None
    relative_order: str | None = None
    description: str | None = None
    involved_characters: list | None = None
    related_chapters: list | None = None
    metadata: dict | None = None


def to_dict(row: TimelineItem):
    return {
        "id": row.id,
        "project_id": row.project_id,
        "title": row.title,
        "event_date": row.event_date,
        "relative_order": row.relative_order,
        "description": row.description,
        "involved_characters": row.involved_characters,
        "related_chapters": row.related_chapters,
        "metadata": row.meta_data,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


@router.get("/projects/{project_id}/timeline")
def list_timeline(project_id: str):
    db: Session = SessionLocal()
    try:
        items = db.query(TimelineItem).filter(TimelineItem.project_id == project_id).all()
        return [to_dict(x) for x in items]
    finally:
        db.close()


@router.post("/timeline/", status_code=201)
def create_timeline(payload: TimelineIn):
    db: Session = SessionLocal()
    try:
        row = TimelineItem(id=str(uuid.uuid4()), **payload.model_dump())
        db.add(row)
        db.commit()
        db.refresh(row)
        return to_dict(row)
    finally:
        db.close()


@router.get("/timeline/{event_id}")
def get_timeline(event_id: str):
    db: Session = SessionLocal()
    try:
        row = db.query(TimelineItem).filter(TimelineItem.id == event_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="Not found")
        return to_dict(row)
    finally:
        db.close()


@router.patch("/timeline/{event_id}")
def update_timeline(event_id: str, payload: TimelineUpdate):
    db: Session = SessionLocal()
    try:
        row = db.query(TimelineItem).filter(TimelineItem.id == event_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="Not found")
        data = payload.model_dump(exclude_unset=True)
        for k, v in data.items():
            setattr(row, k, v)
        row.updated_at = datetime.now(timezone.utc)
        db.add(row)
        db.commit()
        db.refresh(row)
        return to_dict(row)
    finally:
        db.close()


@router.delete("/timeline/{event_id}", status_code=204)
def delete_timeline(event_id: str):
    db: Session = SessionLocal()
    try:
        row = db.query(TimelineItem).filter(TimelineItem.id == event_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="Not found")
        db.delete(row)
        db.commit()
    finally:
        db.close()




