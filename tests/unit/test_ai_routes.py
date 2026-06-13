"""Tests for routes/ai.py"""
from __future__ import annotations
import sys, pathlib
from unittest.mock import patch, AsyncMock, MagicMock
ENGINE_DIR = pathlib.Path(__file__).resolve().parent.parent.parent / "apps" / "engine"
sys.path.insert(0, str(ENGINE_DIR))
from fastapi.testclient import TestClient
from app import app
client = TestClient(app)
def _pid(): return client.post("/api/projects/", json={"title": "AI"}).json()["id"]
def _cid(pid): return client.post("/api/chapters/", json={"project_id": pid, "title": "C", "content": "The hero stood at the gate."}).json()["id"]
def _mock(text="AI result"): return patch("routes.ai.build_client", return_value=MagicMock(chat=AsyncMock(return_value=text)))

def test_ai_run_basic():
    with _mock("result"): r = client.post("/api/ai/run", json={"action": "continue", "text": "start"})
    assert r.status_code == 200 and r.json()["result"] == "result"

def test_ai_run_with_project():
    pid = _pid(); cid = _cid(pid)
    with _mock("cont"): r = client.post("/api/ai/run", json={"action": "continue", "project_id": pid, "chapter_id": cid, "text": "x"})
    assert r.status_code == 200

def test_ai_run_all_actions():
    for a in ["continue","rewrite","expand","shorten","dialogue","emotional","cinematic","grammar","summarize_chapter","summarize_project","continuity","plot_holes","next_scene","character","world","translate_vi_en","translate_en_vi","premise","outline"]:
        with _mock(f"out"): r = client.post("/api/ai/run", json={"action": a, "text": "t"})
        assert r.status_code == 200, f"{a} failed"

def test_ai_run_with_instruction():
    with _mock("instructed"): r = client.post("/api/ai/run", json={"action": "rewrite", "text": "orig", "instruction": "dramatic"})
    assert r.status_code == 200

def test_ai_run_empty_text():
    with _mock("ok"): r = client.post("/api/ai/run", json={"action": "premise"})
    assert r.status_code == 200

def test_ai_run_502_on_error():
    with patch("routes.ai.build_client", return_value=MagicMock(chat=AsyncMock(side_effect=Exception("timeout")))):
        r = client.post("/api/ai/run", json={"action": "continue", "text": "t"})
    assert r.status_code == 502

def test_ai_context_includes_character():
    pid = _pid(); client.post("/api/characters/", json={"project_id": pid, "name": "Zara", "role": "villain"})
    cap = {}
    async def cc(*, system, user): cap["s"] = system; return "ok"
    with patch("routes.ai.build_client", return_value=MagicMock(chat=cc)):
        client.post("/api/ai/run", json={"action": "continue", "project_id": pid, "text": "x"})
    assert "Zara" in cap.get("s", "")

def test_ai_context_includes_lore():
    pid = _pid(); client.post("/api/lore/", json={"project_id": pid, "name": "Shadow Realm", "lore_type": "location"})
    cap = {}
    async def cc(*, system, user): cap["s"] = system; return "ok"
    with patch("routes.ai.build_client", return_value=MagicMock(chat=cc)):
        client.post("/api/ai/run", json={"action": "continue", "project_id": pid, "text": "x"})
    assert "Shadow Realm" in cap.get("s", "")

def test_ai_context_includes_style_guide():
    pid = _pid(); client.patch(f"/api/projects/{pid}", json={"style_guide": "Write in second person."})
    cap = {}
    async def cc(*, system, user): cap["s"] = system; return "ok"
    with patch("routes.ai.build_client", return_value=MagicMock(chat=cc)):
        client.post("/api/ai/run", json={"action": "continue", "project_id": pid, "text": "x"})
    assert "second person" in cap.get("s", "")

def test_ai_context_chapter_in_prompt():
    pid = _pid(); cid = _cid(pid)
    cap = {}
    async def cc(*, system, user): cap["u"] = user; return "ok"
    with patch("routes.ai.build_client", return_value=MagicMock(chat=cc)):
        client.post("/api/ai/run", json={"action": "continue", "project_id": pid, "chapter_id": cid, "text": "x"})
    assert "hero" in cap.get("u", "").lower() or "gate" in cap.get("u", "").lower()

