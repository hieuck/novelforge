"""Full tests for jobs endpoints."""

from __future__ import annotations


def _create_project(client):
    r = client.post("/api/projects/", json={"title": "Jobs Full Test"})
    return r.json()["id"]


def _create_job(client, pid, task="Test job"):
    from unittest.mock import patch

    with patch("routes.jobs._run_agent_job"):
        r = client.post("/api/agent/jobs", json={"project_id": pid, "task": task})
        return r


def test_jobs_create_and_list(client):
    pid = _create_project(client)
    _create_job(client, pid, "Job 1")
    _create_job(client, pid, "Job 2")

    r = client.get(f"/api/projects/{pid}/jobs")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 2


def test_jobs_cancel(client):
    pid = _create_project(client)
    created = _create_job(client, pid, "Cancel me").json()
    assert created["status"] == "queued"

    r = client.post(f"/api/jobs/{created['id']}/cancel")
    assert r.status_code == 200
    # Status may be cancelled or failed depending on timing
    assert r.json()["status"] in ("cancelled", "failed")


def test_jobs_list_empty(client):
    pid = _create_project(client)
    r = client.get(f"/api/projects/{pid}/jobs")
    assert r.status_code == 200
    assert r.json() == []
