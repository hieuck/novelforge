"""End-to-end test: create a real story via the API."""
import json
import os
import sys
import time
import urllib.request
import urllib.error

API = "http://127.0.0.1:9000/api"

def req(method, path, body=None):
    url = f"{API}{path}"
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body else None
    r = urllib.request.Request(url, data=data, method=method)
    r.add_header("Content-Type", "application/json")
    try:
        resp = urllib.request.urlopen(r)
        content = resp.read()
        try:
            return resp.status, json.loads(content.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return resp.status, {"_binary": True, "size": len(content)}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return e.code, json.loads(body) if body else {}

def test(label, ok):
    print(f"  {'PASS' if ok else 'FAIL'} {label}")
    return ok

print("=" * 50)
print("  E2E Story Creation Test")
print("=" * 50)

# 1. Health
s, d = req("GET", "/health")
assert test("Health check", s == 200 and d["status"] == "ok"), "Engine not running"

# 2. Create project
s, d = req("POST", "/projects/", {"title": "Truyện ma", "genre": "Horror", "language": "vi"})
assert test("Create project", s == 201 and "id" in d)
pid = d["id"]
print(f"     Project ID: {pid}")

# 3. List projects
s, d = req("GET", "/projects/")
assert test("List projects", s == 200 and len(d) >= 1)

# 4. Create chapter
s, d = req("POST", "/chapters/", {
    "project_id": pid,
    "title": "Chương 1: Đêm",
    "content": "Đêm tối. Tiếng gió rít bên ngoài. Linh ngồi trong góc phòng, tim đập thình thịch."
})
assert test("Create chapter", s == 201 and "id" in d)
ch1_id = d["id"]

# 5. Create another chapter
s, d = req("POST", "/chapters/", {
    "project_id": pid,
    "title": "Chương 2: Cánh cửa",
    "content": '"Ai đó?" Linh thì thầm. Cánh cửa từ từ mở ra.'
})
assert test("Create chapter 2", s == 201)

# 6. List chapters
s, d = req("GET", f"/projects/{pid}/chapters")
assert test("List chapters", s == 200 and len(d) == 2)

# 7. Get chapter 1
s, d = req("GET", f"/chapters/{ch1_id}")
assert test("Get chapter", s == 200 and d["id"] == ch1_id)

# 8. Update chapter
s, d = req("PATCH", f"/chapters/{ch1_id}", {"content": "Đêm tối. Tiếng gió rít bên ngoài. Linh ngồi trong góc phòng, tim đập thình thịch. Cô biết có ai đó đang ở ngoài cửa."})
assert test("Update chapter", s == 200)

# 9. Create character
s, d = req("POST", "/characters/", {
    "project_id": pid,
    "name": "Linh",
    "role": "Nhân vật chính",
    "age": "25",
    "personality": "Dũng cảm, tò mò"
})
assert test("Create character", s == 201)
char_id = d["id"]

# 10. List characters
s, d = req("GET", f"/projects/{pid}/characters")
assert test("List characters", s == 200 and len(d) >= 1)

# 11. Get character
s, d = req("GET", f"/characters/{char_id}")
assert test("Get character", s == 200 and d["id"] == char_id)

# 12. Create lore
s, d = req("POST", "/lore/", {
    "project_id": pid,
    "lore_type": "location",
    "name": "Ngôi nhà hoang",
    "description": "Một ngôi nhà bỏ hoang ở cuối làng, nơi đồn đại có ma."
})
assert test("Create lore", s == 201)
lore_id = d["id"]

# 13. List lore
s, d = req("GET", f"/projects/{pid}/lore")
assert test("List lore", s == 200 and len(d) >= 1)

# 14. Create timeline
s, d = req("POST", "/timeline/", {
    "project_id": pid,
    "title": "Linh vào nhà hoang",
    "description": "Đêm đầu tiên Linh bước vào ngôi nhà hoang."
})
assert test("Create timeline", s == 201)
tl_id = d["id"]

# 15. List timeline
s, d = req("GET", f"/projects/{pid}/timeline")
assert test("List timeline", s == 200 and len(d) >= 1)

# 16. Search
s, d = req("GET", f"/projects/{pid}/search?q=Linh")
assert test("Search", s == 200)

# 17. Export
s, d = req("POST", "/export", {"project_id": pid, "fmt": "md"})
assert test("Export markdown", s == 200)

# 18. Get project
s, d = req("GET", f"/projects/{pid}")
assert test("Get project", s == 200 and d["title"] == "Truyện ma")

# 19. Delete chapter
s, d = req("DELETE", f"/chapters/{ch1_id}")
assert test("Delete chapter", s == 204)

# 20. Delete project (cascades all data)
s, d = req("DELETE", f"/projects/{pid}")
assert test("Delete project", s == 204)

# 21. Verify deleted
s, d = req("GET", f"/projects/{pid}")
assert test("Project gone", s == 404)

print()
print("=" * 50)
print(f"  ALL {21 if True else 0} TESTS PASSED")
print("=" * 50)
