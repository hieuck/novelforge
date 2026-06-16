"""
Full-text search service using SQLite FTS5.

Creates virtual FTS tables alongside the main tables and provides
a clean interface so it can be swapped for a vector DB later.
"""
from __future__ import annotations

import logging
import sqlite3
from typing import Any

from db.base import engine

logger = logging.getLogger("novelforge.search")


def _conn() -> sqlite3.Connection:
    con = engine.raw_connection()
    con.row_factory = sqlite3.Row
    return con


_SETUP_SQL = """
CREATE VIRTUAL TABLE IF NOT EXISTS fts_chapters USING fts5(
    chapter_id UNINDEXED,
    project_id UNINDEXED,
    title,
    content,
    tokenize = "unicode61"
);
CREATE VIRTUAL TABLE IF NOT EXISTS fts_lore USING fts5(
    lore_id UNINDEXED,
    project_id UNINDEXED,
    name,
    description,
    tokenize = "unicode61"
);
CREATE VIRTUAL TABLE IF NOT EXISTS fts_characters USING fts5(
    character_id UNINDEXED,
    project_id UNINDEXED,
    name,
    personality,
    goals,
    notes,
    tokenize = "unicode61"
);
"""


def init_fts() -> None:
    """Create FTS5 virtual tables if they don't exist. Call once on startup."""
    try:
        con = _conn()
        con.executescript(_SETUP_SQL)
        con.commit()
        con.close()
        logger.info("FTS5 tables initialised")
    except Exception as exc:
        logger.error("FTS init failed: %s", exc)


def index_chapter(chapter_id: str, project_id: str, title: str, content: str) -> None:
    try:
        con = _conn()
        con.execute("DELETE FROM fts_chapters WHERE chapter_id = ?", (chapter_id,))
        con.execute(
            "INSERT INTO fts_chapters(chapter_id, project_id, title, content) VALUES (?,?,?,?)",
            (chapter_id, project_id, title or "", content or ""),
        )
        con.commit()
        con.close()
    except Exception as exc:
        logger.warning("FTS index chapter failed: %s", exc)


def index_lore(lore_id: str, project_id: str, name: str, description: str) -> None:
    try:
        con = _conn()
        con.execute("DELETE FROM fts_lore WHERE lore_id = ?", (lore_id,))
        con.execute(
            "INSERT INTO fts_lore(lore_id, project_id, name, description) VALUES (?,?,?,?)",
            (lore_id, project_id, name or "", description or ""),
        )
        con.commit()
        con.close()
    except Exception as exc:
        logger.warning("FTS index lore failed: %s", exc)


def index_character(
    character_id: str, project_id: str,
    name: str, personality: str, goals: str, notes: str,
) -> None:
    try:
        con = _conn()
        con.execute("DELETE FROM fts_characters WHERE character_id = ?", (character_id,))
        con.execute(
            "INSERT INTO fts_characters(character_id, project_id, name, personality, goals, notes) "
            "VALUES (?,?,?,?,?,?)",
            (character_id, project_id, name or "", personality or "", goals or "", notes or ""),
        )
        con.commit()
        con.close()
    except Exception as exc:
        logger.warning("FTS index character failed: %s", exc)


def remove_chapter(chapter_id: str) -> None:
    try:
        con = _conn()
        con.execute("DELETE FROM fts_chapters WHERE chapter_id = ?", (chapter_id,))
        con.commit()
        con.close()
    except Exception as exc:
        logger.warning("FTS remove chapter failed: %s", exc)


def remove_lore(lore_id: str) -> None:
    try:
        con = _conn()
        con.execute("DELETE FROM fts_lore WHERE lore_id = ?", (lore_id,))
        con.commit()
        con.close()
    except Exception as exc:
        logger.warning("FTS remove lore failed: %s", exc)


def remove_character(character_id: str) -> None:
    try:
        con = _conn()
        con.execute("DELETE FROM fts_characters WHERE character_id = ?", (character_id,))
        con.commit()
        con.close()
    except Exception as exc:
        logger.warning("FTS remove character failed: %s", exc)


def _sanitize_fts_query(query: str) -> str:
    """Make user input safe for FTS5 MATCH expression."""
    q = query.strip()
    fts_operators = {"AND", "OR", "NOT", "NEAR"}
    has_operator = any(op in q.upper().split() for op in fts_operators)
    if has_operator or '"' in q or "*" in q:
        return q
    return f'"{q.replace(chr(34), " ")}"'


def search_project(project_id: str, query: str, limit: int = 20) -> list[dict[str, Any]]:
    """Search chapters, lore, and characters for a project. Returns ranked results."""
    if not query or not query.strip():
        return []
    safe_query = _sanitize_fts_query(query)
    results: list[dict[str, Any]] = []

    try:
        con = _conn()

        # Each table gets its own try/except so a bad FTS expression falls back to LIKE
        try:
            rows = con.execute(
                "SELECT chapter_id AS id, title,"
                " snippet(fts_chapters,3,'<b>','</b>','...',20) AS excerpt,"
                " 'chapter' AS kind, rank"
                " FROM fts_chapters WHERE project_id=? AND fts_chapters MATCH ?"
                " ORDER BY rank LIMIT ?",
                (project_id, safe_query, limit),
            ).fetchall()
            results.extend(dict(r) for r in rows)
        except sqlite3.OperationalError:
            rows = con.execute(
                "SELECT chapter_id AS id, title, '' AS excerpt, 'chapter' AS kind, 0 AS rank"
                " FROM fts_chapters WHERE project_id=? AND (title LIKE ? OR content LIKE ?) LIMIT ?",
                (project_id, f"%{query}%", f"%{query}%", limit),
            ).fetchall()
            results.extend(dict(r) for r in rows)

        try:
            rows = con.execute(
                "SELECT lore_id AS id, name AS title,"
                " snippet(fts_lore,3,'<b>','</b>','...',20) AS excerpt,"
                " 'lore' AS kind, rank"
                " FROM fts_lore WHERE project_id=? AND fts_lore MATCH ?"
                " ORDER BY rank LIMIT ?",
                (project_id, safe_query, limit),
            ).fetchall()
            results.extend(dict(r) for r in rows)
        except sqlite3.OperationalError:
            rows = con.execute(
                "SELECT lore_id AS id, name AS title, '' AS excerpt, 'lore' AS kind, 0 AS rank"
                " FROM fts_lore WHERE project_id=? AND (name LIKE ? OR description LIKE ?) LIMIT ?",
                (project_id, f"%{query}%", f"%{query}%", limit),
            ).fetchall()
            results.extend(dict(r) for r in rows)

        try:
            rows = con.execute(
                "SELECT character_id AS id, name AS title,"
                " snippet(fts_characters,2,'<b>','</b>','...',20) AS excerpt,"
                " 'character' AS kind, rank"
                " FROM fts_characters WHERE project_id=? AND fts_characters MATCH ?"
                " ORDER BY rank LIMIT ?",
                (project_id, safe_query, limit),
            ).fetchall()
            results.extend(dict(r) for r in rows)
        except sqlite3.OperationalError:
            rows = con.execute(
                "SELECT character_id AS id, name AS title, '' AS excerpt, 'character' AS kind, 0 AS rank"
                " FROM fts_characters WHERE project_id=? AND (name LIKE ? OR goals LIKE ?) LIMIT ?",
                (project_id, f"%{query}%", f"%{query}%", limit),
            ).fetchall()
            results.extend(dict(r) for r in rows)

        con.close()
    except Exception as exc:
        logger.error("FTS search failed query=%r: %s", query, exc)

    results.sort(key=lambda r: r.get("rank") or 0)
    return results[:limit]
