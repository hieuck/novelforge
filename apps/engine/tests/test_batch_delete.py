"""Tests for POST /api/chapters/batch-delete endpoint."""
from __future__ import annotations


def _make_project(client):
    return client.post("/api/projects/", json={"title": "Test"}).json()


def test_batch_delete_chapters(client):
    """Batch delete removes multiple chapters."""
    proj = _make_project(client)
    ch1 = client.post("/api/chapters/", json={"project_id": proj["id"], "title": "A"}).json()
    ch2 = client.post("/api/chapters/", json={"project_id": proj["id"], "title": "B"}).json()
    ch3 = client.post("/api/chapters/", json={"project_id": proj["id"], "title": "C"}).json()

    r = client.post("/api/chapters/batch-delete", json={"ids": [ch1["id"], ch3["id"]]})
    assert r.status_code == 200
    data = r.json()
    assert data["deleted"] == 2

    remaining = client.get(f"/api/projects/{proj['id']}/chapters").json()
    assert len(remaining) == 1
    assert remaining[0]["id"] == ch2["id"]


def test_batch_delete_empty_list(client):
    """Empty list returns 0 deleted."""
    r = client.post("/api/chapters/batch-delete", json={"ids": []})
    assert r.status_code == 200
    assert r.json()["deleted"] == 0
