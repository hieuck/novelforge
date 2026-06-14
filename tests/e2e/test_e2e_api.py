"""E2E tests - requires engine running at localhost:9000. Auto-skipped if not available."""
from __future__ import annotations
import sys, pathlib, pytest
ENGINE_DIR = pathlib.Path(__file__).resolve().parent.parent.parent / "apps" / "engine"
sys.path.insert(0, str(ENGINE_DIR))
try:
    import httpx; HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False
BASE = "http://127.0.0.1:9000/api"
TIMEOUT = 5.0
def _up():
    if not HAS_HTTPX: return False
    try: return httpx.get(f"{BASE}/health", timeout=2.0).status_code == 200
    except: return False
skip = pytest.mark.skipif(not _up(), reason="Engine not running at localhost:9000")

@skip
def test_e2e_health():
    r = httpx.get(f"{BASE}/health", timeout=TIMEOUT)
    assert r.status_code == 200 and r.json()["status"] == "ok"

@skip
def test_e2e_project_chapter_crud():
    c = httpx.Client(base_url=BASE, timeout=TIMEOUT)
    pid = c.post("/projects/", json={"title": "E2E Novel", "genre": "Fantasy"}).json()["id"]
    try:
        ch = c.post("/chapters/", json={"project_id": pid, "title": "Prologue", "content": "In a land far away"})
        assert ch.status_code == 201 and ch.json()["word_count"] == 5
        cid = ch.json()["id"]
        assert c.get(f"/chapters/{cid}").json()["title"] == "Prologue"
        upd = c.patch(f"/chapters/{cid}", json={"content": "Once upon a time in a land far away the adventure began."})
        assert upd.json()["word_count"] > 5
        assert len(c.get(f"/projects/{pid}/chapters").json()) == 1
    finally:
        c.delete(f"/projects/{pid}")

@skip
def test_e2e_character_workflow():
    c = httpx.Client(base_url=BASE, timeout=TIMEOUT)
    pid = c.post("/projects/", json={"title": "E2E CB"}).json()["id"]
    try:
        char = c.post("/characters/", json={"project_id": pid, "name": "Aria", "role": "hero", "age": "22"})
        assert char.status_code == 201
        cid = char.json()["id"]
        assert c.get(f"/projects/{pid}/characters").json()[0]["name"] == "Aria"
        assert c.patch(f"/characters/{cid}", json={"age": "23"}).json()["age"] == "23"
        c.delete(f"/characters/{cid}")
        assert c.get(f"/characters/{cid}").status_code == 404
    finally:
        c.delete(f"/projects/{pid}")

@skip
def test_e2e_lore_and_search():
    c = httpx.Client(base_url=BASE, timeout=TIMEOUT)
    pid = c.post("/projects/", json={"title": "E2E Lore"}).json()["id"]
    try:
        c.post("/lore/", json={"project_id": pid, "name": "Shadowgate Keep", "lore_type": "location", "description": "Ancient fortress"})
        c.post("/chapters/", json={"project_id": pid, "title": "The Fortress", "content": "Shadowgate loomed over the valley."})
        results = c.get(f"/projects/{pid}/search?q=Shadowgate&limit=10").json()
        assert len(results) >= 1
    finally:
        c.delete(f"/projects/{pid}")

@skip
def test_e2e_export_all_formats():
    c = httpx.Client(base_url=BASE, timeout=TIMEOUT)
    pid = c.post("/projects/", json={"title": "E2E Export"}).json()["id"]
    try:
        for i, t in enumerate(["Ch1", "Ch2", "Ch3"]):
            c.post("/chapters/", json={"project_id": pid, "title": t, "content": f"Content {i}.", "scene_order": i})
        md = c.post("/export", json={"project_id": pid, "fmt": "md"})
        assert md.status_code == 200 and "Ch1" in md.text
        html = c.post("/export", json={"project_id": pid, "fmt": "html"})
        assert "<!DOCTYPE html>" in html.text
        txt = c.post("/export", json={"project_id": pid, "fmt": "txt"})
        assert "E2E Export" in txt.text
    finally:
        c.delete(f"/projects/{pid}")

@skip
def test_e2e_settings_persist():
    c = httpx.Client(base_url=BASE, timeout=TIMEOUT)
    saved = c.post("/settings/current", json={"provider": "ollama", "base_url": "http://localhost:11434", "model": "gemma3:4b", "temperature": 0.7, "max_tokens": 2048})
    assert saved.json()["provider"] == "ollama"
    assert c.get("/settings/current").json()["model"] == "gemma3:4b"
    bad = c.post("/settings/test", json={"provider": "ollama", "base_url": "http://127.0.0.1:19999", "model": "x", "temperature": 0.7, "max_tokens": 100})
    assert bad.json()["ok"] == False

@skip
def test_e2e_import_markdown():
    c = httpx.Client(base_url=BASE, timeout=TIMEOUT)
    pid = c.post("/projects/", json={"title": "E2E Import"}).json()["id"]
    try:
        md = "# N\n\n## The Beginning\nContent one.\n\n## The End\nContent two.\n"
        r = c.post("/import", json={"project_id": pid, "content": md, "filename": "t.md", "mode": "split_h2"})
        assert r.status_code == 200 and r.json()["imported"] == 2
        titles = [x["title"] for x in r.json()["chapters"]]
        assert "The Beginning" in titles and "The End" in titles
    finally:
        c.delete(f"/projects/{pid}")

@skip
def test_e2e_jobs_lifecycle():
    c = httpx.Client(base_url=BASE, timeout=TIMEOUT)
    pid = c.post("/projects/", json={"title": "E2E Jobs"}).json()["id"]
    try:
        job = c.post("/jobs", json={"project_id": pid, "kind": "outline"})
        assert job.status_code == 201 and job.json()["status"] == "queued"
        jid = job.json()["id"]
        assert c.get(f"/jobs/{jid}").json()["kind"] == "outline"
        assert c.post(f"/jobs/{jid}/cancel").json()["cancelled"] == True
        assert c.get(f"/jobs/{jid}").json()["status"] == "cancelled"
    finally:
        c.delete(f"/projects/{pid}")

@skip
def test_e2e_full_writing_session():
    """Full session: project -> chapters -> character -> lore -> search -> export."""
    c = httpx.Client(base_url=BASE, timeout=TIMEOUT)
    pid = c.post("/projects/", json={"title": "Full Session Novel", "genre": "Fantasy", "style_guide": "Dark tone, short sentences."}).json()["id"]
    try:
        ch_ids = []
        for i, (t, ct) in enumerate([("Awakening", "The hero woke to thunder."), ("The Quest", "They set out at dawn."), ("The Battle", "Swords clashed in the dark.")]):
            cid = c.post("/chapters/", json={"project_id": pid, "title": t, "content": ct, "scene_order": i}).json()["id"]
            ch_ids.append(cid)
        c.post("/characters/", json={"project_id": pid, "name": "Kaelith", "role": "protagonist", "personality": "fierce and loyal", "goals": "Avenge fallen clan"})
        c.post("/lore/", json={"project_id": pid, "name": "Ironspire City", "lore_type": "location", "description": "Capital city of the Northern Kingdom"})
        c.post("/timeline/", json={"project_id": pid, "title": "The Fall of Ironspire", "event_date": "Year 450", "involved_characters": ["Kaelith"]})
        search = c.get(f"/projects/{pid}/search?q=Kaelith&limit=10").json()
        assert len(search) >= 1
        exported = c.post("/export", json={"project_id": pid, "fmt": "md"}).text
        assert "Awakening" in exported and "The Quest" in exported and "The Battle" in exported
        assert c.post("/export", json={"project_id": pid, "fmt": "html"}).status_code == 200
    finally:
        c.delete(f"/projects/{pid}")
