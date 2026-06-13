"""
NovelForge backend tests.

Run from repo root:
    cd apps/engine
    .venv\\Scripts\\pip install pytest httpx
    .venv\\Scripts\\pytest ../../tests/test_engine.py -v
"""
import sys
import pathlib
import uuid

ENGINE_DIR = pathlib.Path(__file__).resolve().parent.parent / "apps" / "engine"
sys.path.insert(0, str(ENGINE_DIR))

import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def make_project(title: str | None = None) -> str:
    r = client.post("/api/projects/", json={"title": title or f"P-{uuid.uuid4().hex[:6]}"})
    assert r.status_code == 201
    return r.json()["id"]


def make_chapter(project_id: str, title: str = "Ch1", content: str = "hello world") -> str:
    r = client.post("/api/chapters/", json={
        "project_id": project_id, "title": title, "content": content,
    })
    assert r.status_code == 201
    return r.json()["id"]


# ── health ────────────────────────────────────────────────────────────────────

def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ── projects ──────────────────────────────────────────────────────────────────

def test_create_project():
    r = client.post("/api/projects/", json={"title": "My Novel", "genre": "Fantasy", "language": "vi"})
    assert r.status_code == 201
    d = r.json()
    assert d["title"] == "My Novel"
    assert "id" in d


def test_list_projects():
    make_project()
    r = client.get("/api/projects/")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_project_not_found():
    r = client.get("/api/projects/does-not-exist")
    assert r.status_code == 404


def test_update_project():
    pid = make_project()
    r = client.patch(f"/api/projects/{pid}", json={"title": "Updated", "genre": "SciFi"})
    assert r.status_code == 200
    assert r.json()["title"] == "Updated"


def test_delete_project():
    pid = make_project()
    assert client.delete(f"/api/projects/{pid}").status_code == 204
    assert client.get(f"/api/projects/{pid}").status_code == 404


# ── chapters ──────────────────────────────────────────────────────────────────

def test_create_chapter_word_count():
    pid = make_project()
    r = client.post("/api/chapters/", json={
        "project_id": pid, "title": "Chapter 1",
        "content": "Once upon a time in a land far away.",
    })
    assert r.status_code == 201
    assert r.json()["word_count"] == 9


def test_list_chapters():
    pid = make_project()
    make_chapter(pid, "Ch1")
    make_chapter(pid, "Ch2")
    r = client.get(f"/api/projects/{pid}/chapters")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_update_chapter_recalculates_word_count():
    pid = make_project()
    cid = make_chapter(pid, content="one two three")
    r = client.patch(f"/api/chapters/{cid}", json={"content": "a b c d e"})
    assert r.json()["word_count"] == 5


def test_delete_chapter():
    pid = make_project()
    cid = make_chapter(pid)
    assert client.delete(f"/api/chapters/{cid}").status_code == 204
    assert client.get(f"/api/chapters/{cid}").status_code == 404


# ── characters ────────────────────────────────────────────────────────────────

def test_character_crud():
    pid = make_project()
    r = client.post("/api/characters/", json={
        "project_id": pid, "name": "Aria", "role": "protagonist",
        "age": "22", "goals": "Save the world",
    })
    assert r.status_code == 201
    cid = r.json()["id"]

    assert len(client.get(f"/api/projects/{pid}/characters").json()) == 1

    r3 = client.patch(f"/api/characters/{cid}", json={"age": "23"})
    assert r3.json()["age"] == "23"

    assert client.delete(f"/api/characters/{cid}").status_code == 204
    assert client.get(f"/api/characters/{cid}").status_code == 404


# ── lore ──────────────────────────────────────────────────────────────────────

def test_lore_crud():
    pid = make_project()
    r = client.post("/api/lore/", json={
        "project_id": pid, "lore_type": "location",
        "name": "Eldoria", "description": "A magical kingdom",
        "tags": ["magic", "kingdom"],
    })
    assert r.status_code == 201
    lid = r.json()["id"]

    assert len(client.get(f"/api/projects/{pid}/lore").json()) == 1

    r3 = client.patch(f"/api/lore/{lid}", json={"description": "Updated"})
    assert "Updated" in r3.json()["description"]

    assert client.delete(f"/api/lore/{lid}").status_code == 204


# ── timeline ──────────────────────────────────────────────────────────────────

def test_timeline_crud():
    pid = make_project()
    r = client.post("/api/timeline/", json={
        "project_id": pid, "title": "The Great War",
        "event_date": "Year 300", "description": "War begins",
    })
    assert r.status_code == 201
    tid = r.json()["id"]

    assert len(client.get(f"/api/projects/{pid}/timeline").json()) == 1

    client.patch(f"/api/timeline/{tid}", json={"description": "The war that ended an age"})
    assert client.delete(f"/api/timeline/{tid}").status_code == 204


# ── settings ──────────────────────────────────────────────────────────────────

def test_settings_defaults():
    r = client.get("/api/settings/current")
    assert r.status_code == 200
    assert "provider" in r.json()
    assert "model" in r.json()


def test_settings_save():
    r = client.post("/api/settings/current", json={
        "provider": "openai_compat",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
        "temperature": 0.8,
        "max_tokens": 4096,
    })
    assert r.status_code == 200
    assert r.json()["provider"] == "openai_compat"


# ── export ────────────────────────────────────────────────────────────────────

def test_export_markdown():
    pid = make_project("Export Novel")
    make_chapter(pid, "Chapter One", "The sun rose over the mountains.")
    r = client.post("/api/export", json={"project_id": pid, "fmt": "md"})
    assert r.status_code == 200
    assert "text/markdown" in r.headers.get("content-type", "")
    assert "Chapter One" in r.text
    assert "The sun rose" in r.text


def test_export_html():
    pid = make_project("HTML Novel")
    make_chapter(pid, "Prologue", "In the beginning there was darkness.")
    r = client.post("/api/export", json={"project_id": pid, "fmt": "html"})
    assert r.status_code == 200
    assert "<!DOCTYPE html>" in r.text
    assert "HTML Novel" in r.text


def test_export_zip():
    pid = make_project()
    make_chapter(pid)
    r = client.post("/api/export", json={"project_id": pid, "fmt": "zip"})
    assert r.status_code == 200
    assert "application/zip" in r.headers.get("content-type", "")


def test_export_unknown_format():
    pid = make_project()
    r = client.post("/api/export", json={"project_id": pid, "fmt": "docx"})
    assert r.status_code == 400


# ── import ────────────────────────────────────────────────────────────────────

def test_import_single():
    pid = make_project()
    r = client.post("/api/import", json={
        "project_id": pid,
        "content": "This is imported content.",
        "filename": "my_chapter.md",
        "mode": "single",
    })
    assert r.status_code == 200
    assert r.json()["imported"] == 1
    assert r.json()["chapters"][0]["title"] == "my_chapter"


def test_import_split_h2():
    pid = make_project()
    content = "# My Novel\n\n## Chapter A\nContent A.\n\n## Chapter B\nContent B.\n"
    r = client.post("/api/import", json={
        "project_id": pid, "content": content,
        "filename": "novel.md", "mode": "split_h2",
    })
    assert r.status_code == 200
    d = r.json()
    assert d["imported"] == 2
    titles = [c["title"] for c in d["chapters"]]
    assert "Chapter A" in titles
    assert "Chapter B" in titles


# ── context builder ───────────────────────────────────────────────────────────

def test_context_builder():
    import asyncio
    from services.context.builder import ProjectContext

    pid = make_project("Context Test")
    make_chapter(pid, "Opening", "The dragon appeared at dawn.")
    client.post("/api/characters/", json={
        "project_id": pid, "name": "Kael", "role": "warrior"
    })
    client.post("/api/lore/", json={
        "project_id": pid, "lore_type": "magic",
        "name": "Dragon Fire", "description": "Eternal magical flame"
    })

    ctx = ProjectContext(pid)
    asyncio.get_event_loop().run_until_complete(ctx.load())

    assert len(ctx.chapters) == 1
    assert len(ctx.characters) == 1
    assert len(ctx.lore_items) == 1
    assert "Kael" in ctx.character_context()
    assert "Dragon Fire" in ctx.lore_context()
    assert "dragon" in ctx.chapter_context(ctx.chapters[0].id).lower()


# ── word count edge cases ─────────────────────────────────────────────────────

def test_word_count_empty():
    pid = make_project()
    r = client.post("/api/chapters/", json={"project_id": pid, "title": "Empty", "content": ""})
    assert r.json()["word_count"] == 0


def test_word_count_unicode():
    pid = make_project()
    r = client.post("/api/chapters/", json={
        "project_id": pid, "title": "VN",
        "content": "Ngày xưa có một chàng trai dũng cảm"
    })
    assert r.json()["word_count"] == 8  # 8 space-separated tokens
