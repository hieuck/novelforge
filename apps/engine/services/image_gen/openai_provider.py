"""OpenAI DALL-E image generation provider."""

from __future__ import annotations

import logging

from httpx import AsyncClient, Timeout

from .base import ImageGenProvider

logger = logging.getLogger("novelforge.image_gen.openai")


class OpenAIProvider(ImageGenProvider):
    def __init__(self, api_key: str, model: str = "dall-e-3", base_url: str = ""):
        self.api_key = api_key
        self.model = model
        self.base_url = (base_url or "https://api.openai.com/v1").rstrip("/")

    async def generate(self, prompt: str, size: str = "1024x1024") -> tuple[bytes, str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "prompt": prompt,
            "n": 1,
            "size": size,
            "response_format": "b64_json",
        }
        async with AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/images/generations",
                json=payload,
                headers=headers,
                timeout=Timeout(connect=10.0, read=120.0, write=10.0),
            )
            resp.raise_for_status()
            data = resp.json()
            b64 = data["data"][0]["b64_json"]
            import base64

            return base64.b64decode(b64), "image/png"
