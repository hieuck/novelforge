from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from typing import Any

from httpx import AsyncClient, Timeout

from services.providers.base import LLMClient, ProviderSettings


class OllamaClient(LLMClient):
    async def chat(self, *, system: str, user: str) -> str:
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        return await self.chat_messages(messages)

    async def chat_messages(self, messages: list[dict]) -> str:
        url = self.settings.base_url.rstrip("/") + "/api/chat"
        payload = {
            "model": self.settings.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.settings.temperature,
                "num_predict": self.settings.max_tokens,
            },
        }
        async with _client() as client:
            response = await client.post(url, json=payload, timeout=_timeout())
            response.raise_for_status()
            return _extract_ollama(response.json())

    async def chat_stream(self, messages: list[dict]) -> AsyncGenerator[str, None]:
        url = self.settings.base_url.rstrip("/") + "/api/chat"
        payload = {
            "model": self.settings.model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": self.settings.temperature,
                "num_predict": self.settings.max_tokens,
            },
        }
        async with _client() as client:
            async with client.stream("POST", url, json=payload, timeout=_timeout()) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                        delta = (data.get("message") or {}).get("content") or ""
                        if delta:
                            yield delta
                        if data.get("done"):
                            break
                    except (json.JSONDecodeError, KeyError):
                        continue


class OpenAIClient(LLMClient):
    async def chat(self, *, system: str, user: str) -> str:
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        return await self.chat_messages(messages)

    async def chat_messages(self, messages: list[dict]) -> str:
        url = self.settings.base_url.rstrip("/") + "/chat/completions"
        headers = self._headers()
        payload = {
            "model": self.settings.model,
            "messages": messages,
            "temperature": self.settings.temperature,
            "max_tokens": self.settings.max_tokens,
        }
        async with _client() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=_timeout())
            response.raise_for_status()
            return _extract_openai(response.json())

    async def chat_stream(self, messages: list[dict]) -> AsyncGenerator[str, None]:
        url = self.settings.base_url.rstrip("/") + "/chat/completions"
        headers = self._headers()
        payload = {
            "model": self.settings.model,
            "messages": messages,
            "temperature": self.settings.temperature,
            "max_tokens": self.settings.max_tokens,
            "stream": True,
        }
        async with _client() as client:
            async with client.stream("POST", url, headers=headers, json=payload, timeout=_timeout()) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    chunk = line[6:]
                    if chunk.strip() == "[DONE]":
                        break
                    try:
                        data = json.loads(chunk)
                        delta = ((data.get("choices") or [{}])[0].get("delta") or {}).get("content") or ""
                        if delta:
                            yield delta
                    except (json.JSONDecodeError, IndexError, KeyError):
                        continue

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.settings.api_key:
            headers["Authorization"] = f"Bearer {self.settings.api_key}"
        return headers


def build_client(settings: ProviderSettings) -> LLMClient:
    provider = (settings.provider or "ollama").lower()
    if provider in {"openai", "openai_compat", "lmstudio", "openrouter"}:
        return OpenAIClient(settings)
    return OllamaClient(settings)


def _extract_ollama(data: dict[str, Any]) -> str:
    if isinstance(data.get("message"), dict):
        content = data["message"].get("content")
        if isinstance(content, str) and content.strip():
            return content
    return json.dumps(data, ensure_ascii=False)


def _extract_openai(data: dict[str, Any]) -> str:
    choices = data.get("choices") or []
    if choices:
        message = (choices[0] or {}).get("message") or {}
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content
    return json.dumps(data, ensure_ascii=False)


def _timeout() -> Timeout:
    return Timeout(connect=5.0, read=180.0, write=10.0, pool=5.0)


def _client() -> AsyncClient:
    return AsyncClient()
