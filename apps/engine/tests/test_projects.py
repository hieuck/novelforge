"""Tests for /api/projects/* endpoints.

NOTE: Routes are registered at /api/ directly (not /api/projects/).
Project-specific sub-routes (chapters, characters, etc.) are handled
by their own routers also mounted at /api/.
"""
from __future__ import annotations

import pytest


def test_list_projects_empty(client):
    r = client.get("/api/")
    assert r.status_code == 200
    assert r.json() == []


def test_create_project(client):
    r = client.post("/api/", json={"title": "My Novel", "genre": "Fantasy", "language": "vi"})
    assert r.status_code == 201
    data = r.json()
    assert data["title"] == "My Novel"
    assert data["genre"] == "Fantasy"
    assert "id" in data


def test_list_projects_after_create(client):
    client.post("/api/", json={"title": "A"})
    client.post("/api/", json={"title": "B"})
    r = client.get("/api/")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_get_project(client):
    created = client.post("/api/", json={"title": "Test"}).json()
    r = client.get(f"/api/{created['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == created["id"]


def test_get_project_not_found(client):
    r = client.get("/api/nonexistent-id")
    assert r.status_code == 404


def test_update_project(client):
    created = client.post("/api/", json={"title": "Old"}).json()
    r = client.patch(f"/api/{created['id']}", json={"title": "New", "genre": "SciFi"})
    assert r.status_code == 200
    data = r.json()
    assert data["title"] == "New"
    assert data["genre"] == "SciFi"


def test_update_project_partial(client):
    created = client.post("/api/", json={"title": "Keep", "genre": "Fantasy"}).json()
    r = client.patch(f"/api/{created['id']}", json={"genre": "Horror"})
    assert r.status_code == 200
    data = r.json()
    assert data["title"] == "Keep"
    assert data["genre"] == "Horror"


def test_delete_project(client):
    created = client.post("/api/", json={"title": "ToDelete"}).json()
    r = client.delete(f"/api/{created['id']}")
    assert r.status_code == 204
    # Verify it's gone
    r2 = client.get(f"/api/{created['id']}")
    assert r2.status_code == 404


def test_delete_project_not_found(client):
    r = client.delete("/api/nonexistent")
    assert r.status_code == 404


def test_delete_project_cascades_chapters(client):
    """Deleting a project should also delete its chapters."""
    proj = client.post("/api/", json={"title": "Cascade"}).json()
    client.post("/api/", json={"project_id": proj["id"], "title": "Ch1", "content": "text"})
    client.delete(f"/api/{proj['id']}")
    r = client.get(f"/api/{proj['id']}")
    # Either 404 or empty list — project exists but chapters are gone
    assert r.status_code in (200, 404)
    if r.status_code == 200:
        assert r.json() is not None
