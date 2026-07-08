"""Tests for DELETE /api/backup/{filename} endpoint."""

from __future__ import annotations


def test_delete_single_backup(client):
    """Deleting a single backup removes it from the list."""
    created = client.post("/api/backup").json()
    filename = created["filename"]

    r = client.delete(f"/api/backup/{filename}")
    assert r.status_code == 204

    backups = client.get("/api/backups").json()
    assert not any(b["filename"] == filename for b in backups)


def test_delete_backup_not_found(client):
    """Returns 404 for non-existent backup."""
    r = client.delete("/api/backup/nonexistent.db")
    assert r.status_code == 404


def test_delete_backup_invalid_name(client):
    """Returns 404 for invalid backup filename."""
    r = client.delete("/api/backup/../../etc/passwd")
    assert r.status_code == 404
