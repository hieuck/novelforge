from __future__ import annotations

import json
from typing import Any

from db.session import SessionLocal
from models.character import Character
from models.chapter import Chapter
from models.lore import Lore
from models.project import Project
from models.timeline import TimelineItem


class ProjectContext:
    def __init__(self, project_id: str | None = None) -> None:
        self.project_id = project_id
        self.project: Project | None = None
        self.chapters: list[Chapter] = []
        self.characters: list[Character] = []
        self.lore_items: list[Lore] = []
        self.timeline_items: list[TimelineItem] = []

    async def load(self) -> None:
        if not self.project_id:
            return
        db = SessionLocal()
        try:
            self.project = db.query(Project).filter(Project.id == self.project_id).first()
            self.chapters = (
                db.query(Chapter)
                .filter(Chapter.project_id == self.project_id)
                .order_by(Chapter.scene_order.asc(), Chapter.created_at.asc())
                .all()
            )
            self.characters = (
                db.query(Character)
                .filter(Character.project_id == self.project_id)
                .order_by(Character.name.asc())
                .all()
            )
            self.lore_items = (
                db.query(Lore)
                .filter(Lore.project_id == self.project_id)
                .order_by(Lore.lore_type.asc(), Lore.name.asc())
                .all()
            )
            self.timeline_items = (
                db.query(TimelineItem)
                .filter(TimelineItem.project_id == self.project_id)
                .order_by(TimelineItem.created_at.asc())
                .all()
            )
        finally:
            db.close()

    def chapter_context(self, chapter_id: str | None, max_surrounding: int = 2) -> str:
        if not self.chapters:
            return ""
        target_idx = -1
        for idx, chapter in enumerate(self.chapters):
            if chapter.id == chapter_id:
                target_idx = idx
                break
        if target_idx == -1:
            selected = self.chapters[: max(3, max_surrounding * 2 + 1)]
        else:
            start = max(0, target_idx - max_surrounding)
            end = min(len(self.chapters), target_idx + max_surrounding + 1)
            selected = self.chapters[start:end]

        parts: list[str] = []
        for chapter in selected:
            marker = " [CURRENT]" if chapter.id == chapter_id else ""
            heading = chapter.title or f"Chương không tên"
            summary = _clean(chapter.summary)
            content = _clean(chapter.content)
            parts.append(
                f"## {heading}{marker}\n"
                + (f"{summary}\n" if summary else "")
                + (f"{content[:1200]}\n" if content else "")
            )
        return "\n".join(parts)

    def character_context(self) -> str:
        if not self.characters:
            return ""
        return "\n".join(
            _character_block(character) for character in self.characters[:40]
        )

    def lore_context(self) -> str:
        if not self.lore_items:
            return ""
        grouped: dict[str, list[Lore]] = {}
        order = []
        for item in self.lore_items:
            grouped.setdefault(item.lore_type, []).append(item)
            if item.lore_type not in order:
                order.append(item.lore_type)
        parts: list[str] = []
        for lore_type in order[:20]:
            items = grouped[lore_type]
            parts.append(f"### {lore_type}")
            for item in items[:25]:
                parts.append(_lore_block(item))
        return "\n".join(parts)

    def timeline_context(self) -> str:
        if not self.timeline_items:
            return ""
        return "\n".join(
            f"- {item.title} ({item.event_date or item.relative_order or '...'}): "
            + _clean(item.description)
            for item in self.timeline_items[:50]
        )

    def style_context(self) -> str:
        if not self.project:
            return ""
        return _clean(self.project.style_guide)


def _clean(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return text if text else ""


def _character_block(character: Character) -> str:
    lines = [f"- {character.name or 'Không tên'}"]
    if character.alias:
        lines.append(f"  Bí danh: {character.alias}")
    if character.role:
        lines.append(f"  Vai trò: {character.role}")
    if character.age:
        lines.append(f"  Tuổi: {character.age}")
    if character.personality:
        lines.append(f"  Tính cách: {character.personality}")
    if character.appearance:
        lines.append(f"  Ngoại hình: {character.appearance}")
    if character.goals:
        lines.append(f"  Mục tiêu: {character.goals}")
    if character.secrets:
        lines.append(f"  Bí mật: {character.secrets}")
    if character.relationships:
        lines.append(f"  Mối quan hệ: {json.dumps(character.relationships, ensure_ascii=False)}")
    if character.summary:
        lines.append(f"  Tóm tắt: {character.summary}")
    return "\n".join(lines)


def _lore_block(item: Lore) -> str:
    lines = [f"- {item.name} ({item.lore_type})"]
    if item.description:
        lines.append(f"  {item.description}")
    if item.tags:
        lines.append(f"  Tags: {', '.join(item.tags)}")
    return "\n".join(lines)
