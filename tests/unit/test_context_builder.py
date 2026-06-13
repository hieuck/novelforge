"""Unit tests for services/context/builder.py"""
from __future__ import annotations
import sys, pathlib, asyncio
ENGINE_DIR = pathlib.Path(__file__).resolve().parent.parent.parent / "apps" / "engine"
sys.path.insert(0, str(ENGINE_DIR))
from fastapi.testclient import TestClient
from app import app
client = TestClient(app)

def _proj(t="CtxP"): return client.post("/api/projects/", json={"title": t}).json()["id"]
def _ch(pid, t="C", c="dragon roars"): return client.post("/api/chapters/", json={"project_id": pid, "title": t, "content": c}).json()["id"]
def _char(pid, n="Aria"): return client.post("/api/characters/", json={"project_id": pid, "name": n, "role": "hero"}).json()["id"]
def _lore(pid, n="Eld", tp="location"): return client.post("/api/lore/", json={"project_id": pid, "name": n, "lore_type": tp}).json()["id"]
def _tl(pid, t="War"): return client.post("/api/timeline/", json={"project_id": pid, "title": t, "event_date": "Y300"}).json()["id"]
def _ctx(pid):
    from services.context.builder import ProjectContext
    ctx = ProjectContext(pid); asyncio.get_event_loop().run_until_complete(ctx.load()); return ctx

def test_context_loads_all():
    pid = _proj(); _ch(pid); _char(pid); _lore(pid); _tl(pid)
    ctx = _ctx(pid)
    assert len(ctx.chapters)==1 and len(ctx.characters)==1 and len(ctx.lore_items)==1 and len(ctx.timeline_items)==1

def test_context_empty_project():
    ctx = _ctx(_proj("Empty"))
    assert ctx.chapters == [] and ctx.characters == []

def test_context_nonexistent_id():
    ctx = _ctx("bad-id")
    assert ctx.project is None and ctx.chapters == []

def test_context_none_id():
    from services.context.builder import ProjectContext
    ctx = ProjectContext(None); asyncio.get_event_loop().run_until_complete(ctx.load())
    assert ctx.chapters == []

def test_chapter_context_current_marker():
    pid = _proj(); cid = _ch(pid, "Battle", "Swords clashed.")
    ctx = _ctx(pid)
    assert "[CURRENT]" in ctx.chapter_context(cid)

def test_chapter_context_has_title():
    pid = _proj(); cid = _ch(pid, "The Great Battle", "content")
    ctx = _ctx(pid)
    assert "The Great Battle" in ctx.chapter_context(cid)

def test_chapter_context_unknown_id_returns_str():
    pid = _proj(); _ch(pid)
    ctx = _ctx(pid)
    assert isinstance(ctx.chapter_context("unknown"), str)

def test_chapter_context_empty_project():
    ctx = _ctx(_proj())
    assert ctx.chapter_context(None) == ""

def test_character_context_name():
    pid = _proj(); _char(pid, "Kael")
    assert "Kael" in _ctx(pid).character_context()

def test_character_context_empty():
    assert _ctx(_proj()).character_context() == ""

def test_character_context_multiple():
    pid = _proj()
    for n in ["Aria", "Kael", "Zara"]: _char(pid, n)
    r = _ctx(pid).character_context()
    assert "Aria" in r and "Kael" in r and "Zara" in r

def test_lore_context_name():
    pid = _proj(); _lore(pid, "Eldoria")
    assert "Eldoria" in _ctx(pid).lore_context()

def test_lore_context_empty():
    assert _ctx(_proj()).lore_context() == ""

def test_timeline_context_event():
    pid = _proj(); _tl(pid, "The Great Flood")
    assert "The Great Flood" in _ctx(pid).timeline_context()

def test_style_context_from_project():
    pid = _proj()
    client.patch(f"/api/projects/{pid}", json={"style_guide": "first person tense"})
    assert "first person" in _ctx(pid).style_context()

def test_style_context_empty_by_default():
    assert _ctx(_proj()).style_context() == ""
