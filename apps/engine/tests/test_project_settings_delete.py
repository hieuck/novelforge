"""Tests for DELETE /api/projects/{id}/settings endpoint."""
from __future__ import annotations


def test_delete_project_settings(client):
    """Deleting settings removes all settings for a project."""
    proj = client.post("/api/projects/", json={"title": "Test"}).json()
    client.put(f"/api/projects/{proj['id']}/settings", json={"goal": "500", "theme": "dark"})
    
    r = client.delete(f"/api/projects/{proj['id']}/settings")
    assert r.status_code == 204
    
    get_r = client.get(f"/api/projects/{proj['id']}/settings")
    assert get_r.status_code == 200
    assert get_r.json() == {}


def test_delete_project_settings_not_found(client):
    """Returns 404 for non-existent project."""
    r = client.delete("/api/projects/nonexistent/settings")
    assert r.status_code == 404
