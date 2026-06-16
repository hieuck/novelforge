"""Test AI WebSocket streaming endpoint with mocked engine."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch


def test_ai_ws_health(client):
    """Simple connect/disconnect to AI WS."""
    with client.websocket_connect("/api/ws/ai") as ws:
        ws.send_json({"action": "continue", "text": "Hello"})
        # Should receive either delta or error
        data = ws.receive_json()
        assert "delta" in data or "error" in data


def test_ai_ws_stream(client):
    """Test streaming response from AI WS with mocked AIEngine."""

    async def mock_stream_gen(*args, **kwargs):
        yield "Hello"
        yield " world"

    with patch("routes.ai.AIEngine") as MockEngine:
        instance = MockEngine.return_value
        instance.prepare = AsyncMock()
        instance.stream = mock_stream_gen

        with client.websocket_connect("/api/ws/ai") as ws:
            ws.send_json({"action": "continue", "text": "Write a story"})

            chunks = []
            for _ in range(5):
                try:
                    data = ws.receive_json()
                    if "delta" in data:
                        chunks.append(data["delta"])
                    if data.get("done"):
                        break
                except Exception:
                    break

            assert len(chunks) > 0, "Expected at least one chunk"


def test_ai_ws_error_on_prepare(client):
    """Test that engine prepare failure returns error."""
    with patch("routes.ai.AIEngine") as MockEngine:
        instance = MockEngine.return_value
        instance.prepare = AsyncMock(side_effect=Exception("Context load failed"))

        with client.websocket_connect("/api/ws/ai") as ws:
            ws.send_json({"action": "continue", "text": "test"})
            data = ws.receive_json()
            assert "error" in data
