"""Tests for GET /api/projects/{id}/search/count endpoint."""

from __future__ import annotations


def test_search_count_empty_query(client):
    """Empty query returns count 0."""
    r = client.get("/api/projects/fake/search/count?q=")
    assert r.status_code == 200
    assert r.json()["count"] == 0


def test_search_count_no_results(client):
    """No matches returns count 0."""
    proj = client.post("/api/projects/", json={"title": "Test"}).json()
    r = client.get(f"/api/projects/{proj['id']}/search/count?q=zzzzz")
    assert r.status_code == 200
    assert r.json()["count"] == 0
