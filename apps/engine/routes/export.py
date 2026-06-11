from fastapi import APIRouter
from pydantic import BaseModel
router = APIRouter()

class ProjectExportIn(BaseModel):
    project_id: str
    fmt: str = "md"

@router.post("/export")
async def export_project(payload: ProjectExportIn):
    return {"format": payload.fmt, "content": "", "filename": f"{payload.project_id}.{payload.fmt}"}
