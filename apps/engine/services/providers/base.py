from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ProviderSettings:
    provider: str = "ollama"
    base_url: str = "http://localhost:11434"
    api_key: Optional[str] = None
    model: str = "llama3.1:8b"
    temperature: float = 0.7
    max_tokens: int = 2048


class LLMClient:
    def __init__(self, settings: ProviderSettings) -> None:
        self.settings = settings

    async def chat(self, *, system: str, user: str) -> str:
        raise NotImplementedError

    @property
    def provider_name(self) -> str:
        return self.settings.provider
