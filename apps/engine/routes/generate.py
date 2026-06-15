"""Image generation routes."""
from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from db.session import SessionLocal
from models.image import GeneratedImage
from models.chapter import Chapter
from services.image_gen.factory import create_provider
from services.ai_service import _get_settings

router = APIRouter()

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "generated"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SIZE_MAP = {"small": "512x512", "medium": "1024x1024", "large": "1792x1024"}


class GenImageIn(BaseModel):
    prompt: str
    size: str = "medium"
    provider: str = ""
    project_id: str = ""
    entity_type: str = ""   # 'character', 'chapter', 'scene'
    entity_id: str = ""


@router.post("/generate/image", status_code=201)
async def generate_image(payload: GenImageIn) -> dict:
    """Generate an image from a text prompt."""
    if not payload.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    size_str = SIZE_MAP.get(payload.size, "1024x1024")

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
        raise HTTPException(status_code=400, detail="Ollama does not support image generation.")

    needs_key = provider_name not in ("mock", "comfyui")
    if needs_key and not api_key:
        raise HTTPException(status_code=400, detail=f"API key required for {provider_name}. Use 'mock' for placeholder or configure an API key.")

    try:
        provider = create_provider(provider_name, api_key, model, base_url)
        image_bytes, mime = await provider.generate(payload.prompt, size_str)
    except NotImplementedError:
        raise HTTPException(status_code=400, detail=f"Provider '{provider_name}' not supported yet")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image generation failed: {e}")

    ext = "png" if "png" in mime else "jpg"
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = DATA_DIR / filename
    filepath.write_bytes(image_bytes)

    # Register in DB
    img_id = str(uuid.uuid4())
    db = SessionLocal()
    try:
        img = GeneratedImage(
            id=img_id, project_id=payload.project_id or "",
            filename=filename, prompt=payload.prompt,
            entity_type=payload.entity_type or None,
            entity_id=payload.entity_id or None,
            mime=mime, file_size=str(len(image_bytes)),
        )
        db.add(img)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()

    return {
        "id": img_id,
        "filename": filename,
        "url": f"/api/generated/{filename}",
        "mime": mime,
        "size": len(image_bytes),
    }


@router.get("/projects/{project_id}/images")
def list_project_images(project_id: str) -> list[dict]:
    """List all generated images for a project."""
    db = SessionLocal()
    try:
        items = db.query(GeneratedImage).filter(
            GeneratedImage.project_id == project_id
        ).order_by(GeneratedImage.created_at.desc()).all()
        return [
            {
                "id": i.id, "filename": i.filename,
                "url": f"/api/generated/{i.filename}",
                "prompt": i.prompt, "entity_type": i.entity_type,
                "entity_id": i.entity_id, "mime": i.mime,
                "file_size": i.file_size,
                "created_at": i.created_at.isoformat() + "Z" if i.created_at else None,
            }
            for i in items
        ]
    finally:
        db.close()


@router.delete("/projects/{project_id}/images/{image_id}", status_code=204)
def delete_project_image(project_id: str, image_id: str) -> None:
    """Delete a generated image."""
    db = SessionLocal()
    try:
        img = db.query(GeneratedImage).filter(
            GeneratedImage.id == image_id,
            GeneratedImage.project_id == project_id,
        ).first()
        if not img:
            raise HTTPException(status_code=404, detail="Image not found")
        filepath = DATA_DIR / img.filename
        if filepath.exists():
            filepath.unlink()
        db.delete(img)
        db.commit()
    finally:
        db.close()


@router.get("/generated/{filename}")
async def serve_generated(filename: str):
    """Serve a generated image."""
    filepath = DATA_DIR / filename
    if not filepath.exists():
        for f in DATA_DIR.iterdir():
            if f.name.startswith(filename):
                filepath = f
                break
        else:
            raise HTTPException(status_code=404, detail="Image not found")

    ext = filepath.suffix.lower()
    media_type = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}.get(ext, "application/octet-stream")
    return FileResponse(str(filepath), media_type=media_type)


@router.post("/projects/{project_id}/storyboard/export-video")
async def export_storyboard_video(project_id: str) -> FileResponse:
    """Export storyboard as MP4 video slideshow. Requires FFmpeg."""
    import asyncio
    import subprocess
    import tempfile

    db = SessionLocal()
    try:
        chapters = db.query(Chapter).filter(
            Chapter.project_id == project_id
        ).order_by(Chapter.scene_order).all()
    finally:
        db.close()

    chapters = [c for c in chapters if c.illustration_url]

    if not chapters:
        raise HTTPException(status_code=400, detail="No chapters with illustrations found. Generate scene images first.")

    temp_dir = Path(tempfile.mkdtemp())
    output_path = DATA_DIR / f"storyboard_{uuid.uuid4()}.mp4"

    try:
        # Download each image and create a concat file for FFmpeg
        import httpx
        concat_lines = []
        async with httpx.AsyncClient() as client:
            for ch in chapters:
                img_url = ch.illustration_url.lstrip("/")
                # Construct full URL from relative path
                img_path = DATA_DIR / Path(img_url).name
                if img_path.exists():
                    ext = img_path.suffix or ".jpg"
                    dest = temp_dir / f"scene_{ch.scene_order:03d}{ext}"
                    import shutil
                    shutil.copy2(img_path, dest)
                    concat_lines.append(f"file '{dest.name}'\nduration 3\n")

        if not concat_lines:
            raise HTTPException(status_code=400, detail="Could not load illustration files")

        # Write concat file
        concat_file = temp_dir / "concat.txt"
        concat_file.write_text("".join(concat_lines))

        # Run FFmpeg
        cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(concat_file),
            "-vf", "fps=24,format=yuv420p",
            "-c:v", "libx264", "-preset", "fast",
            str(output_path),
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        try:
            await asyncio.wait_for(proc.communicate(), timeout=120)
        except asyncio.TimeoutError:
            proc.kill()
            raise HTTPException(status_code=500, detail="Video export timed out")

        if proc.returncode != 0:
            raise HTTPException(status_code=500, detail="FFmpeg processing failed")

        return FileResponse(str(output_path), media_type="video/mp4", filename="storyboard.mp4")

    except HTTPException:
        raise
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="FFmpeg not found. Install FFmpeg to export video.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video export failed: {e}")
    finally:
        # Cleanup temp files
        import shutil
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass
