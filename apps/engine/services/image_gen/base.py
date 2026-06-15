"""Image generation provider abstraction."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class ImageGenProvider(ABC):
    """Abstract base for image generation providers."""

    @abstractmethod
    async def generate(self, prompt: str, size: str = "1024x1024") -> tuple[bytes, str]:
        """Generate image from prompt. Returns (image_bytes, mime_type)."""
        ...


class ProviderSettings:
    def __init__(
        self,
        provider: str = "openai",
        api_key: str = "",
        model: str = "dall-e-3",
        base_url: str = "",
    ):
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
