"""Tests for search type filter (new feature)."""
from __future__ import annotations


def test_search_with_unknown_type(client):
    """Search returns 400 for invalid type filter."""
    proj = client.post("/api/projects/", json={"title": "Test"}).json()
    r = client.get(f"/api/projects/{proj['id']}/search?q=test&type=invalid_type")
    assert r.status_code == 400


def test_search_with_valid_type(client):
    """Search with valid type filter returns 200."""
    proj = client.post("/api/projects/", json={"title": "Test"}).json()
    r = client.get(f"/api/projects/{proj['id']}/search?q=test&type=chapter")
    assert r.status_code == 200
