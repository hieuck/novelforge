from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from db.session import SessionLocal
from models.project import Project
import uuid
from datetime import datetime


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


def to_dict(p: Project):
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
def list_projects():
    db: Session = SessionLocal()
    try:
        items = db.query(Project).order_by(Project.updated_at.desc()).all()
        return [to_dict(p) for p in items]
    finally:
        db.close()


@router.post("/")
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


@router.get("/{project_id}")
def get_project(project_id: str):
    db: Session = SessionLocal()
    try:
        p = db.query(Project).filter(Project.id == project_id).first()
        if not p:
            raise HTTPException(status_code=404, detail="Not found")
        return to_dict(p)
    finally:
        db.close()


@router.patch("/{project_id}")
def update_project(project_id: str, payload: ProjectUpdate):
    db: Session = SessionLocal()
    try:
        p = db.query(Project).filter(Project.id == project_id).first()
        if not p:
            raise HTTPException(status_code=404, detail="Not found")
        data = payload.model_dump(exclude_unset=True)
        for k, v in data.items():
            setattr(p, k, v)
        p.updated_at = datetime.utcnow()
        db.add(p)
        db.commit()
        db.refresh(p)
        return to_dict(p)
    finally:
        db.close()
