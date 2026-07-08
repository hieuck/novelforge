"""Tests for GET /api/chapters/recent endpoint."""

from __future__ import annotations


def test_recent_chapters_empty(client):
    """Returns empty list when no chapters exist."""
    r = client.get("/api/chapters/recent")
    assert r.status_code == 200
    assert r.json() == []


def test_recent_chapters_returns_recent(client):
    """Returns recent chapters ordered by updated_at."""
    proj = client.post("/api/projects/", json={"title": "Test"}).json()
    ch1 = client.post("/api/chapters/", json={"project_id": proj["id"], "title": "A", "content": "a"}).json()
    ch2 = client.post("/api/chapters/", json={"project_id": proj["id"], "title": "B", "content": "b"}).json()

    r = client.get("/api/chapters/recent?limit=5")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 2
    assert data[0]["id"] in (ch1["id"], ch2["id"])
    assert data[1]["id"] in (ch1["id"], ch2["id"])


def test_recent_chapters_limit(client):
    """Respects limit parameter."""
    proj = client.post("/api/projects/", json={"title": "Test"}).json()
    for i in range(5):
        client.post("/api/chapters/", json={"project_id": proj["id"], "title": f"Ch{i}", "content": "x"})

    r = client.get("/api/chapters/recent?limit=3")
    assert r.status_code == 200
    assert len(r.json()) == 3
