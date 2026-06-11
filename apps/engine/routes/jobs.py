from fastapi import APIRouter
from db.session import SessionLocal
from models.job import Job

router = APIRouter()

@router.get("/projects/{project_id}/jobs")
async def list_jobs(project_id: str):
    db = SessionLocal()
    try:
        return db.query(Job).filter(Job.project_id == project_id).order_by(Job.created_at.desc()).all()
    finally:
        db.close()
