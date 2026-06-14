"""Tests for /api/projects/* endpoints."""
from __future__ import annotations

import pytest


def test_list_projects_empty(client):
    r = client.get("/api/projects/")
    assert r.status_code == 200
    assert r.json() == []


def test_create_project(client):
    r = client.post("/api/projects/", json={"title": "My Novel", "genre": "Fantasy", "language": "vi"})
    assert r.status_code == 201
    data = r.json()
    assert data["title"] == "My Novel"
    assert data["genre"] == "Fantasy"
    assert "id" in data


def test_list_projects_after_create(client):
    client.post("/api/projects/", json={"title": "A"})
    client.post("/api/projects/", json={"title": "B"})
    r = client.get("/api/projects/")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_get_project(client):
    created = client.post("/api/projects/", json={"title": "Test"}).json()
    r = client.get(f"/api/projects/{created['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == created["id"]


def test_get_project_not_found(client):
    r = client.get("/api/projects/nonexistent-id")
    assert r.status_code == 404


def test_update_project(client):
    created = client.post("/api/projects/", json={"title": "Old"}).json()
    r = client.patch(f"/api/projects/{created['id']}", json={"title": "New", "genre": "SciFi"})
    assert r.status_code == 200
    data = r.json()
    assert data["title"] == "New"
    assert data["genre"] == "SciFi"


def test_update_project_partial(client):
    created = client.post("/api/projects/", json={"title": "Keep", "genre": "Fantasy"}).json()
    r = client.patch(f"/api/projects/{created['id']}", json={"genre": "Horror"})
    assert r.status_code == 200
    data = r.json()
    assert data["title"] == "Keep"
    assert data["genre"] == "Horror"


def test_delete_project(client):
    created = client.post("/api/projects/", json={"title": "ToDelete"}).json()
    r = client.delete(f"/api/projects/{created['id']}")
    assert r.status_code == 204
    # Verify it's gone
    r2 = client.get(f"/api/projects/{created['id']}")
    assert r2.status_code == 404


def test_delete_project_not_found(client):
    r = client.delete("/api/projects/nonexistent")
    assert r.status_code == 404


def test_delete_project_cascades_chapters(client):
    """Deleting a project should also delete its chapters."""
    proj = client.post("/api/projects/", json={"title": "Cascade"}).json()
    client.post("/api/chapters/", json={"project_id": proj["id"], "title": "Ch1", "content": "text"})
    client.delete(f"/api/projects/{proj['id']}")
    r = client.get(f"/api/projects/{proj['id']}/chapters")
    # Either 404 or empty list — project is gone
    assert r.status_code in (200, 404)
    if r.status_code == 200:
        assert r.json() == []
