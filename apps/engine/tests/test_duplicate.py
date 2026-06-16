"""Tests for POST /api/chapters/{id}/duplicate."""
from __future__ import annotations


def test_duplicate_chapter(client):
    """Duplicating a chapter creates a copy with same content."""
    proj = client.post("/api/projects/", json={"title": "Test"}).json()
    ch = client.post("/api/chapters/", json={
        "project_id": proj["id"], "title": "Original",
        "content": "Some content here.", "scene_order": 5,
    }).json()

    r = client.post(f"/api/chapters/{ch['id']}/duplicate")
    assert r.status_code == 201
    data = r.json()
    assert data["title"] == "Original (Copy)"
    assert data["content"] == "Some content here."
    assert data["project_id"] == proj["id"]
    assert data["id"] != ch["id"]


def test_duplicate_chapter_not_found(client):
    """Returns 404 for non-existent chapter."""
    r = client.post("/api/chapters/nonexistent/duplicate")
    assert r.status_code == 404
