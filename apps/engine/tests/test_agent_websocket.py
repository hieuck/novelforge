"""Test agent WebSocket flow with mocked LLM client."""
from __future__ import annotations

import json
from unittest.mock import patch


def _create_project(client):
    r = client.post("/api/projects/", json={"title": "WS Agent Test", "language": "vi"})
    return r.json()["id"]


class MockLLMClient:
    def __init__(self, responses: list[str] | None = None):
        self.responses = responses or []
        self.call_count = 0

    async def chat_messages(self, messages: list[dict]) -> str:
        idx = self.call_count
        self.call_count += 1
        if idx < len(self.responses):
            return self.responses[idx]
        return '{"reasoning": "ok", "tool": "generate_text", "params": {"prompt": "ok"}, "description": "ok"}'

    async def chat_stream(self, messages: list[dict]):
        yield "mock"


def _recv_until(ws, target_types: set[str], max_msgs=15):
    """Receive WebSocket messages until one of target_types is seen."""
    msgs = []
    for _ in range(max_msgs):
        data = ws.receive_json()
        msgs.append(data)
        if data["type"] in target_types:
            break
    return msgs


def test_agent_empty_task(client):
    """Empty task should return error immediately."""
    with client.websocket_connect("/api/ws/agent") as ws:
        ws.send_json({"project_id": None, "task": "", "language": "vi"})
        data = ws.receive_json()
        assert data["type"] == "error"


def test_agent_no_provider(client):
    """Test that missing AI provider config returns error."""
    pid = _create_project(client)
    # Patch _get_settings to return empty base_url
    with patch("routes.agent._get_settings") as mock_settings:
        from services.providers.base import ProviderSettings
        mock_settings.return_value = ProviderSettings(base_url="", model="")

        with client.websocket_connect("/api/ws/agent") as ws:
            ws.send_json({"project_id": pid, "task": "test", "language": "vi"})
            data = ws.receive_json()
            assert data["type"] == "error"


def test_agent_plan_execute_flow(client):
    """Test agent plans and executes with mocked LLM."""
    pid = _create_project(client)

    mock_llm = MockLLMClient(responses=[
        json.dumps([{"step": 1, "tool": "read_project_summary", "description": "Read project", "params": {}}]),
        json.dumps({"reasoning": "Read project data first", "tool": "read_project_summary", "description": "Read project", "params": {}}),
    ])

    with patch("routes.agent.build_client", return_value=mock_llm):
        with client.websocket_connect(f"/api/ws/agent") as ws:
            ws.send_json({"project_id": pid, "task": "Read project", "language": "vi"})

            msgs = _recv_until(ws, {"done", "error", "cancelled"}, max_msgs=10)
            types = [m["type"] for m in msgs]

            assert "plan" in types, f"Expected plan in {types}"
            assert "step_start" in types, f"Expected step_start in {types}"


def test_agent_generate_text(client):
    """Test agent handles generate_text tool."""
    pid = _create_project(client)

    mock_llm = MockLLMClient(responses=[
        json.dumps([{"step": 1, "tool": "generate_text", "description": "Write content", "params": {"prompt": "Write a short story about a hero"}}]),
        json.dumps({"reasoning": "Time to write", "tool": "generate_text", "description": "Write", "params": {"prompt": "Write"}}),
        json.dumps({"quality": "good", "retry_needed": False}),
    ])

    with patch("routes.agent.build_client", return_value=mock_llm):
        with client.websocket_connect(f"/api/ws/agent") as ws:
            ws.send_json({"project_id": pid, "task": "Write something", "language": "vi"})

            msgs = _recv_until(ws, {"done", "error"}, max_msgs=12)
            types = [m["type"] for m in msgs]

            assert "text_delta" in types, f"Expected streaming text in {types}"
            assert "step_done" in types, f"Expected step_done in {types}"
