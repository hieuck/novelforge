from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from db.session import SessionLocal
from models.extra import Character
import uuid
from datetime import datetime, timezone


router = APIRouter()


class CharacterIn(BaseModel):
    project_id: str | None = None
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


def to_dict(c: Character):
    return {
        "id": c.id,
        "project_id": c.project_id,
        "name": c.name,
        "alias": c.alias,
        "role": c.role,
        "age": c.age,
        "personality": c.personality,
        "appearance": c.appearance,
        "goals": c.goals,
        "secrets": c.secrets,
        "relationships": c.relationships,
        "first_appearance": c.first_appearance,
        "notes": c.notes,
        "summary": c.summary,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }


@router.get("/projects/{project_id}/characters")
def list_characters(project_id: str):
    db: Session = SessionLocal()
    try:
        items = db.query(Character).filter(Character.project_id == project_id).all()
        return [to_dict(c) for c in items]
    finally:
        db.close()


@router.post("/characters/", status_code=201)
def create_character(payload: CharacterIn):
    db: Session = SessionLocal()
    try:
        c = Character(id=str(uuid.uuid4()), **payload.model_dump())
        db.add(c)
        db.commit()
        db.refresh(c)
        return to_dict(c)
    finally:
        db.close()


@router.get("/characters/{character_id}")
def get_character(character_id: str):
    db: Session = SessionLocal()
    try:
        c = db.query(Character).filter(Character.id == character_id).first()
        if not c:
            raise HTTPException(status_code=404, detail="Not found")
        return to_dict(c)
    finally:
        db.close()


@router.patch("/characters/{character_id}")
def update_character(character_id: str, payload: CharacterUpdate):
    db: Session = SessionLocal()
    try:
        c = db.query(Character).filter(Character.id == character_id).first()
        if not c:
            raise HTTPException(status_code=404, detail="Not found")
        data = payload.model_dump(exclude_unset=True)
        for k, v in data.items():
            setattr(c, k, v)
        c.updated_at = datetime.now(timezone.utc)
        db.add(c)
        db.commit()
        db.refresh(c)
        return to_dict(c)
    finally:
        db.close()


@router.delete("/characters/{character_id}", status_code=204)
def delete_character(character_id: str):
    db: Session = SessionLocal()
    try:
        c = db.query(Character).filter(Character.id == character_id).first()
        if not c:
            raise HTTPException(status_code=404, detail="Not found")
        db.delete(c)
        db.commit()
        try:
            from services.search import remove_character
            remove_character(character_id)
        except Exception:
            pass
    finally:
        db.close()



