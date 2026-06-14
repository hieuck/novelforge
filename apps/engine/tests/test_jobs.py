"""Tests for /api/agent/jobs and related endpoints."""
from __future__ import annotations

from unittest.mock import patch


def _create_project(client):
    r = client.post("/api/projects/", json={"title": "Jobs Test"})
    return r.json()["id"]


def test_create_job(client):
    pid = _create_project(client)
    with patch("routes.jobs._run_agent_job"):
        r = client.post("/api/agent/jobs", json={"project_id": pid, "task": "Test task"})
    assert r.status_code == 201
    data = r.json()
    assert data["kind"] == "agent"
    assert data["status"] == "queued"
    assert "id" in data


def test_list_project_jobs(client):
    pid = _create_project(client)
    with patch("routes.jobs._run_agent_job"):
        client.post("/api/agent/jobs", json={"project_id": pid, "task": "Job A"})
        client.post("/api/agent/jobs", json={"project_id": pid, "task": "Job B"})
    r = client.get(f"/api/projects/{pid}/jobs")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 2


def test_cancel_job(client):
    pid = _create_project(client)
    with patch("routes.jobs._run_agent_job"):
        created = client.post("/api/agent/jobs", json={"project_id": pid, "task": "Cancel me"}).json()
    r = client.post(f"/api/jobs/{created['id']}/cancel")
    assert r.status_code == 200
    assert r.json()["status"] in ("cancelled", "failed")
