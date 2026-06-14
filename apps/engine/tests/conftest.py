"""Shared test fixtures for NovelForge engine tests."""
from __future__ import annotations

import os
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure the engine package root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.base import Base
from db.session import SessionLocal as _RealSession


# ── In-memory SQLite for tests ────────────────────────────────────────────────

TEST_DB_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def setup_db(monkeypatch):
    """Create all tables in the in-memory DB and patch SessionLocal for every test."""
    Base.metadata.create_all(bind=test_engine)

    # Patch SessionLocal everywhere it is imported
    import db.session as session_mod
    import db.base as base_mod

    monkeypatch.setattr(session_mod, "SessionLocal", TestingSession)
    monkeypatch.setattr(base_mod, "engine", test_engine)

    # Also patch in every route/service module that cached the import
    for mod_name in list(sys.modules):
        mod = sys.modules[mod_name]
        if hasattr(mod, "SessionLocal") and mod.SessionLocal is _RealSession:
            monkeypatch.setattr(mod, "SessionLocal", TestingSession)

    yield

    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    """FastAPI test client with a fresh app instance."""
    # Patch search init so it doesn't touch real filesystem
    import services.search as search_mod
    from unittest.mock import patch

    with patch.object(search_mod, "init_fts", return_value=None), \
         patch.object(search_mod, "index_chapter", return_value=None), \
         patch.object(search_mod, "index_lore", return_value=None), \
         patch.object(search_mod, "index_character", return_value=None), \
         patch.object(search_mod, "remove_chapter", return_value=None), \
         patch.object(search_mod, "remove_lore", return_value=None), \
         patch.object(search_mod, "remove_character", return_value=None):
        from app import create_app
        app = create_app()
        yield TestClient(app)
