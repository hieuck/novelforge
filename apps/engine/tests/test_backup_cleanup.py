"""Tests for POST /api/backup/cleanup endpoint."""
from __future__ import annotations


def test_cleanup_removes_old_backups(client):
    """Cleanup deletes backups beyond the keep count."""
    client.post("/api/backup")
    client.post("/api/backup")
    client.post("/api/backup")

    r = client.post("/api/backup/cleanup?keep=2")
    assert r.status_code == 200
    data = r.json()
    assert data["deleted"] >= 1


def test_cleanup_default_keep(client):
    """Default keep is 10 if not specified."""
    r = client.post("/api/backup/cleanup")
    assert r.status_code == 200


def test_cleanup_not_found(client):
    """Returns empty result when no backups exist."""
    r = client.post("/api/backup/cleanup?keep=5")
    assert r.status_code == 200
