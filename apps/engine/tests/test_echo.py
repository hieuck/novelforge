"""Tests for GET/POST /api/tools/echo endpoint."""

from __future__ import annotations


def test_echo_get(client):
    """GET echo returns ok and method."""
    r = client.get("/api/tools/echo")
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["method"] == "GET"


def test_echo_post(client):
    """POST echo returns the posted data."""
    r = client.post("/api/tools/echo", json={"hello": "world"})
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["method"] == "POST"
    assert data["body"]["hello"] == "world"


def test_echo_not_found(client):
    """Returns 404 for invalid path."""
    r = client.get("/api/tools/echo/invalid")
    assert r.status_code == 404
