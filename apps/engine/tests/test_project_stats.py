"""Tests for GET /api/projects/{id}/stats endpoint."""

from __future__ import annotations


def test_project_stats_empty(client):
    """Returns zero counts for a project with no chapters."""
    proj = client.post("/api/projects/", json={"title": "Empty"}).json()
    r = client.get(f"/api/projects/{proj['id']}/stats")
    assert r.status_code == 200
    data = r.json()
    assert data["chapters"] == 0
    assert data["words"] == 0
    assert data["characters"] == 0
    assert data["images"] == 0
    assert data["lore"] == 0
    assert data["timeline"] == 0


def test_project_stats_with_data(client):
    """Returns correct counts for a project with entities."""
    proj = client.post("/api/projects/", json={"title": "Full"}).json()
    client.post(
        "/api/chapters/",
        json={
            "project_id": proj["id"],
            "title": "Ch1",
            "content": "one two",
        },
    )
    client.post(
        "/api/chapters/",
        json={
            "project_id": proj["id"],
            "title": "Ch2",
            "content": "three four five",
        },
    )
    client.post(
        "/api/characters/",
        json={
            "project_id": proj["id"],
            "name": "Hero",
        },
    )
    client.post(
        "/api/lore/",
        json={
            "project_id": proj["id"],
            "lore_type": "location",
            "name": "World",
        },
    )

    r = client.get(f"/api/projects/{proj['id']}/stats")
    assert r.status_code == 200
    data = r.json()
    assert data["chapters"] == 2
    assert data["words"] == 5  # 2 + 3
    assert data["characters"] == 1
    assert data["lore"] == 1


def test_project_stats_not_found(client):
    """Returns 404 for non-existent project."""
    r = client.get("/api/projects/nonexistent/stats")
    assert r.status_code == 404
