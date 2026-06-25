"""Tests for version info in health endpoint."""
from __future__ import annotations


def test_health_includes_version(client):
    """Health response includes app version."""
    r = client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert "version" in data
    assert isinstance(data["version"], str)
    assert len(data["version"]) > 0
