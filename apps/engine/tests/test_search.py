from __future__ import annotations


def test_search_not_found(client):
    r = client.get("/api/projects/nonexistent/search?q=test")
    assert r.status_code == 200
    assert r.json() == []
