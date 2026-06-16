"""Image generation provider factory."""

from __future__ import annotations

from .base import ImageGenProvider
from .comfy_provider import ComfyUIProvider
from .mock_provider import MockProvider
from .openai_provider import OpenAIProvider


def create_provider(provider: str = "mock", api_key: str = "", model: str = "", base_url: str = "") -> ImageGenProvider:
    """Create an image generation provider instance."""
    p = (provider or "mock").lower()

    if p == "mock":
        return MockProvider()

    if p == "comfyui":
        return ComfyUIProvider(base_url=base_url or "http://127.0.0.1:8188")

    if p in ("openai", "openai_compat"):
        return OpenAIProvider(
            api_key=api_key,
            model=model or "dall-e-3",
            base_url=base_url,
        )

    if p == "stability":
        raise NotImplementedError("Stability AI provider not yet implemented")

    return MockProvider()
