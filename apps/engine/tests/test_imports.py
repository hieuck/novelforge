"""Tests for /api/import endpoint."""

from __future__ import annotations


def test_import_single_chapter(client):
    """Import content as a single chapter."""
    proj = client.post("/api/projects/", json={"title": "Test"}).json()
    r = client.post(
        "/api/import",
        json={
            "project_id": proj["id"],
            "content": "Once upon a time...",
            "mode": "single",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["imported"] == 1


def test_import_split_h2(client):
    """Import content split by ## headings into multiple chapters."""
    proj = client.post("/api/projects/", json={"title": "Test"}).json()
    content = """# Title
## Chapter One
Content of first chapter.
## Chapter Two
Content of second chapter.
"""
    r = client.post(
        "/api/import",
        json={
            "project_id": proj["id"],
            "content": content,
            "mode": "split_h2",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["imported"] == 2


def test_import_default_mode(client):
    """Default mode is 'single'."""
    proj = client.post("/api/projects/", json={"title": "Test"}).json()
    r = client.post(
        "/api/import",
        json={
            "project_id": proj["id"],
            "content": "Just text.",
        },
    )
    assert r.status_code == 200


def test_import_empty_content(client):
    """Empty content imports one empty chapter."""
    proj = client.post("/api/projects/", json={"title": "Test"}).json()
    r = client.post(
        "/api/import",
        json={
            "project_id": proj["id"],
            "content": "",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["imported"] == 1
