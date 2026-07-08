"""Tests for /api/chapters/* endpoints."""

from __future__ import annotations


def _create_project(client):
    return client.post("/api/projects/", json={"title": "Test Novel"}).json()


def test_list_chapters_empty(client):
    proj = _create_project(client)
    r = client.get(f"/api/projects/{proj['id']}/chapters")
    assert r.status_code == 200
    assert r.json() == []


def test_create_chapter(client):
    proj = _create_project(client)
    r = client.post("/api/chapters/", json={"project_id": proj["id"], "title": "Ch1", "content": "Hello"})
    assert r.status_code == 201
    data = r.json()
    assert data["title"] == "Ch1"
    assert data["project_id"] == proj["id"]
    assert data["content"] == "Hello"
    assert "id" in data


def test_list_chapters_after_create(client):
    proj = _create_project(client)
    client.post("/api/chapters/", json={"project_id": proj["id"], "title": "Ch1"})
    client.post("/api/chapters/", json={"project_id": proj["id"], "title": "Ch2"})
    r = client.get(f"/api/projects/{proj['id']}/chapters")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_get_chapter(client):
    proj = _create_project(client)
    created = client.post("/api/chapters/", json={"project_id": proj["id"], "title": "Ch1"}).json()
    r = client.get(f"/api/chapters/{created['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == created["id"]


def test_get_chapter_not_found(client):
    r = client.get("/api/chapters/nonexistent-id")
    assert r.status_code == 404


def test_update_chapter(client):
    proj = _create_project(client)
    created = client.post(
        "/api/chapters/", json={"project_id": proj["id"], "title": "Old", "content": "Old text"}
    ).json()
    r = client.patch(f"/api/chapters/{created['id']}", json={"title": "New", "content": "New text"})
    assert r.status_code == 200
    data = r.json()
    assert data["title"] == "New"
    assert data["content"] == "New text"


def test_delete_chapter(client):
    proj = _create_project(client)
    created = client.post("/api/chapters/", json={"project_id": proj["id"], "title": "ToDelete"}).json()
    r = client.delete(f"/api/chapters/{created['id']}")
    assert r.status_code == 204
    r2 = client.get(f"/api/chapters/{created['id']}")
    assert r2.status_code == 404


def test_chapter_word_count_on_create(client):
    """word_count is auto-calculated on create."""
    proj = _create_project(client)
    r = client.post(
        "/api/chapters/", json={"project_id": proj["id"], "title": "WC", "content": "one two three four five"}
    )
    assert r.status_code == 201
    assert r.json()["word_count"] == 5


def test_chapter_word_count_on_update(client):
    """word_count is recalculated when content changes."""
    proj = _create_project(client)
    created = client.post("/api/chapters/", json={"project_id": proj["id"], "title": "WC", "content": "one two"}).json()
    assert created["word_count"] == 2
    r = client.patch(f"/api/chapters/{created['id']}", json={"content": "a b c d e f g h"})
    assert r.status_code == 200
    assert r.json()["word_count"] == 8


def test_chapter_reorder(client):
    """POST /chapters/reorder sets scene_order."""
    proj = _create_project(client)
    ch1 = client.post("/api/chapters/", json={"project_id": proj["id"], "title": "A", "scene_order": 0}).json()
    ch2 = client.post("/api/chapters/", json={"project_id": proj["id"], "title": "B", "scene_order": 1}).json()
    ch3 = client.post("/api/chapters/", json={"project_id": proj["id"], "title": "C", "scene_order": 2}).json()

    # Reorder: reverse
    r = client.post("/api/chapters/reorder", json={"ordered_ids": [ch3["id"], ch2["id"], ch1["id"]]})
    assert r.status_code == 200
    assert r.json()["count"] == 3

    chs = client.get(f"/api/projects/{proj['id']}/chapters").json()
    assert len(chs) == 3
    # Should now be C, B, A
    assert chs[0]["id"] == ch3["id"]
    assert chs[1]["id"] == ch2["id"]
    assert chs[2]["id"] == ch1["id"]
