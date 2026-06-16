"""Tests for GET /api/stats/dashboard."""
from __future__ import annotations


def test_stats_dashboard_empty(client):
    """Returns zero counts when there are no projects."""
    r = client.get("/api/stats/dashboard")
    assert r.status_code == 200
    data = r.json()
    assert data["total_projects"] == 0
    assert data["total_chapters"] == 0
    assert data["total_characters"] == 0
    assert data["total_words"] == 0
    assert data["total_images"] == 0
    assert data["total_lore"] == 0
    assert data["total_timeline"] == 0


def test_stats_dashboard_with_data(client):
    """Returns correct counts after creating projects and entities."""
    proj = client.post("/api/projects/", json={"title": "Test"}).json()
    client.post("/api/chapters/", json={
        "project_id": proj["id"], "title": "Ch1",
        "content": "one two three",
    })
    client.post("/api/chapters/", json={
        "project_id": proj["id"], "title": "Ch2",
        "content": "four five",
    })
    client.post("/api/characters/", json={
        "project_id": proj["id"], "name": "Hero",
    })
    client.post("/api/lore/", json={
        "project_id": proj["id"], "lore_type": "location", "name": "Eldoria",
    })
    client.post("/api/timeline/", json={
        "project_id": proj["id"], "title": "Great War",
    })

    r = client.get("/api/stats/dashboard")
    assert r.status_code == 200
    data = r.json()
    assert data["total_projects"] == 1
    assert data["total_chapters"] == 2
    assert data["total_characters"] == 1
    assert data["total_words"] == 5  # 3 + 2
    assert data["total_lore"] == 1
    assert data["total_timeline"] == 1
