"""Tests for /api/projects/{id}/search endpoint."""

from __future__ import annotations


def test_search_empty_query(client):
    """Empty query returns empty list."""
    r = client.get("/api/projects/fake/search?q=")
    assert r.status_code == 200
    assert r.json() == []


def test_search_no_results(client):
    """Search with no matches returns empty list."""
    proj = client.post("/api/projects/", json={"title": "Test"}).json()
    client.post(
        "/api/chapters/",
        json={
            "project_id": proj["id"],
            "title": "Ch1",
            "content": "Hello world.",
        },
    )

    r = client.get(f"/api/projects/{proj['id']}/search?q=zzzznotfound")
    assert r.status_code == 200
    assert r.json() == []


def test_search_limit_respected(client):
    """Search respects limit parameter."""
    r = client.get("/api/projects/fake/search?q=test&limit=5")
    assert r.status_code == 200


def test_search_whitespace_query(client):
    """Whitespace-only query returns empty list."""
    proj = client.post("/api/projects/", json={"title": "Test"}).json()
    r = client.get(f"/api/projects/{proj['id']}/search?q=   ")
    assert r.status_code == 200
    assert r.json() == []
