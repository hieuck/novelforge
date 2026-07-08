"""Tests for reading time in chapter stats."""

from __future__ import annotations


def test_reading_time_in_stats(client):
    """Chapter stats includes reading time estimates."""
    proj = client.post("/api/projects/", json={"title": "Test"}).json()
    ch = client.post(
        "/api/chapters/",
        json={
            "project_id": proj["id"],
            "title": "Ch1",
            "content": "word " * 200,  # 200 words ≈ 1 min reading
        },
    ).json()

    r = client.get(f"/api/chapters/{ch['id']}/stats")
    assert r.status_code == 200
    data = r.json()
    assert "reading_time_seconds" in data
    assert "reading_time_minutes" in data
    assert data["reading_time_seconds"] >= 30  # 200 words at 200 wpm ≈ 60s
    assert data["reading_time_minutes"] == 1


def test_reading_time_empty(client):
    """Empty chapter has zero reading time."""
    proj = client.post("/api/projects/", json={"title": "Test"}).json()
    ch = client.post(
        "/api/chapters/",
        json={
            "project_id": proj["id"],
            "title": "Empty",
            "content": "",
        },
    ).json()

    r = client.get(f"/api/chapters/{ch['id']}/stats")
    assert r.status_code == 200
    data = r.json()
    assert data["reading_time_seconds"] == 0
    assert data["reading_time_minutes"] == 0
