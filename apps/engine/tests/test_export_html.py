"""Tests for HTML export of single chapter (new feature)."""
from __future__ import annotations


def test_export_single_chapter_html(client):
    """Export a single chapter as HTML (new feature)."""
    proj = client.post("/api/projects/", json={"title": "Test"}).json()
    ch = client.post("/api/chapters/", json={
        "project_id": proj["id"], "title": "Ch1", "content": "Hello <world>.",
    }).json()

    r = client.get(f"/api/chapters/{ch['id']}/export?format=html")
    assert r.status_code == 200
    assert r.headers["content-type"] == "text/html; charset=utf-8"
    assert "<h1>" in r.text or "<h2>" in r.text, "HTML export should wrap title in heading tags"
    assert "Hello" in r.text


def test_export_project_html(client):
    """Export entire project as HTML (existing feature)."""
    proj = client.post("/api/projects/", json={"title": "Test"}).json()
    client.post("/api/chapters/", json={
        "project_id": proj["id"], "title": "Ch1", "content": "Content.",
    })

    r = client.post("/api/export", json={"project_id": proj["id"], "fmt": "html"})
    assert r.status_code == 200
    assert r.headers["content-type"] == "text/html; charset=utf-8"
