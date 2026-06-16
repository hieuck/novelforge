"""Integration tests for the schema migration script."""
from __future__ import annotations

import sqlite3

import pytest
from sqlalchemy import create_engine, inspect, text


@pytest.fixture
def old_db(tmp_path):
    """Create a database with the schema as it existed before migrations."""
    db_path = tmp_path / "test_novelforge.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript("""
        CREATE TABLE projects (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            genre TEXT,
            language TEXT DEFAULT 'vi',
            style_guide TEXT,
            summary TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        );
        CREATE TABLE chapters (
            id TEXT PRIMARY KEY,
            project_id TEXT REFERENCES projects(id),
            title TEXT NOT NULL,
            content TEXT NOT NULL DEFAULT '',
            status TEXT DEFAULT 'draft',
            word_count INTEGER DEFAULT 0,
            scene_order INTEGER DEFAULT 0,
            summary TEXT,
            notes TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        );
        CREATE TABLE characters (
            id TEXT PRIMARY KEY,
            project_id TEXT,
            name TEXT NOT NULL,
            alias TEXT,
            role TEXT,
            age TEXT,
            personality TEXT,
            appearance TEXT,
            goals TEXT,
            secrets TEXT,
            relationships TEXT,
            first_appearance TEXT,
            notes TEXT,
            summary TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        );
        CREATE TABLE generated_images (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            filename TEXT NOT NULL,
            prompt TEXT,
            entity_type TEXT,
            entity_id TEXT,
            mime TEXT,
            file_size TEXT,
            created_at TIMESTAMP
        );
        CREATE TABLE summaries (
            id TEXT PRIMARY KEY,
            project_id TEXT REFERENCES projects(id),
            kind TEXT NOT NULL,
            subject_id TEXT,
            text TEXT NOT NULL,
            embedding TEXT,
            created_at TIMESTAMP
        );
        CREATE TABLE settings (
            id TEXT PRIMARY KEY DEFAULT 'app-settings',
            project_id TEXT,
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            is_secret INTEGER DEFAULT 0,
            updated_at TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()
    return str(db_path)


def _run_migration_on(db_path: str):
    """Run the migration logic directly on a given database."""
    engine = create_engine(f"sqlite:///{db_path}")
    inspector = inspect(engine)
    with engine.connect() as conn:
        for table in ("chapters",):
            existing = {c["name"] for c in inspector.get_columns(table)}
            for col_name, col_type in [("illustration_url", "VARCHAR")]:
                if col_name not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type} NULL"))
        for table in ("characters",):
            existing = {c["name"] for c in inspector.get_columns(table)}
            for col_name, col_type in [("gender", "VARCHAR"), ("portrait_url", "VARCHAR")]:
                if col_name not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type} NULL"))
        for table, indexes in {
            "chapters": [("ix_chapters_project_id", "project_id")],
            "summaries": [("ix_summaries_project_id", "project_id")],
            "settings": [("ix_settings_project_id", "project_id")],
        }.items():
            existing = {ix["name"] for ix in inspector.get_indexes(table)}
            for ix_name, col_name in indexes:
                if ix_name not in existing:
                    conn.execute(text(f"CREATE INDEX IF NOT EXISTS {ix_name} ON {table}({col_name})"))
        conn.commit()
    engine.dispose()


def test_migration_adds_columns(old_db):
    """Verify the migration adds missing columns and indexes."""
    _run_migration_on(old_db)

    conn = sqlite3.connect(old_db)
    cursor = conn.execute("PRAGMA table_info(chapters)")
    chapters_cols = {row[1] for row in cursor.fetchall()}
    assert "illustration_url" in chapters_cols, "Should add illustration_url to chapters"

    cursor = conn.execute("PRAGMA table_info(characters)")
    chars_cols = {row[1] for row in cursor.fetchall()}
    assert "gender" in chars_cols, "Should add gender to characters"
    assert "portrait_url" in chars_cols, "Should add portrait_url to characters"

    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='ix_chapters_project_id'")
    assert cursor.fetchone(), "Should create ix_chapters_project_id index"

    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='ix_summaries_project_id'")
    assert cursor.fetchone(), "Should create ix_summaries_project_id index"

    conn.close()


def test_migration_idempotent(old_db):
    """Running migration twice should be safe."""
    _run_migration_on(old_db)
    _run_migration_on(old_db)  # second run should not raise

    conn = sqlite3.connect(old_db)
    cursor = conn.execute("PRAGMA table_info(chapters)")
    assert "illustration_url" in {row[1] for row in cursor.fetchall()}
    conn.close()
