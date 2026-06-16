"""Tests for POST /api/chapters/{id}/move endpoint."""
from __future__ import annotations


def _make_project(client):
    return client.post("/api/projects/", json={"title": "Test"}).json()


def test_move_chapter_to_position(client):
    """Moving chapter updates its scene_order."""
    proj = _make_project(client)
    ch1 = client.post("/api/chapters/", json={"project_id": proj["id"], "title": "A", "scene_order": 0}).json()
    ch2 = client.post("/api/chapters/", json={"project_id": proj["id"], "title": "B", "scene_order": 1}).json()
    ch3 = client.post("/api/chapters/", json={"project_id": proj["id"], "title": "C", "scene_order": 2}).json()

    # Move ch3 (last) to position 0 (first)
    r = client.post(f"/api/chapters/{ch3['id']}/move?position=0")
    assert r.status_code == 200

    chapters = client.get(f"/api/projects/{proj['id']}/chapters").json()
    assert chapters[0]["id"] == ch3["id"]
    assert chapters[0]["scene_order"] == 0
    assert chapters[1]["id"] == ch1["id"]
    assert chapters[1]["scene_order"] == 1
    assert chapters[2]["id"] == ch2["id"]
    assert chapters[2]["scene_order"] == 2


def test_move_chapter_invalid_position(client):
    """Returns 400 for out-of-bounds position."""
    proj = _make_project(client)
    ch = client.post("/api/chapters/", json={"project_id": proj["id"], "title": "A", "scene_order": 0}).json()
    r = client.post(f"/api/chapters/{ch['id']}/move?position=999")
    assert r.status_code == 400


def test_move_chapter_not_found(client):
    """Returns 404 for non-existent chapter."""
    r = client.post("/api/chapters/nonexistent/move?position=0")
    assert r.status_code == 404
