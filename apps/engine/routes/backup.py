"""Database backup and restore endpoints."""

from __future__ import annotations

import shutil
import uuid
from datetime import UTC, datetime
from pathlib import Path

from db.base import engine
from db.paths import get_data_dir
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import text

router = APIRouter()
BACKUP_DIR = get_data_dir() / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/backup", status_code=201)
def create_backup() -> dict:
    """Backup the SQLite database to a timestamped file."""
    from db.base import engine as _engine
    db_path = Path(_engine.url.database) if _engine.url.database else get_data_dir() / "novelforge.db"
    if not db_path.exists():
        raise HTTPException(status_code=404, detail="Database file not found")
    ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    backup_name = f"novelforge_backup_{ts}_{uuid.uuid4().hex[:8]}.db"
    backup_path = BACKUP_DIR / backup_name
    shutil.copy2(db_path, backup_path)
    return {"filename": backup_name, "path": str(backup_path), "size_bytes": backup_path.stat().st_size}


@router.get("/backups")
def list_backups() -> list[dict]:
    """List all available database backups."""
    if not BACKUP_DIR.exists():
        return []
    backups = []
    for f in sorted(BACKUP_DIR.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if f.suffix == ".db":
            backups.append(
                {
                    "filename": f.name,
                    "size_bytes": f.stat().st_size,
                    "created_at": datetime.fromtimestamp(f.stat().st_mtime, tz=UTC).isoformat() + "Z",
                }
            )
    return backups


@router.get("/backup/{filename}")
def download_backup(filename: str) -> FileResponse:
    """Download a specific backup file."""
    backup_path = BACKUP_DIR / filename
    if not backup_path.exists() or backup_path.suffix != ".db":
        raise HTTPException(status_code=404, detail="Backup not found")
    return FileResponse(str(backup_path), media_type="application/octet-stream", filename=filename)


@router.post("/backup/{filename}/restore", status_code=200)
def restore_backup(filename: str) -> dict:
    """Restore a backup. Overwrites the current database."""
    backup_path = BACKUP_DIR / filename
    if not backup_path.exists() or backup_path.suffix != ".db":
        raise HTTPException(status_code=404, detail="Backup not found")
    from db.base import engine as _engine
    db_path = Path(_engine.url.database) if _engine.url.database else get_data_dir() / "novelforge.db"
    shutil.copy2(backup_path, db_path)
    return {"message": f"Restored {filename}. Restart the engine for changes to take effect."}


@router.post("/backup/cleanup", status_code=200)
def cleanup_old_backups(keep: int = 10) -> dict:
    """Delete old backups, keeping only the most recent `keep` files."""
    if not BACKUP_DIR.exists():
        return {"deleted": 0, "kept": 0}
    backups = sorted(BACKUP_DIR.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
    backups = [p for p in backups if p.suffix == ".db"]
    if len(backups) <= keep:
        return {"deleted": 0, "kept": len(backups)}
    deleted = 0
    for p in backups[keep:]:
        try:
            p.unlink()
            deleted += 1
        except Exception:
            pass
    return {"deleted": deleted, "kept": keep}


@router.post("/maintenance/vacuum", status_code=200)
def vacuum_database() -> dict:
    """VACUUM the SQLite database to reclaim space."""
    with engine.connect() as conn:
        conn.execute(text("VACUUM"))
    return {"message": "Database vacuumed successfully."}


@router.post("/maintenance/cleanup-images", status_code=200)
def cleanup_orphaned_images() -> dict:
    """Delete generated images not referenced by any chapter or character."""
    from db.session import SessionLocal
    from models.chapter import Chapter
    from models.extra import Character
    from models.image import GeneratedImage

    db = SessionLocal()
    try:
        chapters = {c.illustration_url for c in db.query(Chapter).filter(Chapter.illustration_url.isnot(None)).all()}
        characters = {c.portrait_url for c in db.query(Character).filter(Character.portrait_url.isnot(None)).all()}
        referenced = chapters | characters

        orphans = db.query(GeneratedImage).all()
        removed = 0
        for img in orphans:
            url = f"/api/generated/{img.filename}"
            if url not in referenced:
                file_path = get_data_dir() / "generated" / img.filename
                if file_path.exists():
                    file_path.unlink()
                db.delete(img)
                removed += 1
        db.commit()
        return {"message": f"Cleaned up {removed} orphaned images."}
    finally:
        db.close()


@router.delete("/backup/{filename}", status_code=204)
def delete_single_backup(filename: str) -> None:
    """Delete a specific backup file."""
    import ntpath
    safe_name = ntpath.basename(filename)
    if not safe_name or ".." in safe_name or "/" in safe_name:
        raise HTTPException(status_code=404, detail="Invalid backup filename")
    backup_path = BACKUP_DIR / safe_name
    if not backup_path.exists() or backup_path.suffix != ".db":
        raise HTTPException(status_code=404, detail="Backup not found")
    backup_path.unlink()
