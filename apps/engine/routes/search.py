from __future__ import annotations

from fastapi import APIRouter, HTTPException
from services.search import search_project

_VALID_TYPES = {"chapter", "character", "lore"}

router = APIRouter()


@router.get("/projects/{project_id}/search")
def search(project_id: str, q: str, limit: int = 20, type: str | None = None) -> list[dict]:
    """Full-text search across chapters, lore, and characters for a project."""
    if type and type not in _VALID_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid type '{type}'. Valid: {', '.join(sorted(_VALID_TYPES))}",
        )
    if not q or not q.strip():
        return []
    results = search_project(project_id, q.strip(), limit=min(limit, 50))
    if type:
        results = [r for r in results if r.get("kind") == type]
    return results


@router.get("/projects/{project_id}/search/count")
def search_count(project_id: str, q: str, type: str | None = None) -> dict:
    """Return count of search results without returning the results."""
    if type and type not in _VALID_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid type '{type}'. Valid: {', '.join(sorted(_VALID_TYPES))}",
        )
    if not q or not q.strip():
        return {"count": 0}
    results = search_project(project_id, q.strip(), limit=1000)
    if type:
        results = [r for r in results if r.get("kind") == type]
    return {"count": len(results)}
