"""Tests that chapter export includes summary field."""

from __future__ import annotations


def test_export_txt_includes_summary(client):
    """TXT export should include chapter summary if present."""
    proj = client.post("/api/projects/", json={"title": "Test"}).json()
    ch = client.post(
        "/api/chapters/",
        json={
            "project_id": proj["id"],
            "title": "Ch1",
            "content": "Hello world.",
            "summary": "A short summary here",
        },
    ).json()

    r = client.get(f"/api/chapters/{ch['id']}/export?format=txt")
    assert r.status_code == 200
    assert "Summary" in r.text or "summary" in r.text
    assert "A short summary here" in r.text


def test_export_md_includes_summary(client):
    """MD export should include chapter summary if present."""
    proj = client.post("/api/projects/", json={"title": "Test"}).json()
    ch = client.post(
        "/api/chapters/",
        json={
            "project_id": proj["id"],
            "title": "Ch1",
            "content": "Hello world.",
            "summary": "A short summary here",
        },
    ).json()

    r = client.get(f"/api/chapters/{ch['id']}/export?format=md")
    assert r.status_code == 200
    assert "A short summary here" in r.text
