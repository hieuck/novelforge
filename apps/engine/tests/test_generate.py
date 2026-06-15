"""Tests for image generation endpoints."""
from __future__ import annotations

from unittest.mock import patch, AsyncMock, Mock


def test_generate_image_missing_prompt(client):
    """POST /generate/image without prompt returns 400."""
    r = client.post("/api/generate/image", json={"prompt": ""})
    assert r.status_code == 400


def test_generate_image_ollama(client):
    """Ollama provider should reject image gen."""
    with patch("routes.generate._get_settings") as mock_settings:
        from services.providers.base import ProviderSettings
        mock_settings.return_value = ProviderSettings(provider="ollama", api_key="")
        r = client.post("/api/generate/image", json={"prompt": "test"})
        assert r.status_code == 400
        assert "Ollama" in r.json()["detail"]


def test_generate_image_no_api_key(client):
    """No API key should return 400."""
    with patch("routes.generate._get_settings") as mock_settings:
        from services.providers.base import ProviderSettings
        mock_settings.return_value = ProviderSettings(provider="openai", api_key="")
        r = client.post("/api/generate/image", json={"prompt": "test"})
        assert r.status_code == 400
        assert "API key" in r.json()["detail"]


def test_serve_generated_not_found(client):
    """GET /generated/unknown returns 404."""
    r = client.get("/api/generated/nonexistent.png")
    assert r.status_code == 404
