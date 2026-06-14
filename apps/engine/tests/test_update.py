from __future__ import annotations


def test_update_check(client):
    r = client.get("/api/update/check")
    assert r.status_code == 200
    data = r.json()
    assert "update_available" in data
