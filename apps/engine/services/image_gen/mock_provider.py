"""Mock image provider returning SVG placeholders for testing."""
from __future__ import annotations

from .base import ImageGenProvider


class MockProvider(ImageGenProvider):
    """Returns a placeholder SVG. Useful for testing UI without a real provider."""

    async def generate(self, prompt: str, size: str = "1024x1024") -> tuple[bytes, str]:
        w, h = (int(x) for x in size.split("x"))
        bx, by = (w - 200) // 2, (h - 200) // 2
        cx, cy = w // 2, h // 2
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <rect width="{w}" height="{h}" fill="#1e293b"/>
  <rect x="{bx}" y="{by}" width="200" height="200" rx="16" fill="#334155"/>
  <text x="{cx}" y="{cy - 20}" fill="#94a3b8" font-family="system-ui" font-size="24" text-anchor="middle">🎨</text>
  <text x="{cx}" y="{cy + 30}" fill="#64748b" font-family="system-ui" font-size="14" text-anchor="middle">AI Image</text>
</svg>"""
        return svg.encode("utf-8"), "image/svg+xml"
