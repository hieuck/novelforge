"""Tests for export with various formats."""
from __future__ import annotations


def _create_project_with_chapter(client):
    r = client.post("/api/projects/", json={"title": "Export Format Test"})
    pid = r.json()["id"]
    client.post("/api/chapters/", json={
        "project_id": pid, "title": "Ch1", "content": "Hello world."
    })
    return pid


def test_export_markdown(client):
    pid = _create_project_with_chapter(client)
    r = client.post("/api/export", json={"project_id": pid, "fmt": "md"})
    assert r.status_code == 200


def test_export_html(client):
    pid = _create_project_with_chapter(client)
    r = client.post("/api/export", json={"project_id": pid, "fmt": "html"})
    assert r.status_code == 200


def test_export_plaintext(client):
    pid = _create_project_with_chapter(client)
    r = client.post("/api/export", json={"project_id": pid, "fmt": "txt"})
    assert r.status_code == 200


def test_export_zip(client):
    pid = _create_project_with_chapter(client)
    r = client.post("/api/export", json={"project_id": pid, "fmt": "zip"})
    assert r.status_code == 200


def test_export_invalid_format(client):
    pid = _create_project_with_chapter(client)
    r = client.post("/api/export", json={"project_id": pid, "fmt": "invalid"})
    assert r.status_code in (400, 422)


def test_export_no_project(client):
    r = client.post("/api/export", json={"project_id": "nonexistent", "fmt": "md"})
    assert r.status_code == 404
