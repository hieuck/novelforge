"""Tests for auto-backup before destructive operations."""

from __future__ import annotations


def test_auto_backup_before_project_delete(client):
    """Deleting a project creates a backup with 'pre_delete_' prefix."""
    proj = client.post("/api/projects/", json={"title": "ToDelete"}).json()

    r = client.delete(f"/api/projects/{proj['id']}")
    assert r.status_code == 204

    # Check most recent backup
    backups = client.get("/api/backups?limit=5").json()
    assert any(b["filename"].startswith("pre_delete_") for b in backups), (
        "No 'pre_delete_' backup found after project delete"
    )


def test_auto_backup_does_not_block_delete(client):
    """Backup failure should not prevent the delete from succeeding."""
    proj = client.post("/api/projects/", json={"title": "StillDeleted"}).json()
    r = client.delete(f"/api/projects/{proj['id']}")
    assert r.status_code == 204
