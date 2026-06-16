"""Tests for /api/backup endpoints."""


def test_create_backup(client):
    r = client.post("/api/backup")
    assert r.status_code == 201
    data = r.json()
    assert "filename" in data
    assert data["filename"].endswith(".db")
    assert data["size_bytes"] > 0


def test_list_backups(client):
    client.post("/api/backup")
    r = client.get("/api/backups")
    assert r.status_code == 200
    backups = r.json()
    assert len(backups) >= 1
    assert backups[0]["filename"].endswith(".db")
    assert backups[0]["size_bytes"] > 0


def test_download_backup(client):
    created = client.post("/api/backup").json()
    r = client.get(f"/api/backup/{created['filename']}")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/octet-stream"


def test_restore_backup(client):
    created = client.post("/api/backup").json()
    r = client.post(f"/api/backup/{created['filename']}/restore")
    assert r.status_code == 200
    assert r.json()["message"].startswith("Restored")
