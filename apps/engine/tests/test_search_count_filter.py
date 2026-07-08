"""Tests for search count with type filter."""

from __future__ import annotations


def test_search_count_with_type(client):
    """Search count respects type filter."""
    proj = client.post("/api/projects/", json={"title": "Test"}).json()
    r = client.get(f"/api/projects/{proj['id']}/search/count?q=test&type=chapter")
    assert r.status_code == 200
    assert "count" in r.json()


def test_search_count_invalid_type(client):
    """Search count returns 400 for invalid type."""
    proj = client.post("/api/projects/", json={"title": "Test"}).json()
    r = client.get(f"/api/projects/{proj['id']}/search/count?q=test&type=invalid")
    assert r.status_code == 400
