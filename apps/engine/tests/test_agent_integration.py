"""Integration tests for the agent with real Ollama.

Requires: Ollama running with deepseek-r1:8b or similar model.

These tests are skipped by default; run with:
  pytest tests/test_agent_integration.py -v
"""

from __future__ import annotations

import pytest


@pytest.mark.skip(reason="Requires running Ollama with model deepseek-r1:8b")
def test_agent_real_ollama(client):
    """End-to-end: create project, run agent via WebSocket with real LLM."""
    pid = client.post("/api/projects/", json={"title": "Integration Test"}).json()["id"]
    client.post(
        "/api/chapters/",
        json={
            "project_id": pid,
            "title": "Chương 1",
            "content": "Hoàng tử Lạc Thần bắt đầu cuộc hành trình.",
        },
    )

    with client.websocket_connect("/api/ws/agent") as ws:
        ws.send_json(
            {
                "project_id": pid,
                "task": "Tóm tắt chương bằng 2-3 câu.",
                "language": "vi",
            }
        )

        for _ in range(60):
            try:
                data = ws.receive_json()
            except Exception:
                break
            if data["type"] == "done":
                return
            if data["type"] == "error":
                pytest.fail(f"Agent error: {data['message']}")

        pytest.fail("Agent did not complete in time")
