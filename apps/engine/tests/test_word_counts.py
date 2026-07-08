"""Tests for GET /api/projects/{id}/word-counts endpoint."""

from __future__ import annotations


def test_word_counts_empty(client):
    """Returns empty list for project with no chapters."""
    proj = client.post("/api/projects/", json={"title": "Empty"}).json()
    r = client.get(f"/api/projects/{proj['id']}/word-counts")
    assert r.status_code == 200
    assert r.json() == []


def test_word_counts_with_chapters(client):
    """Returns word count for each chapter ordered by scene_order."""
    proj = client.post("/api/projects/", json={"title": "Test"}).json()
    client.post(
        "/api/chapters/",
        json={
            "project_id": proj["id"],
            "title": "Ch1",
            "content": "one two three",
            "scene_order": 0,
        },
    )
    client.post(
        "/api/chapters/",
        json={
            "project_id": proj["id"],
            "title": "Ch2",
            "content": "four five",
            "scene_order": 1,
        },
    )

    r = client.get(f"/api/projects/{proj['id']}/word-counts")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2
    assert data[0]["title"] == "Ch1"
    assert data[0]["word_count"] == 3
    assert data[1]["title"] == "Ch2"
    assert data[1]["word_count"] == 2
    assert data[0]["scene_order"] == 0
    assert data[1]["scene_order"] == 1


def test_word_counts_not_found(client):
    """Returns 404 for non-existent project."""
    r = client.get("/api/projects/nonexistent/word-counts")
    assert r.status_code == 404
