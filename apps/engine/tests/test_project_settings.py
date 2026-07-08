"""Tests for GET /api/projects/{id}/settings endpoint."""

from __future__ import annotations


def test_project_settings_empty(client):
    """Returns empty dict when no settings exist."""
    proj = client.post("/api/projects/", json={"title": "Test"}).json()
    r = client.get(f"/api/projects/{proj['id']}/settings")
    assert r.status_code == 200
    assert r.json() == {}


def test_project_settings_not_found(client):
    """Returns 404 for non-existent project."""
    r = client.get("/api/projects/nonexistent/settings")
    assert r.status_code == 404
