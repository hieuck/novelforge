"""Tests for writing statistics (daily word-count tracking)."""

from __future__ import annotations

from datetime import date


def test_writing_stats_tracks_words_added_on_chapter_update(client):
    """Updating a chapter records a writing session with words added."""
    proj = client.post("/api/projects/", json={"title": "Stats Test"}).json()
    chapter = client.post(
        "/api/chapters/",
        json={"project_id": proj["id"], "title": "Chapter 1", "content": "one two three"},
    ).json()

    # Update with 7 more words than initial 3
    client.patch(f"/api/chapters/{chapter['id']}", json={"content": "one two three four five six seven eight nine ten"})

    r = client.get(f"/api/projects/{proj['id']}/writing-stats")
    assert r.status_code == 200
    data = r.json()
    today = date.today().isoformat()
    assert data["project_id"] == proj["id"]
    assert data["daily_goal"] == 500  # default
    assert any(s["date"] == today and s["words_added"] == 7 for s in data["history"])


def test_writing_stats_daily_goal_can_be_set(client):
    """Project settings can store a daily writing goal."""
    proj = client.post("/api/projects/", json={"title": "Goal Test"}).json()

    r = client.put(f"/api/projects/{proj['id']}/settings", json={"daily_goal": 1000})
    assert r.status_code == 200

    r = client.get(f"/api/projects/{proj['id']}/writing-stats")
    assert r.status_code == 200
    assert r.json()["daily_goal"] == 1000
