"""Schema migration: add columns added after initial release."""

import os
import shutil
import sys
from datetime import UTC, datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from db.base import engine
from sqlalchemy import inspect, text

ADD_COLUMNS: dict[str, list[tuple[str, str]]] = {
    "chapters": [
        ("illustration_url", "VARCHAR"),
    ],
    "characters": [
        ("gender", "VARCHAR"),
        ("portrait_url", "VARCHAR"),
    ],
    "projects": [
        ("daily_goal", "INTEGER"),
    ],
}

CREATE_TABLES: list[str] = [
    """
    CREATE TABLE IF NOT EXISTS writing_sessions (
        id VARCHAR PRIMARY KEY,
        project_id VARCHAR NOT NULL,
        date DATE NOT NULL,
        words_added INTEGER NOT NULL DEFAULT 0,
        words_total INTEGER NOT NULL DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """,
]

ADD_INDEXES: dict[str, list[tuple[str, str]]] = {
    "chapters": [
        ("ix_chapters_project_id", "project_id"),
    ],
    "summaries": [
        ("ix_summaries_project_id", "project_id"),
    ],
    "settings": [
        ("ix_settings_project_id", "project_id"),
    ],
    "writing_sessions": [
        ("ix_writing_sessions_project_id", "project_id"),
        ("ix_writing_sessions_date", "date"),
    ],
}


def _auto_backup():
    """Create a pre-migration backup if the DB has pending changes."""
    from db.paths import get_data_dir

    db_path = get_data_dir() / "novelforge.db"
    if not db_path.exists():
        return
    backup_dir = get_data_dir() / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"pre_migration_{ts}.db"
    shutil.copy2(db_path, backup_path)
    print(f"  [backup] pre-migration backup saved: {backup_path.name}")


def run():
    _auto_backup()
    inspector = inspect(engine)
    with engine.connect() as conn:
        for stmt in CREATE_TABLES:
            conn.execute(text(stmt))
            print("  + ensured table exists")
        for table, cols in ADD_COLUMNS.items():
            existing = {c["name"] for c in inspector.get_columns(table)}
            for col_name, col_type in cols:
                if col_name not in existing:
                    stmt = text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type} NULL")
                    conn.execute(stmt)
                    print(f"  + added {table}.{col_name}")
                else:
                    print(f"  = {table}.{col_name} already exists")
        for table, indexes in ADD_INDEXES.items():
            existing = {ix["name"] for ix in inspector.get_indexes(table)}
            for ix_name, col_name in indexes:
                if ix_name not in existing:
                    conn.execute(text(f"CREATE INDEX IF NOT EXISTS {ix_name} ON {table}({col_name})"))
                    print(f"  + added index {ix_name} on {table}({col_name})")
                else:
                    print(f"  = index {ix_name} already exists")
        conn.commit()
    print("Migration complete.")


if __name__ == "__main__":
    run()
