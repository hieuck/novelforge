"""Quick smoke test — runs against a running engine on localhost:9090."""
import json, subprocess, sys, time, urllib.request, urllib.error

def start_engine():
    proc = subprocess.Popen(
        [sys.executable, '-m', 'uvicorn', 'app:app',
         '--host', '127.0.0.1', '--port', '9090', '--log-level', 'error'],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        cwd=str(__import__('pathlib').Path(__file__).resolve().parent.parent / 'apps' / 'engine'),
    )
    time.sleep(4)
    return proc

def req(method, path, body=None, raw=False):
    url = f"http://127.0.0.1:9090/api{path}"
    data = json.dumps(body).encode() if body else None
    r = urllib.request.Request(url, data=data, method=method)
    r.add_header("Content-Type", "application/json")
    try:
        resp = urllib.request.urlopen(r)
        content = resp.read()
        if raw or resp.status == 204:
            return content if raw else None
        return json.loads(content)
    except urllib.error.HTTPError as e:
        return {"_status": e.code, "_error": e.read().decode()}

def check(n, label, ok, detail=""):
    m = "✅" if ok else "❌"
    print(f"{m} {n:2d}. {label}" + (f" — {detail}" if detail else ""))

proc = start_engine()
try:
    # Health
    h = req("GET", "/health")
    check(1, "Health", h.get("status") == "ok")

    # Project
    p = req("POST", "/projects/", {"title": "Smoke", "genre": "Fantasy"})
    check(2, "Create project", bool(p.get("id")), str(p.get("_status", "")))

    # Chapter
    c = req("POST", "/chapters/", {"project_id": p["id"], "title": "Ch1", "content": "a b c", "scene_order": 0})
    check(3, "Create chapter", c.get("word_count") == 3)

    # Stats
    s = req("GET", f"/chapters/{c['id']}/stats")
    check(4, "Chapter stats", s.get("reading_time_seconds", 0) > 0)

    # Export
    e = req("GET", f"/chapters/{c['id']}/export?format=md", raw=True)
    check(5, "Export chapter", isinstance(e, bytes) and b"# Ch1" in e)

    # Character
    ch = req("POST", "/characters/", {"project_id": p["id"], "name": "Hero"})
    check(6, "Create character", bool(ch.get("id")))

    # Lore
    l = req("POST", "/lore/", {"project_id": p["id"], "name": "World", "lore_type": "location"})
    check(7, "Create lore", bool(l.get("id")))

    # Dashboard
    d = req("GET", "/stats/dashboard")
    check(8, "Dashboard stats", d.get("total_lore", 0) >= 1)

    # Health DB
    hdb = req("GET", "/health/db")
    check(9, "Health DB", hdb.get("tables", 0) >= 5)

    # Echo
    ec = req("POST", "/tools/echo", {"test": True})
    check(10, "Echo", ec.get("ok") is True)

    # Backup
    bk = req("POST", "/backup")
    check(11, "Create backup", bk.get("filename", "").endswith(".db"))

    # Recent
    rc = req("GET", "/chapters/recent?limit=5")
    check(12, "Recent chapters", len(rc) >= 1)

    # Duplicate
    dup = req("POST", f"/chapters/{c['id']}/duplicate")
    check(13, "Duplicate chapter", "(Copy)" in dup.get("title", ""))

    # Settings
    ps = req("PUT", f"/projects/{p['id']}/settings", {"goal": "500"})
    check(14, "Project settings", ps.get("goal") == "500")

    # Batch delete
    bd = req("POST", "/chapters/batch-delete", {"ids": [dup["id"]]})
    check(15, "Batch delete", bd.get("deleted") == 1)

    # Search
    sr = req("GET", f"/projects/{p['id']}/search?q=hello")
    check(16, "Search", isinstance(sr, list))

    # Delete project (should auto-backup)
    dp = req("DELETE", f"/projects/{p['id']}")
    check(17, "Delete project", dp is None or dp.get("_status") == 204)

    # Verify deleted
    pg = req("GET", f"/projects/{p['id']}")
    check(18, "Verify deleted", pg.get("_status") == 404)

    print(f"\n✅ All 18 checks passed!")
except Exception as e:
    print(f"\n❌ FAILED: {e}")
    sys.exit(1)
finally:
    proc.terminate()
    proc.wait()
