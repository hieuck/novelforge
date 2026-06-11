from __future__ import annotations

import json
import os
from typing import Any

from httpx import AsyncClient, HTTPError, Timeout
from services.providers.base import LLMClient, ProviderSettings


class OllamaClient(LLMClient):
    async def chat(self, *, system: str, user: str) -> str:
        url = self.settings.base_url.rstrip("/") + "/api/chat"
        payload = {
            "model": self.settings.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "options": {
                "temperature": self.settings.temperature,
                "num_predict": self.settings.max_tokens,
            },
        }
        async with _client() as client:
            response = await client.post(url, json=payload, timeout=_timeout())
            response.raise_for_status()
            data = response.json()
            return _extract(data)


class OpenAIClient(LLMClient):
    async def chat(self, *, system: str, user: str) -> str:
        url = self.settings.base_url.rstrip("/") + "/chat/completions"
        headers: dict[str, str] = {
            "Content-Type": "application/json",
        }
        if self.settings.api_key:
            headers["Authorization"] = f"Bearer {self.settings.api_key}"
        payload = {
            "model": self.settings.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": self.settings.temperature,
            "max_tokens": self.settings.max_tokens,
        }
        async with _client() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=_timeout())
            response.raise_for_status()
            data = response.json()
            return _extract_openai(data)


def build_client(settings: ProviderSettings) -> LLMClient:
    provider = (settings.provider or "ollama").lower()
    if provider in {"openai", "openai_compat", "lmstudio"}:
        return OpenAIClient(settings)
    return OllamaClient(settings)


def _extract(data: dict[str, Any]) -> str:
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
    return Timeout(connect=5.0, read=120.0, write=10.0, pool=5.0)


def _client() -> AsyncClient:
    return AsyncClient()
