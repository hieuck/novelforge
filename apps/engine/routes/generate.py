"""Image generation routes."""
from __future__ import annotations

import os
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from services.image_gen.factory import create_provider
from services.ai_service import _get_settings

router = APIRouter()

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "generated"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SIZE_MAP = {"small": "512x512", "medium": "1024x1024", "large": "1792x1024"}


class GenImageIn(BaseModel):
    prompt: str
    size: str = "medium"
    provider: str = ""  # empty = use AI settings provider


@router.post("/generate/image", status_code=201)
async def generate_image(payload: GenImageIn) -> dict:
    """Generate an image from a text prompt."""
    if not payload.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    size_str = SIZE_MAP.get(payload.size, "1024x1024")

    # Resolve provider settings
    provider_name = payload.provider or ""
    api_key = ""
    model = ""
    base_url = ""

    if not provider_name:
        settings = await _get_settings()
        provider_name = settings.provider or "mock"
        api_key = settings.api_key or ""
        model = settings.model or ""
        base_url = settings.base_url or ""

    if provider_name in ("ollama",):
        raise HTTPException(status_code=400, detail="Ollama does not support image generation. Use 'mock' for placeholder, ComfyUI for local, or configure an API key.")

    needs_key = provider_name not in ("mock", "comfyui")
    if needs_key and not api_key:
        raise HTTPException(status_code=400, detail=f"API key required for {provider_name}. Use 'mock' for placeholder images, 'comfyui' for local generation, or configure an API key in Settings.")

    try:
        provider = create_provider(provider_name, api_key, model, base_url)
        image_bytes, mime = await provider.generate(payload.prompt, size_str)
    except NotImplementedError:
        raise HTTPException(status_code=400, detail=f"Provider '{provider_name}' does not support image generation yet")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image generation failed: {e}")

    # Save to disk
    ext = "png" if "png" in mime else "jpg"
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = DATA_DIR / filename
    filepath.write_bytes(image_bytes)

    # Register in DB (optional: link to character/chapter later)
    return {
        "filename": filename,
        "url": f"/api/generated/{filename}",
        "mime": mime,
        "size": len(image_bytes),
    }


@router.get("/generated/{filename}")
async def serve_generated(filename: str):
    """Serve a generated image."""
    filepath = DATA_DIR / filename
    if not filepath.exists():
        # Try to find by UUID prefix
        for f in DATA_DIR.iterdir():
            if f.name.startswith(filename):
                filepath = f
                break
        else:
            raise HTTPException(status_code=404, detail="Image not found")

    ext = filepath.suffix.lower()
    media_type = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}.get(ext, "application/octet-stream")
    return FileResponse(str(filepath), media_type=media_type)
