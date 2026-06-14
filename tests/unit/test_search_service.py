"""Unit tests for services/search.py - FTS5 search service."""
from __future__ import annotations
import sqlite3, sys, pathlib, pytest

ENGINE_DIR = pathlib.Path(__file__).resolve().parent.parent.parent / "apps" / "engine"
sys.path.insert(0, str(ENGINE_DIR))

@pytest.fixture()
def tmp_db(tmp_path, monkeypatch):
    db_file = tmp_path / "test.db"
    import services.search as mod
    monkeypatch.setattr(mod, "_DB_PATH", db_file)
    mod.init_fts()
    return db_file, mod

def test_init_fts_creates_tables(tmp_db):
    db_file, _ = tmp_db
    con = sqlite3.connect(str(db_file))
    tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    con.close()
    assert "fts_chapters" in tables and "fts_lore" in tables and "fts_characters" in tables

def test_init_fts_idempotent(tmp_db):
    db_file, mod = tmp_db
    mod.init_fts(); mod.init_fts()
    con = sqlite3.connect(str(db_file))
    count = con.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='fts_chapters'").fetchone()[0]
    con.close()
    assert count == 1

def test_index_chapter_searchable(tmp_db):
    _, mod = tmp_db
    mod.index_chapter("ch1", "proj1", "Opening Scene", "The hero arrives at dawn.")
    assert any(r["id"] == "ch1" for r in mod.search_project("proj1", "hero", limit=5))

def test_index_chapter_update_no_duplicate(tmp_db):
    db_file, mod = tmp_db
    mod.index_chapter("ch1", "proj1", "Title", "original content")
    mod.index_chapter("ch1", "proj1", "Title Updated", "completely new content")
    con = sqlite3.connect(str(db_file))
    count = con.execute("SELECT count(*) FROM fts_chapters WHERE chapter_id='ch1'").fetchone()[0]
    con.close()
    assert count == 1

def test_remove_chapter(tmp_db):
    _, mod = tmp_db
    mod.index_chapter("ch2", "proj1", "Deleted Chapter", "some text here")
    mod.remove_chapter("ch2")
    assert not any(r["id"] == "ch2" for r in mod.search_project("proj1", "Deleted Chapter", limit=5))

def test_remove_nonexistent_no_error(tmp_db):
    _, mod = tmp_db
    mod.remove_chapter("ghost"); mod.remove_lore("ghost"); mod.remove_character("ghost")

def test_index_lore_searchable(tmp_db):
    _, mod = tmp_db
    mod.index_lore("lore1", "proj1", "Dragon Fire", "An ancient magical flame.")
    assert any(r["id"] == "lore1" for r in mod.search_project("proj1", "dragon", limit=5))

def test_index_character_searchable(tmp_db):
    _, mod = tmp_db
    mod.index_character("char1", "proj1", "Aria", "Brave", "Save the world", "")
    assert any(r["id"] == "char1" for r in mod.search_project("proj1", "Aria", limit=5))

def test_search_empty_returns_empty(tmp_db):
    _, mod = tmp_db
    assert mod.search_project("proj1", "") == []
    assert mod.search_project("proj1", "   ") == []

def test_search_project_isolation(tmp_db):
    _, mod = tmp_db
    mod.index_chapter("ch_a", "proj_a", "Secret of Eldoria", "The dragon sleeps.")
    assert mod.search_project("proj_b", "Eldoria", limit=5) == []

def test_search_returns_both_kinds(tmp_db):
    _, mod = tmp_db
    mod.index_chapter("ch1", "proj1", "The Dragon Chapter", "Fire everywhere.")
    mod.index_lore("l1", "proj1", "Dragon Lore", "Dragons are ancient beings.")
    kinds = {r["kind"] for r in mod.search_project("proj1", "dragon", limit=10)}
    assert "chapter" in kinds and "lore" in kinds

def test_search_result_has_excerpt(tmp_db):
    _, mod = tmp_db
    mod.index_chapter("ch1", "proj1", "Title", "Some searchable content here.")
    results = mod.search_project("proj1", "searchable", limit=5)
    assert len(results) > 0 and "excerpt" in results[0]

def test_search_limit_respected(tmp_db):
    _, mod = tmp_db
    for i in range(15):
        mod.index_chapter(f"ch{i}", "proj1", f"Chapter {i}", f"Content about dragons {i}")
    assert len(mod.search_project("proj1", "dragons", limit=5)) <= 5

def test_search_kind_field_is_chapter(tmp_db):
    _, mod = tmp_db
    mod.index_chapter("ch1", "proj1", "Test", "hello world")
    assert mod.search_project("proj1", "hello", limit=5)[0]["kind"] == "chapter"

def test_search_plain_text_no_error(tmp_db):
    _, mod = tmp_db
    mod.index_chapter("ch1", "proj1", "Title", "Aria fights the dragon king.")
    mod.search_project("proj1", "dragon king", limit=5)

def test_search_quoted_query_no_error(tmp_db):
    _, mod = tmp_db
    mod.index_chapter("ch1", "proj1", "Title", "The quick brown fox")
    result = mod.search_project("proj1", '"quick brown"', limit=5)
    assert isinstance(result, list)

def test_search_multiple_tables(tmp_db):
    _, mod = tmp_db
    mod.index_chapter("ch1", "proj1", "Sword of Destiny", "content")
    mod.index_lore("l1", "proj1", "Sword Legend", "ancient blade")
    mod.index_character("c1", "proj1", "Swordmaster", "skilled", "master the sword", "")
    results = mod.search_project("proj1", "sword", limit=20)
    assert len(results) >= 2
