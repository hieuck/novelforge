"""Tests for /api/timeline/* endpoints."""
from __future__ import annotations


def _create_project(client):
    return client.post("/api/projects/", json={"title": "Test Novel"}).json()


def test_list_timeline_empty(client):
    proj = _create_project(client)
    r = client.get(f"/api/projects/{proj['id']}/timeline")
    assert r.status_code == 200
    assert r.json() == []


def test_create_timeline_event(client):
    proj = _create_project(client)
    r = client.post("/api/timeline/", json={"project_id": proj["id"], "title": "Test Event"})
    assert r.status_code == 201
    data = r.json()
    assert data["title"] == "Test Event"
    assert data["project_id"] == proj["id"]
    assert "id" in data


def test_list_timeline_after_create(client):
    proj = _create_project(client)
    client.post("/api/timeline/", json={"project_id": proj["id"], "title": "Event A"})
    client.post("/api/timeline/", json={"project_id": proj["id"], "title": "Event B"})
    r = client.get(f"/api/projects/{proj['id']}/timeline")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_get_timeline_event(client):
    proj = _create_project(client)
    created = client.post("/api/timeline/", json={"project_id": proj["id"], "title": "Event"}).json()
    r = client.get(f"/api/timeline/{created['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == created["id"]


def test_get_timeline_event_not_found(client):
    r = client.get("/api/timeline/nonexistent-id")
    assert r.status_code == 404


def test_update_timeline_event(client):
    proj = _create_project(client)
    created = client.post("/api/timeline/", json={"project_id": proj["id"], "title": "Old Title"}).json()
    r = client.patch(f"/api/timeline/{created['id']}", json={"title": "New Title", "description": "Updated desc"})
    assert r.status_code == 200
    data = r.json()
    assert data["title"] == "New Title"
    assert data["description"] == "Updated desc"


def test_delete_timeline_event(client):
    proj = _create_project(client)
    created = client.post("/api/timeline/", json={"project_id": proj["id"], "title": "ToDelete"}).json()
    r = client.delete(f"/api/timeline/{created['id']}")
    assert r.status_code == 204
    r2 = client.get(f"/api/timeline/{created['id']}")
    assert r2.status_code == 404
