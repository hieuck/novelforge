"""Integration tests - full request/response cycles with DB."""
from __future__ import annotations
import sys, pathlib, zipfile, io
ENGINE_DIR = pathlib.Path(__file__).resolve().parent.parent.parent / "apps" / "engine"
sys.path.insert(0, str(ENGINE_DIR))
from fastapi.testclient import TestClient
from app import app
client = TestClient(app)

def _pid(t="T"): return client.post("/api/projects/", json={"title": t}).json()["id"]

def test_project_chapter_full_flow():
    pid = _pid("IntNov")
    c1 = client.post("/api/chapters/", json={"project_id": pid, "title": "C1", "content": "Once upon a time"}).json()
    c2 = client.post("/api/chapters/", json={"project_id": pid, "title": "C2", "content": "Then it happened", "scene_order": 1}).json()
    chs = client.get(f"/api/projects/{pid}/chapters").json()
    assert len(chs) == 2 and chs[0]["scene_order"] <= chs[1]["scene_order"]
    upd = client.patch(f"/api/chapters/{c1['id']}", json={"content": "Updated content here"}).json()
    assert upd["word_count"] == 3
    client.delete(f"/api/chapters/{c1['id']}")
    assert len(client.get(f"/api/projects/{pid}/chapters").json()) == 1
    client.delete(f"/api/projects/{pid}")
    assert client.get(f"/api/projects/{pid}").status_code == 404

def test_chapter_word_count_persisted():
    pid = _pid(); cid = client.post("/api/chapters/", json={"project_id": pid, "title": "T", "content": "one two three four five"}).json()["id"]
    assert client.get(f"/api/chapters/{cid}").json()["word_count"] == 5

def test_chapter_status_transitions():
    pid = _pid(); cid = client.post("/api/chapters/", json={"project_id": pid, "title": "T", "content": "x"}).json()["id"]
    for s in ["draft", "revised", "final"]:
        assert client.patch(f"/api/chapters/{cid}", json={"status": s}).json()["status"] == s

def test_character_full_lifecycle():
    pid = _pid()
    cid = client.post("/api/characters/", json={"project_id": pid, "name": "Aria", "role": "hero", "relationships": {"mentor": "Kael"}}).json()["id"]
    assert client.get(f"/api/characters/{cid}").json()["relationships"]["mentor"] == "Kael"
    client.patch(f"/api/characters/{cid}", json={"age": "23"})
    assert client.get(f"/api/characters/{cid}").json()["age"] == "23"
    assert len(client.get(f"/api/projects/{pid}/characters").json()) == 1
    client.delete(f"/api/characters/{cid}")
    assert client.get(f"/api/characters/{cid}").status_code == 404

def test_lore_all_types():
    pid = _pid()
    for lt in ["location", "organization", "magic", "technology", "term"]:
        r = client.post("/api/lore/", json={"project_id": pid, "name": f"I-{lt}", "lore_type": lt, "tags": ["t1"]})
        assert r.status_code == 201
    assert len(client.get(f"/api/projects/{pid}/lore").json()) == 5

def test_lore_related_chapters_stored():
    pid = _pid(); cid = client.post("/api/chapters/", json={"project_id": pid, "title": "C", "content": "x"}).json()["id"]
    lid = client.post("/api/lore/", json={"project_id": pid, "name": "K", "lore_type": "location", "related_chapters": [cid]}).json()["id"]
    assert cid in client.get(f"/api/lore/{lid}").json()["related_chapters"]

def test_timeline_with_characters():
    pid = _pid()
    for i in range(3):
        client.post("/api/timeline/", json={"project_id": pid, "title": f"E{i}", "involved_characters": ["Aria"]})
    items = client.get(f"/api/projects/{pid}/timeline").json()
    assert len(items) == 3 and all("Aria" in (x.get("involved_characters") or []) for x in items)

def test_search_indexes_on_create():
    pid = _pid("SrchCr")
    client.post("/api/chapters/", json={"project_id": pid, "title": "Dragon Chapter", "content": "The fire dragon sleeps."})
    client.post("/api/characters/", json={"project_id": pid, "name": "Dragonrider", "role": "hero"})
    client.post("/api/lore/", json={"project_id": pid, "name": "Dragon Keep", "lore_type": "location"})
    results = client.get(f"/api/projects/{pid}/search?q=dragon&limit=20").json()
    assert len(results) >= 2 and "chapter" in {r["kind"] for r in results}

def test_search_updates_on_patch():
    pid = _pid(); cid = client.post("/api/chapters/", json={"project_id": pid, "title": "B", "content": "nothing"}).json()["id"]
    assert len(client.get(f"/api/projects/{pid}/search?q=phoenix").json()) == 0
    client.patch(f"/api/chapters/{cid}", json={"content": "The phoenix rises."})
    assert len(client.get(f"/api/projects/{pid}/search?q=phoenix").json()) > 0

def test_search_removes_on_delete():
    pid = _pid(); cid = client.post("/api/chapters/", json={"project_id": pid, "title": "T", "content": "xyzunique9876"}).json()["id"]
    assert len(client.get(f"/api/projects/{pid}/search?q=xyzunique9876").json()) > 0
    client.delete(f"/api/chapters/{cid}")
    assert len(client.get(f"/api/projects/{pid}/search?q=xyzunique9876").json()) == 0

def test_export_chapters_ordered():
    pid = _pid("ExpOrd")
    for i, t in enumerate(["Part One", "Part Two", "Part Three"]):
        client.post("/api/chapters/", json={"project_id": pid, "title": t, "content": f"c{i}", "scene_order": i})
    md = client.post("/api/export", json={"project_id": pid, "fmt": "md"}).text
    assert md.index("Part One") < md.index("Part Two") < md.index("Part Three")

def test_export_zip_files():
    pid = _pid(); client.post("/api/chapters/", json={"project_id": pid, "title": "C", "content": "x"})
    r = client.post("/api/export", json={"project_id": pid, "fmt": "zip"})
    names = zipfile.ZipFile(io.BytesIO(r.content)).namelist()
    assert "story.md" in names and "characters.json" in names and "project.json" in names

def test_import_export_roundtrip():
    pid = _pid("RT"); md = "# S\n\n## Alpha\nA.\n\n## Beta\nB.\n"
    imp = client.post("/api/import", json={"project_id": pid, "content": md, "filename": "n.md", "mode": "split_h2"}).json()
    assert imp["imported"] == 2
    exported = client.post("/api/export", json={"project_id": pid, "fmt": "md"}).text
    assert "Alpha" in exported and "Beta" in exported

def test_settings_persist():
    client.post("/api/settings/current", json={"provider": "openrouter", "base_url": "https://openrouter.ai/api/v1", "model": "mistral-7b", "temperature": 0.5, "max_tokens": 1024})
    saved = client.get("/api/settings/current").json()
    assert saved["provider"] == "openrouter" and saved["model"] == "mistral-7b"

def test_settings_test_connection_bad_url():
    r = client.post("/api/settings/test", json={"provider": "ollama", "base_url": "http://127.0.0.1:19999", "model": "x", "temperature": 0.7, "max_tokens": 100})
    assert r.status_code == 200 and r.json()["ok"] == False

def test_job_create_get_cancel():
    pid = _pid()
    job = client.post("/api/jobs", json={"project_id": pid, "kind": "outline"}).json()
    assert job["status"] == "queued"
    r = client.post(f"/api/jobs/{job['id']}/cancel")
    assert r.json()["cancelled"] == True
    assert client.get(f"/api/jobs/{job['id']}").json()["status"] == "cancelled"

def test_project_jobs_list():
    pid = _pid()
    for k in ["outline", "summarize", "continuity"]:
        client.post("/api/jobs", json={"project_id": pid, "kind": k})
    jobs = client.get(f"/api/projects/{pid}/jobs").json()
    assert len(jobs) == 3
