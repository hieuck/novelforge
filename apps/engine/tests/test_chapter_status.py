"""Tests for GET /api/projects/{id}/chapter-status-counts."""

from __future__ import annotations


def test_status_counts_empty(client):
    """Returns zero for all statuses when no chapters exist."""
    proj = client.post("/api/projects/", json={"title": "Empty"}).json()
    r = client.get(f"/api/projects/{proj['id']}/chapter-status-counts")
    assert r.status_code == 200
    data = r.json()
    assert data["draft"] == 0
    assert data["revised"] == 0
    assert data["final"] == 0
    assert data["total"] == 0


def test_status_counts_with_data(client):
    """Returns correct counts per status."""
    proj = client.post("/api/projects/", json={"title": "Test"}).json()
    client.post("/api/chapters/", json={"project_id": proj["id"], "title": "C1", "status": "draft"})
    client.post("/api/chapters/", json={"project_id": proj["id"], "title": "C2", "status": "revised"})
    client.post("/api/chapters/", json={"project_id": proj["id"], "title": "C3", "status": "draft"})
    client.post("/api/chapters/", json={"project_id": proj["id"], "title": "C4", "status": "final"})

    r = client.get(f"/api/projects/{proj['id']}/chapter-status-counts")
    assert r.status_code == 200
    data = r.json()
    assert data["draft"] == 2
    assert data["revised"] == 1
    assert data["final"] == 1
    assert data["total"] == 4


def test_status_counts_not_found(client):
    """Returns 404 for non-existent project."""
    r = client.get("/api/projects/nonexistent/chapter-status-counts")
    assert r.status_code == 404
