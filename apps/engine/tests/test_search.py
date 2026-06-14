from __future__ import annotations


def test_search_no_project(client):
    r = client.get("/api/projects/nonexistent/search?q=test")
    assert r.status_code == 200
    assert r.json() == []


def test_search_with_data(client):
    """Create project + chapter, then search."""
    proj = client.post("/api/projects/", json={"title": "Search Test"}).json()
    client.post("/api/chapters/", json={
        "project_id": proj["id"], "title": "Chapter Alpha",
        "content": "The ancient dragon flew across the sky."
    })
    r = client.get(f"/api/projects/{proj['id']}/search?q=dragon&limit=10")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
