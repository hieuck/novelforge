from __future__ import annotations


def _create_project(client):
    r = client.post("/api/projects/", json={"title": "Export Test"})
    assert r.status_code == 201
    return r.json()["id"]


def test_export_no_project(client):
    r = client.post("/api/export", json={"project_id": "nonexistent", "fmt": "md"})
    assert r.status_code == 404


def test_export_markdown(client):
    pid = _create_project(client)
    r = client.post("/api/export", json={"project_id": pid, "fmt": "md"})
    assert r.status_code == 200


def test_export_html(client):
    pid = _create_project(client)
    r = client.post("/api/export", json={"project_id": pid, "fmt": "html"})
    assert r.status_code == 200


def test_import_markdown(client):
    pid = _create_project(client)
    content = "## Chapter 1\n\nHello world."
    r = client.post("/api/import", json={"project_id": pid, "content": content, "filename": "test.md", "mode": "single"})
    assert r.status_code == 200
