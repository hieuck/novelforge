"""Tests for Markdown rendering in HTML export."""

from __future__ import annotations


def test_export_html_renders_bold(client):
    """HTML export renders **bold** as <strong>."""
    proj = client.post("/api/projects/", json={"title": "Markdown Test"}).json()
    ch = client.post(
        "/api/chapters/",
        json={
            "project_id": proj["id"],
            "title": "Chapter 1",
            "content": "This is **bold** text.",
        },
    ).json()

    r = client.get(f"/api/chapters/{ch['id']}/export?format=html")
    assert r.status_code == 200
    html = r.text
    assert "<strong>bold</strong>" in html


def test_export_html_renders_italic(client):
    """HTML export renders *italic* as <em>."""
    proj = client.post("/api/projects/", json={"title": "Markdown Test"}).json()
    ch = client.post(
        "/api/chapters/",
        json={
            "project_id": proj["id"],
            "title": "Chapter 1",
            "content": "This is *italic* text.",
        },
    ).json()

    r = client.get(f"/api/chapters/{ch['id']}/export?format=html")
    assert r.status_code == 200
    html = r.text
    assert "<em>italic</em>" in html


def test_export_html_renders_headings(client):
    """HTML export renders Markdown headings."""
    proj = client.post("/api/projects/", json={"title": "Markdown Test"}).json()
    ch = client.post(
        "/api/chapters/",
        json={
            "project_id": proj["id"],
            "title": "Chapter 1",
            "content": "## Section\n\n### Subsection",
        },
    ).json()

    r = client.get(f"/api/chapters/{ch['id']}/export?format=html")
    assert r.status_code == 200
    html = r.text
    assert "<h2>Section</h2>" in html
    assert "<h3>Subsection</h3>" in html


def test_export_md_preserves_markdown_syntax(client):
    """Markdown export keeps raw formatting markers."""
    proj = client.post("/api/projects/", json={"title": "Markdown Test"}).json()
    ch = client.post(
        "/api/chapters/",
        json={
            "project_id": proj["id"],
            "title": "Chapter 1",
            "content": "**bold** and *italic*",
        },
    ).json()

    r = client.get(f"/api/chapters/{ch['id']}/export?format=md")
    assert r.status_code == 200
    md = r.text
    assert "**bold**" in md
    assert "*italic*" in md
