from __future__ import annotations

from collections.abc import AsyncGenerator
from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderSettings:
    provider: str = "ollama"
    base_url: str = "http://localhost:11434"
    api_key: str | None = None
    model: str = "gemma3:4b"
    temperature: float = 0.7
    max_tokens: int = 2048


class LLMClient:
    def __init__(self, settings: ProviderSettings) -> None:
        self.settings = settings

    async def chat(self, *, system: str, user: str) -> str:
        """Single-turn chat returning the full response."""
        raise NotImplementedError

    async def chat_messages(self, messages: list[dict]) -> str:
        """Multi-turn chat with a messages list, returning the full response."""
        raise NotImplementedError

    async def chat_stream(self, messages: list[dict]) -> AsyncGenerator[str, None]:
        """Stream multi-turn chat, yielding text deltas."""
        raise NotImplementedError
        # This line keeps type checkers happy for the async generator protocol.
        yield ""  # type: ignore[misc]

    @property
    def provider_name(self) -> str:
        return self.settings.provider
