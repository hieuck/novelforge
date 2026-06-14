"""Tests for /api/lore/* endpoints."""
from __future__ import annotations


def _create_project(client):
    return client.post("/api/projects/", json={"title": "Test Novel"}).json()


def test_list_lore_empty(client):
    proj = _create_project(client)
    r = client.get(f"/api/projects/{proj['id']}/lore")
    assert r.status_code == 200
    assert r.json() == []


def test_create_lore(client):
    proj = _create_project(client)
    r = client.post("/api/lore/", json={"project_id": proj["id"], "lore_type": "location", "name": "Test Location"})
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Test Location"
    assert data["lore_type"] == "location"
    assert data["project_id"] == proj["id"]
    assert "id" in data


def test_list_lore_after_create(client):
    proj = _create_project(client)
    client.post("/api/lore/", json={"project_id": proj["id"], "lore_type": "location", "name": "Forest"})
    client.post("/api/lore/", json={"project_id": proj["id"], "lore_type": "character", "name": "Village"})
    r = client.get(f"/api/projects/{proj['id']}/lore")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_get_lore(client):
    proj = _create_project(client)
    created = client.post("/api/lore/", json={"project_id": proj["id"], "lore_type": "location", "name": "Castle"}).json()
    r = client.get(f"/api/lore/{created['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == created["id"]


def test_get_lore_not_found(client):
    r = client.get("/api/lore/nonexistent-id")
    assert r.status_code == 404


def test_update_lore(client):
    proj = _create_project(client)
    created = client.post("/api/lore/", json={"project_id": proj["id"], "lore_type": "location", "name": "Old"}).json()
    r = client.patch(f"/api/lore/{created['id']}", json={"name": "New", "lore_type": "region"})
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "New"
    assert data["lore_type"] == "region"


def test_delete_lore(client):
    proj = _create_project(client)
    created = client.post("/api/lore/", json={"project_id": proj["id"], "lore_type": "location", "name": "ToDelete"}).json()
    r = client.delete(f"/api/lore/{created['id']}")
    assert r.status_code == 204
    r2 = client.get(f"/api/lore/{created['id']}")
    assert r2.status_code == 404
