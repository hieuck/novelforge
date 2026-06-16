"""Tests for /api/ai/run endpoint with mocked AI provider."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch


def test_ai_run_no_settings(client):
    """POST /api/ai/run with dummy text should return 200 (mock)."""
    with patch("routes.ai.run_ai", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = {"result": "Mocked AI response"}
        r = client.post(
            "/api/ai/run",
            json={
                "project_id": None,
                "action": "continue",
                "text": "Test text",
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert "result" in data


def test_ai_run_empty_text(client):
    """Empty text should still be accepted."""
    with patch("routes.ai.run_ai", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = {"result": ""}
        r = client.post(
            "/api/ai/run",
            json={
                "project_id": None,
                "action": "continue",
                "text": "",
            },
        )
        assert r.status_code == 200


def test_ai_run_with_project(client):
    """Run AI with a real project ID."""
    proj = client.post("/api/projects/", json={"title": "AI Test"}).json()
    with patch("routes.ai.run_ai", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = {"result": "Project-aware response"}
        r = client.post(
            "/api/ai/run",
            json={
                "project_id": proj["id"],
                "action": "summarize_chapter",
                "text": "Some chapter content",
            },
        )
        assert r.status_code == 200
