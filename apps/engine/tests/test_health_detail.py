"""Tests for GET /api/health/db endpoint."""
from __future__ import annotations


def test_health_db_returns_size(client):
    """Returns DB health info including file size and table counts."""
    r = client.get("/api/health/db")
    assert r.status_code == 200
    data = r.json()
    assert "size_bytes" in data
    assert "tables" in data
    assert isinstance(data["tables"], int)
    assert data["tables"] > 0
    assert data["status"] == "ok"


def test_health_db_after_creating_data(client):
    """Table count increases after creating tables."""
    r1 = client.get("/api/health/db")
    assert r1.status_code == 200
    assert r1.json()["tables"] >= 8  # projects, chapters, characters, lore, timeline, images, jobs, settings, etc.
