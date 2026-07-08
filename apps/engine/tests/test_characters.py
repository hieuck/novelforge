"""Tests for /api/characters/* endpoints."""

from __future__ import annotations


def _create_project(client):
    return client.post("/api/projects/", json={"title": "Test Novel"}).json()


def test_list_characters_empty(client):
    proj = _create_project(client)
    r = client.get(f"/api/projects/{proj['id']}/characters")
    assert r.status_code == 200
    assert r.json() == []


def test_create_character(client):
    proj = _create_project(client)
    r = client.post("/api/characters/", json={"project_id": proj["id"], "name": "Alice"})
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Alice"
    assert data["project_id"] == proj["id"]
    assert "id" in data


def test_list_characters_after_create(client):
    proj = _create_project(client)
    client.post("/api/characters/", json={"project_id": proj["id"], "name": "Alice"})
    client.post("/api/characters/", json={"project_id": proj["id"], "name": "Bob"})
    r = client.get(f"/api/projects/{proj['id']}/characters")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_get_character(client):
    proj = _create_project(client)
    created = client.post("/api/characters/", json={"project_id": proj["id"], "name": "Alice"}).json()
    r = client.get(f"/api/characters/{created['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == created["id"]


def test_get_character_not_found(client):
    r = client.get("/api/characters/nonexistent-id")
    assert r.status_code == 404


def test_update_character(client):
    proj = _create_project(client)
    created = client.post("/api/characters/", json={"project_id": proj["id"], "name": "Old"}).json()
    r = client.patch(f"/api/characters/{created['id']}", json={"name": "New", "role": "Hero"})
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "New"
    assert data["role"] == "Hero"


def test_delete_character(client):
    proj = _create_project(client)
    created = client.post("/api/characters/", json={"project_id": proj["id"], "name": "ToDelete"}).json()
    r = client.delete(f"/api/characters/{created['id']}")
    assert r.status_code == 204
    r2 = client.get(f"/api/characters/{created['id']}")
    assert r2.status_code == 404
