"""Tests for routes/jobs.py"""
from __future__ import annotations
import sys, pathlib
ENGINE_DIR = pathlib.Path(__file__).resolve().parent.parent.parent / "apps" / "engine"
sys.path.insert(0, str(ENGINE_DIR))
from fastapi.testclient import TestClient
from app import app
client = TestClient(app)
def _pid(): return client.post("/api/projects/", json={"title": "J"}).json()["id"]

def test_create_minimal():
    pid = _pid(); r = client.post("/api/jobs", json={"project_id": pid, "kind": "outline"})
    assert r.status_code == 201; d = r.json()
    assert d["status"] == "queued" and d["kind"] == "outline" and d["project_id"] == pid

def test_create_with_params():
    pid = _pid(); r = client.post("/api/jobs", json={"project_id": pid, "kind": "summarize", "params": {"depth": 3}})
    assert r.json()["params"]["depth"] == 3

def test_get_by_id():
    pid = _pid(); job = client.post("/api/jobs", json={"project_id": pid, "kind": "continuity"}).json()
    f = client.get("/api/jobs/" + job["id"]).json()
    assert f["id"] == job["id"] and f["kind"] == "continuity"

def test_get_not_found():
    assert client.get("/api/jobs/bad-id").status_code == 404

def test_cancel_queued():
    pid = _pid(); job = client.post("/api/jobs", json={"project_id": pid, "kind": "plot_holes"}).json()
    r = client.post("/api/jobs/" + job["id"] + "/cancel")
    assert r.json()["cancelled"] == True
    assert client.get("/api/jobs/" + job["id"]).json()["status"] == "cancelled"

def test_cancel_idempotent():
    pid = _pid(); job = client.post("/api/jobs", json={"project_id": pid, "kind": "x"}).json()
    client.post("/api/jobs/" + job["id"] + "/cancel")
    assert client.post("/api/jobs/" + job["id"] + "/cancel").status_code == 200

def test_project_jobs_list():
    pid = _pid()
    for k in ["outline", "summarize", "continuity", "plot_holes"]:
        client.post("/api/jobs", json={"project_id": pid, "kind": k})
    jobs = client.get("/api/projects/" + pid + "/jobs").json()
    assert len(jobs) == 4 and {"outline","plot_holes"}.issubset({j["kind"] for j in jobs})

def test_websocket_stream():
    pid = _pid(); job = client.post("/api/jobs", json={"project_id": pid, "kind": "test"}).json()
    with client.websocket_connect("/api/ws/jobs/" + job["id"]) as ws:
        data = ws.receive_json()
        assert data["id"] == job["id"] and "status" in data

def test_websocket_not_found():
    with client.websocket_connect("/api/ws/jobs/nonexistent") as ws:
        data = ws.receive_json(); assert "error" in data

