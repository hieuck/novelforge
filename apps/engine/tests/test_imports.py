"""Tests for /api/import endpoint."""
from __future__ import annotations


def test_import_single_markdown(client):
    proj = client.post("/api/projects/", json={"title": "Import Test"}).json()
    content = "# Chapter 1\n\nHello world.\n\n## Chapter 2\n\nMore text."
    r = client.post("/api/import", json={
        "project_id": proj["id"],
        "content": content,
        "filename": "test.md",
        "mode": "single",
    })
    assert r.status_code == 200
    data = r.json()
    assert data.get("imported", 0) >= 1


def test_import_heading_mode(client):
    proj = client.post("/api/projects/", json={"title": "Import Heading"}).json()
    content = "## Chapter 1\n\nText.\n\n## Chapter 2\n\nMore."
    r = client.post("/api/import", json={
        "project_id": proj["id"],
        "content": content,
        "filename": "book.md",
        "mode": "split_h2",
    })
    assert r.status_code == 200
    data = r.json()
    assert data.get("imported", 0) >= 1


def test_import_no_project(client):
    r = client.post("/api/import", json={
        "project_id": "nonexistent",
        "content": "Test",
        "filename": "test.md",
    })
    assert r.status_code == 404
