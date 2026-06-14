"""Tests for /api/settings/* endpoints."""
from __future__ import annotations


_DEFAULT_SETTINGS = {
    "provider": "ollama",
    "base_url": "http://localhost:11434",
    "model": "llama3.1:8b",
    "temperature": 0.7,
    "max_tokens": 2048,
}


def test_settings_about(client):
    r = client.get("/api/settings/about")
    assert r.status_code == 200
    data = r.json()
    assert "app" in data
    assert "version" in data


def test_settings_current(client):
    r = client.get("/api/settings/current")
    assert r.status_code == 200
    data = r.json()
    assert "provider" in data
    assert "model" in data


def test_settings_save_and_read(client):
    r = client.post("/api/settings/current", json=_DEFAULT_SETTINGS)
    assert r.status_code == 200

    r = client.get("/api/settings/current")
    assert r.status_code == 200
    data = r.json()
    assert data["provider"] == "ollama"
    assert data["model"] == "llama3.1:8b"
    assert data["temperature"] == 0.7
    assert data["max_tokens"] == 2048
