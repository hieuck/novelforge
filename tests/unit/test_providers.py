"""Unit tests for AI provider abstraction layer."""
from __future__ import annotations
import sys, pathlib, asyncio, pytest
from unittest.mock import AsyncMock, MagicMock, patch
ENGINE_DIR = pathlib.Path(__file__).resolve().parent.parent.parent / "apps" / "engine"
sys.path.insert(0, str(ENGINE_DIR))
from services.providers.base import ProviderSettings, LLMClient
from services.providers.openai_compat import OllamaClient, OpenAIClient, build_client, _extract, _extract_openai

def test_provider_settings_defaults():
    s = ProviderSettings()
    assert s.provider == "ollama" and s.model == "llama3.1:8b" and s.temperature == 0.7

def test_provider_settings_immutable():
    s = ProviderSettings()
    with pytest.raises((AttributeError, TypeError)): s.provider = "x"

def test_build_client_ollama():
    assert isinstance(build_client(ProviderSettings(provider="ollama")), OllamaClient)

def test_build_client_openai_compat():
    assert isinstance(build_client(ProviderSettings(provider="openai_compat")), OpenAIClient)

def test_build_client_lmstudio():
    assert isinstance(build_client(ProviderSettings(provider="lmstudio")), OpenAIClient)

def test_build_client_unknown_defaults_ollama():
    assert isinstance(build_client(ProviderSettings(provider="mystery")), OllamaClient)

def test_extract_ollama_content():
    assert _extract({"message": {"content": "Hello"}}) == "Hello"

def test_extract_ollama_empty_fallback():
    result = _extract({"message": {"content": ""}})
    assert isinstance(result, str)

def test_extract_ollama_missing_message():
    result = _extract({"done": True})
    assert "done" in result

def test_extract_openai_standard():
    assert _extract_openai({"choices": [{"message": {"content": "Hi"}}]}) == "Hi"

def test_extract_openai_empty_choices():
    assert isinstance(_extract_openai({"choices": []}), str)

def test_extract_openai_missing_choices():
    assert isinstance(_extract_openai({"error": "fail"}), str)

def test_llm_base_raises():
    c = LLMClient(ProviderSettings())
    with pytest.raises(NotImplementedError):
        asyncio.get_event_loop().run_until_complete(c.chat(system="s", user="u"))

def test_llm_provider_name():
    assert LLMClient(ProviderSettings(provider="ollama")).provider_name == "ollama"

def _mock_http(json_response):
    resp = MagicMock()
    resp.json.return_value = json_response
    resp.raise_for_status = MagicMock()
    http = AsyncMock(); http.post = AsyncMock(return_value=resp)
    cm = AsyncMock(); cm.__aenter__ = AsyncMock(return_value=http); cm.__aexit__ = AsyncMock(return_value=False)
    return cm

@pytest.mark.asyncio
async def test_ollama_chat_success():
    cm = _mock_http({"message": {"content": "Generated text"}})
    with patch("services.providers.openai_compat._client", return_value=cm):
        result = await OllamaClient(ProviderSettings()).chat(system="s", user="u")
    assert result == "Generated text"

@pytest.mark.asyncio
async def test_openai_chat_success():
    cm = _mock_http({"choices": [{"message": {"content": "OpenAI resp"}}]})
    with patch("services.providers.openai_compat._client", return_value=cm):
        result = await OpenAIClient(ProviderSettings(provider="openai_compat", api_key="key")).chat(system="s", user="u")
    assert result == "OpenAI resp"

@pytest.mark.asyncio
async def test_ollama_chat_http_error():
    import httpx
    http = AsyncMock(); http.post = AsyncMock(side_effect=httpx.ConnectError("refused"))
    cm = AsyncMock(); cm.__aenter__ = AsyncMock(return_value=http); cm.__aexit__ = AsyncMock(return_value=False)
    with patch("services.providers.openai_compat._client", return_value=cm):
        with pytest.raises(Exception): await OllamaClient(ProviderSettings()).chat(system="s", user="u")

@pytest.mark.asyncio
async def test_openai_bearer_auth_header():
    """OpenAI client must include Authorization: Bearer header when api_key is set."""
    captured_headers = {}
    async def fake_post(url, headers=None, json=None, timeout=None):
        captured_headers.update(headers or {})
        resp = MagicMock(); resp.raise_for_status = MagicMock()
        resp.json.return_value = {"choices": [{"message": {"content": "ok"}}]}
        return resp
    http = AsyncMock(); http.post = fake_post
    cm = AsyncMock(); cm.__aenter__ = AsyncMock(return_value=http); cm.__aexit__ = AsyncMock(return_value=False)
    with patch("services.providers.openai_compat._client", return_value=cm):
        await OpenAIClient(ProviderSettings(provider="openai_compat", api_key="sk-test")).chat(system="s", user="u")
    assert "Authorization" in captured_headers
    assert "sk-test" in captured_headers["Authorization"]
