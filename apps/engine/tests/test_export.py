"""Tests for /api/chapters/{id}/export endpoint."""

from __future__ import annotations


def _make_project(client):
    return client.post("/api/projects/", json={"title": "Test"}).json()


def test_export_single_chapter_txt(client):
    """Export a single chapter as plain text."""
    proj = _make_project(client)
    ch = client.post(
        "/api/chapters/",
        json={
            "project_id": proj["id"],
            "title": "Ch1",
            "content": "Hello world.",
        },
    ).json()

    r = client.get(f"/api/chapters/{ch['id']}/export?format=txt")
    assert r.status_code == 200
    assert r.headers["content-type"] == "text/plain; charset=utf-8"
    assert "Ch1" in r.text
    assert "Hello world." in r.text


def test_export_single_chapter_md(client):
    """Export a single chapter as markdown."""
    proj = _make_project(client)
    ch = client.post(
        "/api/chapters/",
        json={
            "project_id": proj["id"],
            "title": "Chapter One",
            "content": "Some **bold** text.",
        },
    ).json()

    r = client.get(f"/api/chapters/{ch['id']}/export?format=md")
    assert r.status_code == 200
    assert r.headers["content-type"] == "text/markdown; charset=utf-8"
    assert "# Chapter One" in r.text
    assert "**bold**" in r.text


def test_export_single_chapter_not_found(client):
    """Returns 404 for non-existent chapter."""
    r = client.get("/api/chapters/nonexistent/export?format=txt")
    assert r.status_code == 404


def test_export_single_chapter_json(client):
    """Export a single chapter as JSON (not yet implemented)."""
    proj = _make_project(client)
    ch = client.post(
        "/api/chapters/",
        json={
            "project_id": proj["id"],
            "title": "Ch1",
            "content": "Hello.",
        },
    ).json()

    r = client.get(f"/api/chapters/{ch['id']}/export?format=json")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/json"
    data = r.json()
    assert data["title"] == "Ch1"
    assert data["content"] == "Hello."
    assert data["word_count"] == 1


def test_export_project_json(client):
    """Export entire project as JSON (not yet implemented)."""
    proj = _make_project(client)
    client.post(
        "/api/chapters/",
        json={
            "project_id": proj["id"],
            "title": "Ch1",
            "content": "A B C",
        },
    )

    r = client.post("/api/export", json={"project_id": proj["id"], "fmt": "json"})
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/json"
    data = r.json()
    assert data["title"] == proj["title"]
    assert len(data["chapters"]) == 1
    assert data["chapters"][0]["title"] == "Ch1"
