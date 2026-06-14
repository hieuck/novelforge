from __future__ import annotations


def test_update_check(client):
    r = client.get("/api/update/check")
    assert r.status_code == 200
    data = r.json()
    assert "update_available" in data


def test_update_apply_unauthenticated(client):
    """Apply update without a git repo should fail gracefully."""
    r = client.post("/api/update/apply")
    assert r.status_code == 200
    data = r.json()
    # In test environment (no git repo), it should return success=False
    assert "success" in data

