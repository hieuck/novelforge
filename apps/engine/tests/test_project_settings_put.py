"""Tests for PUT /api/projects/{id}/settings endpoint."""

from __future__ import annotations


def test_put_project_settings(client):
    """Save and retrieve project settings."""
    proj = client.post("/api/projects/", json={"title": "Test"}).json()
    r = client.put(f"/api/projects/{proj['id']}/settings", json={"daily_goal": "500", "genre": "fantasy"})
    assert r.status_code == 200
    data = r.json()
    assert data["daily_goal"] == "500"
    assert data["genre"] == "fantasy"

    # Verify persisted
    r2 = client.get(f"/api/projects/{proj['id']}/settings")
    assert r2.status_code == 200
    assert r2.json()["daily_goal"] == "500"


def test_put_project_settings_not_found(client):
    """Returns 404 for non-existent project."""
    r = client.put("/api/projects/nonexistent/settings", json={"key": "val"})
    assert r.status_code == 404
