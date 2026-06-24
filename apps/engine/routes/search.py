from __future__ import annotations

from fastapi import APIRouter
from services.search import search_project

router = APIRouter()


@router.get("/projects/{project_id}/search")
def search(project_id: str, q: str, limit: int = 20) -> list[dict]:
    """Full-text search across chapters, lore, and characters for a project."""
    if not q or not q.strip():
        return []
    return search_project(project_id, q.strip(), limit=min(limit, 50))


@router.get("/projects/{project_id}/search/count")
def search_count(project_id: str, q: str) -> dict:
    """Return count of search results without returning the results."""
    if not q or not q.strip():
        return {"count": 0}
    results = search_project(project_id, q.strip(), limit=1000)
    return {"count": len(results)}
