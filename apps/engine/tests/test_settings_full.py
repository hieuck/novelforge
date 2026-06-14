"""Full tests for settings endpoints — save, load, test connection."""
from __future__ import annotations


def test_settings_save_and_verify(client):
    """Save settings, then read them back."""
    payload = {
        "provider": "ollama",
        "base_url": "http://localhost:11434",
        "model": "llama3.2",
        "temperature": 0.5,
        "max_tokens": 4096,
    }
    r = client.post("/api/settings/current", json=payload)
    assert r.status_code == 200

    r = client.get("/api/settings/current")
    assert r.status_code == 200
    data = r.json()
    assert data["provider"] == "ollama"
    assert data["model"] == "llama3.2"
    assert data["temperature"] == 0.5
    assert data["max_tokens"] == 4096


def test_settings_test_connection(client):
    """Test connection endpoint returns a result."""
    payload = {
        "provider": "ollama",
        "base_url": "http://localhost:11434",
        "model": "deepseek-r1:8b",
        "api_key": "",
    }
    r = client.post("/api/settings/test", json=payload)
    # May succeed or fail depending on whether Ollama is running
    assert r.status_code == 200


def test_settings_about(client):
    """About endpoint returns app metadata."""
    r = client.get("/api/settings/about")
    assert r.status_code == 200
    data = r.json()
    assert data["app"] == "NovelForge"
    assert "version" in data
    assert "python" in data


def test_settings_list_models(client):
    """List models endpoint returns a response."""
    # This endpoint tries to contact the AI provider, so it may error
    r = client.get("/api/settings/models?provider=ollama&base_url=http://localhost:11434")
    assert r.status_code == 200


def test_settings_delete_all_data(client):
    """Delete all data endpoint returns success."""
    r = client.delete("/api/settings/data/all")
    assert r.status_code in (200, 204)
