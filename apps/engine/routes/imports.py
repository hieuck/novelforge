from __future__ import annotations

import re
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.session import SessionLocal
from models.chapter import Chapter
from models.project import Project

router = APIRouter()


class ImportRequest(BaseModel):
    project_id: str
    content: str
    filename: str = "import.md"
    mode: str = "single"  # single | split_h2


def _count_words(text: str) -> int:
    return len(text.split()) if text else 0


def _split_by_h2(content: str) -> list[tuple[str, str]]:
    """Split by ## headings. Lines before first ## are ignored (title/preamble)."""
    chunks: list[tuple[str, str]] = []
    current_title: str | None = None
    current_lines: list[str] = []

    for line in content.splitlines():
        if line.startswith("## "):
            if current_title is not None:
                body = "\n".join(current_lines).strip()
                if body:
                    chunks.append((current_title, body))
            current_title = line[3:].strip()
            current_lines = []
        elif line.startswith("# "):
            pass  # top-level heading = document title, skip
        else:
            if current_title is not None:
                current_lines.append(line)
            # lines before first ## are preamble, dropped

    if current_title is not None:
        body = "\n".join(current_lines).strip()
        if body:
            chunks.append((current_title, body))

    return chunks if chunks else [("Imported", content.strip())]


@router.post("/import")
def import_content(payload: ImportRequest) -> dict:
    db: Session = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == payload.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        existing = db.query(Chapter).filter(Chapter.project_id == payload.project_id).count()

        if payload.mode == "split_h2":
            chunks = _split_by_h2(payload.content)
            created = []
            for i, (title, body) in enumerate(chunks):
                ch = Chapter(
                    id=str(uuid.uuid4()),
                    project_id=payload.project_id,
                    title=title, content=body,
                    scene_order=existing + i, status="draft",
                    word_count=_count_words(body),
                )
                db.add(ch)
                created.append({"id": ch.id, "title": ch.title})
            db.commit()
            return {"imported": len(created), "chapters": created}
        else:
            stem = re.sub(r"\.[^.]+$", "", payload.filename)
            ch = Chapter(
                id=str(uuid.uuid4()),
                project_id=payload.project_id,
                title=stem or "Imported", content=payload.content,
                scene_order=existing, status="draft",
                word_count=_count_words(payload.content),
            )
            db.add(ch)
            db.commit()
            return {"imported": 1, "chapters": [{"id": ch.id, "title": ch.title}]}
    finally:
        db.close()
