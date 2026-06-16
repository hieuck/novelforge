from __future__ import annotations

import io
import json
import zipfile
from datetime import UTC, datetime

from db.session import SessionLocal
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from models.chapter import Chapter
from models.extra import Character, Lore, TimelineItem
from models.project import Project
from pydantic import BaseModel
from sqlalchemy.orm import Session

router = APIRouter()

_MIME: dict[str, str] = {
    "md": "text/markdown",
    "txt": "text/plain",
    "html": "text/html",
    "json": "application/json",
    "zip": "application/zip",
}

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  body {{ max-width: 780px; margin: 2rem auto; font-family: Georgia, serif;
          line-height: 1.8; color: #222; padding: 0 1rem; }}
  h1 {{ font-size: 2rem; margin-bottom: 0.25rem; }}
  .meta {{ color: #666; font-size: 0.9rem; margin-bottom: 2rem; }}
  h2 {{ font-size: 1.4rem; margin-top: 3rem; border-bottom: 1px solid #ddd; padding-bottom: 0.4rem; }}
  p {{ margin: 0.8rem 0; text-indent: 1.5em; }}
  p:first-of-type {{ text-indent: 0; }}
</style>
</head>
<body>
<h1>{title}</h1>
<div class="meta">{genre}{description}</div>
{chapters}
</body>
</html>"""


class ProjectExportIn(BaseModel):
    project_id: str
    fmt: str = "md"


def _load_data(db: Session, project_id: str) -> tuple[Project, list[Chapter]]:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    chapters = db.query(Chapter).filter(Chapter.project_id == project_id).order_by(Chapter.scene_order).all()
    return project, chapters


def _safe_filename(title: str) -> str:
    return "".join(c if c.isalnum() or c in " _-" else "_" for c in title).strip() or "export"


def _build_md(project: Project, chapters: list[Chapter]) -> str:
    lines: list[str] = [f"# {project.title}"]
    if project.description:
        lines.append(f"\n{project.description}")
    lines.append("")
    for ch in chapters:
        lines.append(f"\n## {ch.title or 'Untitled'}")
        lines.append("")
        lines.append(ch.content or "")
    return "\n".join(lines)


def _build_txt(project: Project, chapters: list[Chapter]) -> str:
    lines: list[str] = [project.title.upper(), "=" * len(project.title)]
    if project.description:
        lines.append(project.description)
    lines.append("")
    for ch in chapters:
        lines.append(f"\n{ch.title or 'Untitled'}")
        lines.append("-" * 40)
        lines.append(ch.content or "")
    return "\n".join(lines)


def _build_html(project: Project, chapters: list[Chapter]) -> str:
    ch_html_parts: list[str] = []
    for ch in chapters:
        content = ch.content or ""
        paragraphs = "".join(f"<p>{line}</p>" for line in content.split("\n") if line.strip())
        ch_html_parts.append(f"<h2>{ch.title or 'Untitled'}</h2>\n{paragraphs}")

    genre_str = f"{project.genre} · " if project.genre else ""
    desc_str = project.description or ""

    return HTML_TEMPLATE.format(
        lang=project.language or "vi",
        title=project.title,
        genre=genre_str,
        description=desc_str,
        chapters="\n".join(ch_html_parts),
    )


def _build_zip(db: Session, project: Project, chapters: list[Chapter]) -> bytes:
    buf = io.BytesIO()
    characters = db.query(Character).filter(Character.project_id == project.id).all()
    lore_items = db.query(Lore).filter(Lore.project_id == project.id).all()
    timeline = db.query(TimelineItem).filter(TimelineItem.project_id == project.id).all()

    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # Main story as markdown
        zf.writestr("story.md", _build_md(project, chapters))

        # Individual chapter files
        for i, ch in enumerate(chapters, 1):
            safe = _safe_filename(ch.title or f"chapter_{i}")
            zf.writestr(f"chapters/{i:03d}_{safe}.md", ch.content or "")

        # Project metadata
        meta = {
            "id": project.id,
            "title": project.title,
            "description": project.description,
            "genre": project.genre,
            "language": project.language,
            "summary": project.summary,
            "style_guide": project.style_guide,
            "exported_at": datetime.now(UTC).isoformat(),
        }
        zf.writestr("project.json", json.dumps(meta, ensure_ascii=False, indent=2))

        # Characters
        char_data = [
            {
                "id": c.id,
                "name": c.name,
                "alias": c.alias,
                "role": c.role,
                "age": c.age,
                "personality": c.personality,
                "appearance": c.appearance,
                "goals": c.goals,
                "secrets": c.secrets,
                "notes": c.notes,
            }
            for c in characters
        ]
        zf.writestr("characters.json", json.dumps(char_data, ensure_ascii=False, indent=2))

        # Lore
        lore_data = [
            {
                "id": item.id,
                "name": item.name,
                "lore_type": item.lore_type,
                "description": item.description,
                "tags": item.tags,
            }
            for item in lore_items
        ]
        zf.writestr("lore.json", json.dumps(lore_data, ensure_ascii=False, indent=2))

        # Timeline
        timeline_data = [
            {
                "id": ev.id,
                "title": ev.title,
                "event_date": ev.event_date,
                "description": ev.description,
            }
            for ev in timeline
        ]
        zf.writestr("timeline.json", json.dumps(timeline_data, ensure_ascii=False, indent=2))

    buf.seek(0)
    return buf.read()


@router.get("/chapters/{chapter_id}/export")
def export_single_chapter(chapter_id: str, format: str = "txt") -> Response:
    """Export a single chapter as text or markdown."""
    if format not in _MIME:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")

    db = SessionLocal()
    try:
        ch = db.query(Chapter).filter(Chapter.id == chapter_id).first()
        if not ch:
            raise HTTPException(status_code=404, detail="Chapter not found")

        if format == "json":
            content = json.dumps({
                "id": ch.id,
                "title": ch.title,
                "content": ch.content,
                "word_count": ch.word_count,
                "status": ch.status,
                "scene_order": ch.scene_order,
                "created_at": ch.created_at.isoformat() if ch.created_at else None,
                "updated_at": ch.updated_at.isoformat() if ch.updated_at else None,
            }, ensure_ascii=False, indent=2)
        elif format == "md":
            content = f"# {ch.title or 'Untitled'}\n\n{ch.content or ''}"
        elif format == "html":
            title = ch.title or "Untitled"
            body = "".join(f"<p>{line}</p>" for line in (ch.content or "").split("\n") if line.strip())
            content = (
                f"<!DOCTYPE html><html><head><meta charset='utf-8'>"
                f"<title>{title}</title>"
                f"<style>body{{max-width:780px;margin:2rem auto;font-family:Georgia,serif;line-height:1.8;color:#222;padding:0 1rem}}"
                f"h1{{font-size:2rem}}</style></head><body>"
                f"<h1>{title}</h1>\n{body}"
                f"</body></html>"
            )
        else:
            content = f"{ch.title or 'Untitled'}\n{'=' * 40}\n\n{ch.content or ''}"

        filename = _safe_filename(ch.title or "chapter")
        import urllib.parse
        encoded = urllib.parse.quote(f"{filename}.{format}", safe="")
        return Response(
            content=content.encode("utf-8"),
            media_type=_MIME[format],
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded}"},
        )
    finally:
        db.close()


@router.post("/export")
async def export_project(payload: ProjectExportIn) -> Response:
    fmt = payload.fmt.lower()
    if fmt not in _MIME:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {fmt}")

    db = SessionLocal()
    try:
        project, chapters = _load_data(db, payload.project_id)
        safe_title = _safe_filename(project.title)

        if fmt == "json":
            characters = db.query(Character).filter(Character.project_id == payload.project_id).all()
            lore_items = db.query(Lore).filter(Lore.project_id == payload.project_id).all()
            timeline = db.query(TimelineItem).filter(TimelineItem.project_id == payload.project_id).all()
            content_bytes = json.dumps({
                "id": project.id,
                "title": project.title,
                "description": project.description,
                "genre": project.genre,
                "language": project.language,
                "summary": project.summary,
                "style_guide": project.style_guide,
                "created_at": project.created_at.isoformat() if project.created_at else None,
                "updated_at": project.updated_at.isoformat() if project.updated_at else None,
                "chapters": [
                    {
                        "id": ch.id, "title": ch.title, "content": ch.content,
                        "word_count": ch.word_count, "status": ch.status,
                        "scene_order": ch.scene_order,
                    }
                    for ch in chapters
                ],
                "characters": [
                    {"id": c.id, "name": c.name, "role": c.role, "gender": c.gender,
                     "personality": c.personality, "appearance": c.appearance}
                    for c in characters
                ],
                "lore": [
                    {"id": l.id, "name": l.name, "lore_type": l.lore_type, "description": l.description}
                    for l in lore_items
                ],
                "timeline": [
                    {"id": t.id, "title": t.title, "event_date": t.event_date, "description": t.description}
                    for t in timeline
                ],
            }, ensure_ascii=False, indent=2).encode("utf-8")
        elif fmt == "md":
            content_bytes = _build_md(project, chapters).encode("utf-8")
        elif fmt == "txt":
            content_bytes = _build_txt(project, chapters).encode("utf-8")
        elif fmt == "html":
            content_bytes = _build_html(project, chapters).encode("utf-8")
        else:  # zip
            content_bytes = _build_zip(db, project, chapters)
    finally:
        db.close()

    filename = f"{safe_title}.{fmt}"
    import urllib.parse

    encoded = urllib.parse.quote(filename, safe="")
    return Response(
        content=content_bytes,
        media_type=_MIME[fmt],
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded}"},
    )
