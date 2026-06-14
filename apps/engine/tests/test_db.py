"""Tests for DB layer utilities."""
from __future__ import annotations

import os


def test_db_paths_default():
    """get_data_dir returns a reasonable default."""
    from db.paths import get_data_dir
    d = get_data_dir()
    assert d is not None
    assert d.exists()


def test_db_paths_env_override():
    """NOVELFORGE_DATA_DIR env var overrides default."""
    from db.paths import get_data_dir
    os.environ["NOVELFORGE_DATA_DIR"] = os.path.abspath(".")
    try:
        d = get_data_dir()
        assert d.exists()
    finally:
        del os.environ["NOVELFORGE_DATA_DIR"]


def test_db_session():
    """SessionLocal produces a working session."""
    from db.session import SessionLocal
    db = SessionLocal()
    try:
        from sqlalchemy import text
        r = db.execute(text("SELECT 1")).scalar()
        assert r == 1
    finally:
        db.close()
