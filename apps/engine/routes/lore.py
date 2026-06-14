from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from db.session import SessionLocal
from models.extra import Lore
import uuid
from datetime import datetime, timezone


router = APIRouter()


class LoreIn(BaseModel):
    project_id: str | None = None
    lore_type: str
    name: str
    description: str | None = None
    tags: list | None = None
    related_chapters: list | None = None
    related_characters: list | None = None
    metadata: dict | None = None


class LoreUpdate(BaseModel):
    lore_type: str | None = None
    name: str | None = None
    description: str | None = None
    tags: list | None = None
    related_chapters: list | None = None
    related_characters: list | None = None
    metadata: dict | None = None


def to_dict(row: Lore):
    return {
        "id": row.id,
        "project_id": row.project_id,
        "lore_type": row.lore_type,
        "name": row.name,
        "description": row.description,
        "tags": row.tags,
        "related_chapters": row.related_chapters,
        "related_characters": row.related_characters,
        "metadata": row.meta_data,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


@router.get("/projects/{project_id}/lore")
def list_lore(project_id: str):
    db: Session = SessionLocal()
    try:
        items = db.query(Lore).filter(Lore.project_id == project_id).all()
        return [to_dict(x) for x in items]
    finally:
        db.close()


@router.post("/lore/", status_code=201)
def create_lore(payload: LoreIn):
    db: Session = SessionLocal()
    try:
        row = Lore(id=str(uuid.uuid4()), **payload.model_dump())
        db.add(row)
        db.commit()
        db.refresh(row)
        return to_dict(row)
    finally:
        db.close()


@router.get("/lore/{lore_id}")
def get_lore(lore_id: str):
    db: Session = SessionLocal()
    try:
        row = db.query(Lore).filter(Lore.id == lore_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="Not found")
        return to_dict(row)
    finally:
        db.close()


@router.patch("/lore/{lore_id}")
def update_lore(lore_id: str, payload: LoreUpdate):
    db: Session = SessionLocal()
    try:
        row = db.query(Lore).filter(Lore.id == lore_id).first()
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


@router.delete("/lore/{lore_id}", status_code=204)
def delete_lore(lore_id: str):
    db: Session = SessionLocal()
    try:
        row = db.query(Lore).filter(Lore.id == lore_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="Not found")
        db.delete(row)
        db.commit()
        try:
            from services.search import remove_lore
            remove_lore(lore_id)
        except Exception:
            pass
    finally:
        db.close()




