"""Tests for agent internal tool functions + route consistency."""

from __future__ import annotations

from db.session import SessionLocal
from models.extra import Lore, TimelineItem


def _create_project(client):
    r = client.post("/api/projects/", json={"title": "Agent Tool Test"})
    return r.json()["id"]


class TestAgentCreateLore:
    """Agent's _create_lore must handle list tags correctly."""

    def test_create_lore_with_list_tags(self, client):
        from routes.agent import _create_lore

        pid = _create_project(client)
        result = _create_lore(
            pid,
            {
                "name": "Magic Stone",
                "lore_type": "item",
                "description": "A glowing stone",
                "tags": ["magic", "ancient", "rare"],
            },
        )
        assert "id" in result, f"Failed: {result}"

    def test_create_lore_with_string_tags(self, client):
        from routes.agent import _create_lore

        pid = _create_project(client)
        result = _create_lore(
            pid,
            {
                "name": "Old Scroll",
                "lore_type": "item",
                "description": "Ancient scroll",
                "tags": '["old", "scroll"]',
            },
        )
        assert "id" in result, f"Failed: {result}"

    def test_create_lore_no_tags(self, client):
        from routes.agent import _create_lore

        pid = _create_project(client)
        result = _create_lore(
            pid,
            {
                "name": "Simple Item",
                "lore_type": "item",
            },
        )
        assert "id" in result, f"Failed: {result}"


class TestAgentCreateTimeline:
    """Agent's _create_timeline_event must handle list fields correctly."""

    def test_create_timeline_with_list_characters(self, client):
        from routes.agent import _create_timeline_event

        pid = _create_project(client)
        result = _create_timeline_event(
            pid,
            {
                "title": "Hero appears",
                "description": "The hero arrives",
                "involved_characters": ["char-id-1", "char-id-2"],
            },
        )
        assert "id" in result, f"Failed: {result}"

    def test_create_timeline_empty_characters(self, client):
        from routes.agent import _create_timeline_event

        pid = _create_project(client)
        result = _create_timeline_event(
            pid,
            {
                "title": "Event",
                "involved_characters": [],
            },
        )
        assert "id" in result, f"Failed: {result}"


class TestAgentCreateChapter:
    """Agent's _create_chapter must handle word count correctly."""

    def test_create_chapter(self, client):
        from routes.agent import _create_chapter

        pid = _create_project(client)
        result = _create_chapter(
            pid,
            {
                "title": "Test Chapter",
                "content": "Once upon a time in a land far away.",
            },
        )
        assert "id" in result, f"Failed: {result}"
        assert result.get("word_count", 0) > 0


class TestAgentCreateCharacter:
    """Agent's _create_char must handle all fields."""

    def test_create_character(self, client):
        from routes.agent import _create_char

        pid = _create_project(client)
        result = _create_char(
            pid,
            {
                "name": "Test Hero",
                "role": "protagonist",
                "personality": "Brave",
                "goals": "Save the world",
            },
        )
        assert "id" in result, f"Failed: {result}"
        assert result["name"] == "Test Hero"


class TestRouteAndAgentConsistency:
    """Route and agent must both produce valid DB records."""

    def test_lore_route_and_agent_match(self, client):
        """Create lore via route and via agent — both must appear in DB."""
        pid = _create_project(client)

        # Create via route
        r = client.post(
            "/api/lore/",
            json={
                "project_id": pid,
                "lore_type": "location",
                "name": "Route Lore",
                "tags": ["route", "test"],
            },
        )
        assert r.status_code == 201

        # Create via agent
        from routes.agent import _create_lore

        result = _create_lore(
            pid,
            {
                "name": "Agent Lore",
                "lore_type": "item",
                "tags": ["agent", "test"],
            },
        )
        assert "id" in result

        # Both must be queryable
        db = SessionLocal()
        try:
            items = db.query(Lore).filter(Lore.project_id == pid).all()
            assert len(items) == 2, f"Expected 2 lore, got {len(items)}"
            names = [i.name for i in items]
            assert "Route Lore" in names
            assert "Agent Lore" in names
        finally:
            db.close()

    def test_timeline_route_and_agent_match(self, client):
        """Create timeline via route and via agent — both must appear in DB."""
        pid = _create_project(client)

        r = client.post(
            "/api/timeline/",
            json={
                "project_id": pid,
                "title": "Route Event",
                "involved_characters": ["char-1"],
            },
        )
        assert r.status_code == 201

        from routes.agent import _create_timeline_event

        result = _create_timeline_event(
            pid,
            {
                "title": "Agent Event",
                "involved_characters": ["char-2"],
            },
        )
        assert "id" in result

        db = SessionLocal()
        try:
            items = db.query(TimelineItem).filter(TimelineItem.project_id == pid).all()
            assert len(items) == 2
        finally:
            db.close()


class TestAgentUpdateTools:
    """Agent's update tools (update_character, update_lore, update_chapter)."""

    def test_update_character(self, client):
        from routes.agent import _create_char, _update_character

        pid = _create_project(client)
        created = _create_char(pid, {"name": "Old Name", "role": "hero"})
        cid = created["id"]
        result = _update_character(pid, {"character_id": cid, "name": "New Name"})
        assert result.get("updated"), f"Update failed: {result}"
        assert result["name"] == "New Name"

    def test_update_lore(self, client):
        from routes.agent import _create_lore, _update_lore

        pid = _create_project(client)
        created = _create_lore(pid, {"name": "Old Lore", "lore_type": "item", "tags": ["old"]})
        lid = created["id"]
        result = _update_lore(pid, {"lore_id": lid, "name": "Updated Lore", "tags": ["new"]})
        assert result.get("updated"), f"Update failed: {result}"

    def test_update_lore_list_tags(self, client):
        """Verify _update_lore handles list tags."""
        from routes.agent import _create_lore, _update_lore

        pid = _create_project(client)
        created = _create_lore(pid, {"name": "Tag Test", "lore_type": "item"})
        lid = created["id"]
        result = _update_lore(pid, {"lore_id": lid, "tags": ["tag1", "tag2"]})
        assert result.get("updated"), f"Update failed: {result}"

    def test_update_chapter(self, client):
        from routes.agent import _create_chapter, _update_chapter

        pid = _create_project(client)
        created = _create_chapter(pid, {"title": "Ch1", "content": "Old text"})
        cid = created["id"]
        result = _update_chapter(pid, {"chapter_id": cid, "content": "New text here"})
        assert result.get("updated"), f"Update failed: {result}"
        assert result["word_count"] > 0
