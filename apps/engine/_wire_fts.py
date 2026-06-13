"""Wire FTS indexing hooks into chapter/lore/character routes."""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent


def patch(path: pathlib.Path, old: str, new: str, count: int = 1) -> bool:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        print(f"  SKIP {path.name}: pattern not found")
        return False
    path.write_text(text.replace(old, new, count), encoding="utf-8")
    return True


# ── chapters.py: remove from FTS on delete ───────────────────────────────────
patch(
    ROOT / "routes/chapters.py",
    "        db.delete(c)\n        db.commit()\n    finally:\n        db.close()",
    "        db.delete(c)\n        db.commit()\n"
    "        from services.search import remove_chapter\n"
    "        remove_chapter(chapter_id)\n"
    "    finally:\n        db.close()",
    1,
)
print("chapters.py OK")

# ── lore.py: index on create, remove on delete ───────────────────────────────
lore_path = ROOT / "routes/lore.py"
patch(
    lore_path,
    "        db.add(row)\n        db.commit()\n        db.refresh(row)\n        return _to_dict(row)",
    "        db.add(row)\n        db.commit()\n        db.refresh(row)\n"
    "        from services.search import index_lore\n"
    "        index_lore(row.id, row.project_id or '', row.name, row.description or '')\n"
    "        return _to_dict(row)",
    1,
)
patch(
    lore_path,
    "        db.delete(row)\n        db.commit()\n    finally:\n        db.close()",
    "        db.delete(row)\n        db.commit()\n"
    "        from services.search import remove_lore\n"
    "        remove_lore(lore_id)\n"
    "    finally:\n        db.close()",
    1,
)
print("lore.py OK")

# ── characters.py: index on create, remove on delete ─────────────────────────
chars_path = ROOT / "routes/characters.py"
patch(
    chars_path,
    "        c = Character(id=str(uuid.uuid4()), **payload.model_dump())\n"
    "        db.add(c)\n        db.commit()\n        db.refresh(c)\n        return _to_dict(c)",
    "        c = Character(id=str(uuid.uuid4()), **payload.model_dump())\n"
    "        db.add(c)\n        db.commit()\n        db.refresh(c)\n"
    "        from services.search import index_character\n"
    "        index_character(c.id, c.project_id or '', c.name,\n"
    "                        c.personality or '', c.goals or '', c.notes or '')\n"
    "        return _to_dict(c)",
    1,
)
patch(
    chars_path,
    "        db.delete(c)\n        db.commit()\n    finally:\n        db.close()",
    "        db.delete(c)\n        db.commit()\n"
    "        from services.search import remove_character\n"
    "        remove_character(character_id)\n"
    "    finally:\n        db.close()",
    1,
)
print("characters.py OK")
print("Done.")
