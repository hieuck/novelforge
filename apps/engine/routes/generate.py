"""Image generation routes."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

from db.session import SessionLocal
from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from models.image import GeneratedImage
from pydantic import BaseModel
from services.ai_service import _get_settings
from services.image_gen.factory import create_provider

router = APIRouter()

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "generated"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SIZE_MAP = {"small": "512x512", "medium": "1024x1024", "large": "1792x1024"}


class GenImageIn(BaseModel):
    prompt: str
    size: str = "medium"
    provider: str = ""
    project_id: str = ""
    entity_type: str = ""  # 'character', 'chapter', 'scene'
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
        raise HTTPException(
            status_code=400,
            detail=f"API key required for {provider_name}. Use 'mock' for placeholder or configure an API key.",
        )

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
            id=img_id,
            project_id=payload.project_id or "",
            filename=filename,
            prompt=payload.prompt,
            entity_type=payload.entity_type or None,
            entity_id=payload.entity_id or None,
            mime=mime,
            file_size=str(len(image_bytes)),
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
def list_project_images(project_id: str, entity_type: str | None = None, entity_id: str | None = None) -> list[dict]:
    """List all generated images for a project. Filter by entity_type and/or entity_id."""
    db = SessionLocal()
    try:
        q = db.query(GeneratedImage).filter(GeneratedImage.project_id == project_id)
        if entity_type:
            q = q.filter(GeneratedImage.entity_type == entity_type)
        if entity_id:
            q = q.filter(GeneratedImage.entity_id == entity_id)
        items = q.order_by(GeneratedImage.created_at.desc()).all()
        return [
            {
                "id": i.id,
                "filename": i.filename,
                "url": f"/api/generated/{i.filename}",
                "prompt": i.prompt,
                "entity_type": i.entity_type,
                "entity_id": i.entity_id,
                "mime": i.mime,
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
        img = (
            db.query(GeneratedImage)
            .filter(
                GeneratedImage.id == image_id,
                GeneratedImage.project_id == project_id,
            )
            .first()
        )
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
    media_type = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}.get(
        ext, "application/octet-stream"
    )
    return FileResponse(str(filepath), media_type=media_type)


@router.post("/projects/{project_id}/storyboard/export-video", status_code=201)
async def export_storyboard_video(project_id: str, background_tasks: BackgroundTasks) -> dict:
    """Start storyboard video export in background. Returns job_id. Poll /api/jobs/{job_id} or WS."""
    from models.extra import Job as JobModel

    db = SessionLocal()
    try:
        job = JobModel(
            id=str(uuid.uuid4()),
            project_id=project_id,
            kind="video_export",
            status="queued",
            params=json.dumps({"project_id": project_id}),
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        result = {"job_id": job.id, "status": job.status}
    finally:
        db.close()

    background_tasks.add_task(_run_video_export, result["job_id"])
    return result


async def _run_video_export(job_id: str) -> None:
    """Run video export in background, updating job status."""
    import asyncio
    import shutil
    import tempfile

    from db.session import SessionLocal
    from models.chapter import Chapter as ChapterModel
    from models.extra import Job as JobModel

    db = SessionLocal()
    try:
        job = db.query(JobModel).filter(JobModel.id == job_id).first()
        if not job or job.status == "cancelled":
            return

        params = json.loads(job.params or "{}")
        project_id = params["project_id"]

        chapters = (
            db.query(ChapterModel)
            .filter(
                ChapterModel.project_id == project_id,
                ChapterModel.illustration_url.isnot(None),
            )
            .order_by(ChapterModel.scene_order)
            .all()
        )
    finally:
        db.close()

    if not chapters:
        _update_job(job_id, "failed", "No chapters with illustrations found")
        return

    job_id_local = job_id
    temp_dir_obj = tempfile.mkdtemp()
    temp_dir = Path(temp_dir_obj)
    output_path = DATA_DIR / f"storyboard_{uuid.uuid4()}.mp4"

    try:
        from db.session import SessionLocal

        db2 = SessionLocal()
        try:
            j = db2.query(JobModel).filter(JobModel.id == job_id_local).first()
            if j:
                j.status = "running"
                j.updated_at = datetime.now(UTC)
                db2.commit()
        finally:
            db2.close()

        concat_lines = []
        total = len(chapters)
        for idx, ch in enumerate(chapters):
            img_path = DATA_DIR / Path(ch.illustration_url.lstrip("/")).name
            if img_path.exists():
                ext = img_path.suffix or ".jpg"
                dest = temp_dir / f"scene_{ch.scene_order:03d}{ext}"
                shutil.copy2(img_path, dest)
                concat_lines.append(f"file '{dest.name}'\nduration 3\n")
                # Update progress
                _update_job_progress(job_id_local, idx + 1, total)

        if not concat_lines:
            _update_job(job_id_local, "failed", "Could not load illustration files")
            return

        concat_file = temp_dir / "concat.txt"
        concat_file.write_text("".join(concat_lines))

        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-vf",
            "fps=24,format=yuv420p",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            str(output_path),
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            await asyncio.wait_for(proc.communicate(), timeout=120)
        except TimeoutError:
            proc.kill()
            _update_job(job_id_local, "failed", "Video export timed out")
            return

        if proc.returncode != 0:
            _update_job(job_id_local, "failed", "FFmpeg processing failed")
            return

        _update_job(job_id_local, "done", str(output_path))

    except FileNotFoundError:
        _update_job(job_id_local, "failed", "FFmpeg not found")
    except Exception as e:
        _update_job(job_id_local, "failed", f"Video export failed: {e}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@router.get("/jobs/{job_id}/video")
def download_video(job_id: str) -> FileResponse:
    """Download the completed video export."""
    from models.extra import Job as JobModel

    db = SessionLocal()
    try:
        job = db.query(JobModel).filter(JobModel.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        if job.status != "done":
            raise HTTPException(status_code=400, detail="Video export not completed yet")
        result = json.loads(job.result or "{}")
        path = result.get("message", "")
        if not path or not Path(path).exists():
            raise HTTPException(status_code=404, detail="Video file not found")
        return FileResponse(path, media_type="video/mp4", filename="storyboard.mp4")
    finally:
        db.close()


def _update_job(job_id: str, status: str, message: str = "") -> None:
    from db.session import SessionLocal
    from models.extra import Job as JobModel

    db = SessionLocal()
    try:
        job = db.query(JobModel).filter(JobModel.id == job_id).first()
        if not job:
            return
        job.status = status
        job.result = json.dumps({"message": message})
        job.updated_at = datetime.now(UTC)
        db.commit()
    except Exception:
        pass
    finally:
        db.close()


def _update_job_progress(job_id: str, current: int, total: int) -> None:
    from db.session import SessionLocal
    from models.extra import Job as JobModel

    db = SessionLocal()
    try:
        job = db.query(JobModel).filter(JobModel.id == job_id).first()
        if not job:
            return
        job.result = json.dumps({"progress": current, "total": total, "message": f"Processing {current}/{total}"})
        job.updated_at = datetime.now(UTC)
        db.commit()
    except Exception:
        pass
    finally:
        db.close()
