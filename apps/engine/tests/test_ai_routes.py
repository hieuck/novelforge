"""Tests for routes/ai.py — HTTP endpoint and prompt builders."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app import app
from routes.ai import _build_messages, _system_prompt, _ACTION_PROMPTS
from services.context.builder import ProjectContext


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    return TestClient(app)


def _empty_ctx() -> ProjectContext:
    return ProjectContext(project_id=None)


def _mock_settings():
    from services.providers.base import ProviderSettings
    return ProviderSettings(
        provider="ollama",
        base_url="http://localhost:11434",
        model="llama3.1:8b",
    )


# ── _system_prompt ────────────────────────────────────────────────────────────

class TestSystemPrompt:
    def test_empty_context_returns_base_prompt(self):
        ctx = _empty_ctx()
        result = _system_prompt(ctx)
        assert "trợ lý viết tiểu thuyết" in result

    def test_includes_character_context_when_present(self):
        ctx = _empty_ctx()
        ctx.characters = [
            MagicMock(
                name="Aria", alias=None, role="Hero", age="25",
                personality="Brave", appearance=None, goals="Save world",
                secrets=None, relationships=None, summary=None,
            )
        ]
        result = _system_prompt(ctx)
        assert "Aria" in result
        assert "Nhân vật" in result

    def test_no_character_section_when_empty(self):
        ctx = _empty_ctx()
        result = _system_prompt(ctx)
        assert "## Nhân vật" not in result

    def test_includes_style_guide_when_set(self):
        ctx = _empty_ctx()
        ctx.project = MagicMock(style_guide="Văn phong trang trọng")
        result = _system_prompt(ctx)
        assert "Văn phong trang trọng" in result


# ── _build_messages ───────────────────────────────────────────────────────────

class TestBuildMessages:
    def test_minimal_call_returns_system_and_user(self):
        ctx = _empty_ctx()
        msgs = _build_messages(
            system="sys",
            action="continue",
            text="input text",
            instruction="",
            chapter_context="",
            history=[],
        )
        assert msgs[0] == {"role": "system", "content": "sys"}
        assert msgs[-1]["role"] == "user"
        assert "input text" in msgs[-1]["content"]

    def test_action_prompt_included_in_user_message(self):
        msgs = _build_messages(
            system="sys", action="rewrite", text="x",
            instruction="", chapter_context="", history=[],
        )
        assert _ACTION_PROMPTS["rewrite"] in msgs[-1]["content"]

    def test_chapter_context_included_when_provided(self):
        msgs = _build_messages(
            system="sys", action="continue", text="",
            instruction="", chapter_context="Chapter content here", history=[],
        )
        assert "Chapter content here" in msgs[-1]["content"]

    def test_instruction_included_when_provided(self):
        msgs = _build_messages(
            system="sys", action="continue", text="",
            instruction="Keep it formal", chapter_context="", history=[],
        )
        assert "Keep it formal" in msgs[-1]["content"]

    def test_history_injected_between_system_and_current(self):
        from routes.ai import ConversationMessage
        history = [
            ConversationMessage(role="user", content="prior q"),
            ConversationMessage(role="assistant", content="prior a"),
        ]
        msgs = _build_messages(
            system="sys", action="continue", text="new q",
            instruction="", chapter_context="", history=history,
        )
        # system, prior user, prior assistant, current user
        assert len(msgs) == 4
        assert msgs[1] == {"role": "user", "content": "prior q"}
        assert msgs[2] == {"role": "assistant", "content": "prior a"}

    def test_history_trimmed_to_12_messages(self):
        from routes.ai import ConversationMessage
        # 10 turns = 20 messages — should be trimmed to last 12
        history = [
            ConversationMessage(role="user" if i % 2 == 0 else "assistant", content=f"msg{i}")
            for i in range(20)
        ]
        msgs = _build_messages(
            system="sys", action="continue", text="q",
            instruction="", chapter_context="", history=history,
        )
        # system + 12 history + 1 current = 14
        assert len(msgs) == 14

    def test_unknown_action_falls_back_to_default(self):
        msgs = _build_messages(
            system="sys", action="nonexistent_action", text="x",
            instruction="", chapter_context="", history=[],
        )
        assert msgs[-1]["role"] == "user"
        assert "Hỗ trợ viết tiểu thuyết" in msgs[-1]["content"]

    def test_invalid_history_roles_filtered_out(self):
        from routes.ai import ConversationMessage
        history = [
            ConversationMessage(role="system", content="injected system"),
            ConversationMessage(role="user", content="real user"),
        ]
        msgs = _build_messages(
            system="sys", action="continue", text="q",
            instruction="", chapter_context="", history=history,
        )
        roles = [m["role"] for m in msgs]
        # "system" role from history must be filtered out
        assert roles.count("system") == 1
        assert msgs[0]["content"] == "sys"


# ── _ACTION_PROMPTS ───────────────────────────────────────────────────────────

class TestActionPrompts:
    def test_all_expected_actions_present(self):
        required = [
            "continue", "rewrite", "expand", "shorten", "dialogue",
            "emotional", "cinematic", "grammar", "fix_pacing", "add_sensory",
            "tension_build", "perspective_shift", "summarize_chapter",
            "summarize_project", "continuity", "plot_holes", "next_scene",
            "character", "world", "translate_vi_en", "translate_en_vi",
            "premise", "outline",
        ]
        for action in required:
            assert action in _ACTION_PROMPTS, f"Missing action: {action}"

    def test_all_prompts_are_non_empty(self):
        for action, prompt in _ACTION_PROMPTS.items():
            assert len(prompt.strip()) > 0, f"Empty prompt for: {action}"

    def test_new_writing_actions_have_prompts(self):
        for action in ("fix_pacing", "add_sensory", "tension_build", "perspective_shift"):
            assert action in _ACTION_PROMPTS
            assert len(_ACTION_PROMPTS[action]) > 10


# ── HTTP /ai/run endpoint ─────────────────────────────────────────────────────

def _mock_ai_context():
    """Return a pre-configured (mock_build, mock_ctx) pair for patching."""
    mock_client = AsyncMock()
    mock_client.chat_messages = AsyncMock(return_value="Generated text")

    mock_ctx = AsyncMock()
    mock_ctx.character_context.return_value = ""
    mock_ctx.lore_context.return_value = ""
    mock_ctx.timeline_context.return_value = ""
    mock_ctx.style_context.return_value = ""
    mock_ctx.chapter_context.return_value = ""
    mock_ctx.project = None
    return mock_client, mock_ctx


class TestAiRunEndpoint:
    def test_returns_result_on_success(self, client):
        mock_client, mock_ctx = _mock_ai_context()
        with (
            patch("routes.ai._get_settings", return_value=_mock_settings()),
            patch("routes.ai.build_client", return_value=mock_client),
            patch("routes.ai.ProjectContext", return_value=mock_ctx),
        ):
            resp = client.post("/api/ai/run", json={
                "action": "continue",
                "text": "hello",
            })
            assert resp.status_code == 200
            data = resp.json()
            assert data["result"] == "Generated text"
            assert data["action"] == "continue"

    def test_returns_502_on_provider_error(self, client):
        mock_client, mock_ctx = _mock_ai_context()
        mock_client.chat_messages = AsyncMock(side_effect=Exception("provider down"))
        with (
            patch("routes.ai._get_settings", return_value=_mock_settings()),
            patch("routes.ai.build_client", return_value=mock_client),
            patch("routes.ai.ProjectContext", return_value=mock_ctx),
        ):
            resp = client.post("/api/ai/run", json={
                "action": "continue",
                "text": "hello",
            })
            assert resp.status_code == 502
            assert "provider down" in resp.json()["detail"]

    def test_accepts_history_field(self, client):
        mock_client, mock_ctx = _mock_ai_context()
        with (
            patch("routes.ai._get_settings", return_value=_mock_settings()),
            patch("routes.ai.build_client", return_value=mock_client),
            patch("routes.ai.ProjectContext", return_value=mock_ctx),
        ):
            resp = client.post("/api/ai/run", json={
                "action": "rewrite",
                "text": "rewrite me",
                "history": [
                    {"role": "user", "content": "prior"},
                    {"role": "assistant", "content": "response"},
                ],
            })
            assert resp.status_code == 200
            # Verify history was passed through to chat_messages
            called_messages = mock_client.chat_messages.call_args[0][0]
            user_contents = [m["content"] for m in called_messages if m["role"] == "user"]
            assert any("prior" in c for c in user_contents)
