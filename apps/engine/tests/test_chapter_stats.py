"""Tests for GET /api/chapters/{id}/stats endpoint."""
from __future__ import annotations


def test_chapter_stats(client):
    """Returns detailed stats for a chapter."""
    proj = client.post("/api/projects/", json={"title": "Test"}).json()
    ch = client.post("/api/chapters/", json={
        "project_id": proj["id"],
        "title": "Ch1",
        "content": "Hello world. This is a test.\n\nSecond paragraph here!",
    }).json()

    r = client.get(f"/api/chapters/{ch['id']}/stats")
    assert r.status_code == 200
    data = r.json()
    assert data["word_count"] == 9
    assert data["char_count"] == 52
    assert data["sentence_count"] == 3
    assert data["paragraph_count"] == 2


def test_chapter_stats_empty(client):
    """Returns zero stats for empty chapter."""
    proj = client.post("/api/projects/", json={"title": "Test"}).json()
    ch = client.post("/api/chapters/", json={
        "project_id": proj["id"],
        "title": "Empty",
        "content": "",
    }).json()

    r = client.get(f"/api/chapters/{ch['id']}/stats")
    assert r.status_code == 200
    data = r.json()
    assert data["word_count"] == 0
    assert data["char_count"] == 0


def test_chapter_stats_not_found(client):
    """Returns 404 for non-existent chapter."""
    r = client.get("/api/chapters/nonexistent/stats")
    assert r.status_code == 404
