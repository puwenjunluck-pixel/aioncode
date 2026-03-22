"""Integration tests for Dashboard API (FastAPI routers)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from aioncode.internal.dashboard import create_app
from aioncode.internal.dashboard.services.encoding import encode_project_path


@pytest.fixture
def app():
    """Create a test FastAPI app."""
    return create_app(dev=False)


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    """Create a project with .aion/ structure for testing."""
    aion = tmp_path / ".aion"
    aion.mkdir()
    (aion / "config.yml").write_text('version: "0.5.0"\n')
    (aion / "changelog.md").write_text(
        "## 2026-03-22 10:00 | Test\n\n### Summary\n- test\n"
    )
    (aion / "rules").mkdir()
    (aion / "rules" / "pitfalls.md").write_text(
        "---\ncategory: pitfalls\nrule_count: 1\n---\n\n- **test rule**\n"
    )
    (aion / "specs").mkdir()
    (aion / "plans").mkdir()
    (aion / "bugs").mkdir()
    (aion / "monitor").mkdir()
    (aion / "monitor" / "events.jsonl").write_text(
        json.dumps({"ts": "2026-03-22T10:00:00Z", "tool_name": "Read"}) + "\n"
    )
    # sessions.jsonl
    (aion / "sessions.jsonl").write_text(
        json.dumps({"ts": "2026-03-22", "tools": ["Read"], "files": 3}) + "\n"
    )
    (tmp_path / ".git").mkdir()
    return tmp_path


@pytest.fixture
def encoded(project_dir: Path) -> str:
    """Encoded project path for URL parameters."""
    return encode_project_path(str(project_dir))


# --- Projects Router ---


class TestProjectsAPI:
    def test_list_projects(self, client):
        resp = client.get("/api/projects")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_add_and_remove_project(self, client, project_dir):
        # Add
        resp = client.post("/api/projects/add", json={"path": str(project_dir)})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("ok") is True

        # Remove
        resp = client.post("/api/projects/remove", json={"path": str(project_dir)})
        assert resp.status_code == 200

    def test_project_stats(self, client, encoded, project_dir):
        resp = client.get(f"/api/projects/{encoded}/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "rules" in data or "ok" in data


# --- Files Router ---


class TestFilesAPI:
    def test_file_tree(self, client, encoded):
        resp = client.get(f"/api/projects/{encoded}/files")
        assert resp.status_code == 200

    def test_read_file(self, client, encoded):
        resp = client.get(
            f"/api/projects/{encoded}/file", params={"path": "config.yml"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("ok") is True
        assert "content" in data

    def test_create_and_delete_file(self, client, encoded):
        # Create
        resp = client.post(
            f"/api/projects/{encoded}/file",
            json={"path": "specs/test.md", "content": "# Test spec\n"},
        )
        assert resp.status_code == 200
        assert resp.json().get("ok") is True

        # Read back
        resp = client.get(
            f"/api/projects/{encoded}/file", params={"path": "specs/test.md"}
        )
        assert resp.json().get("content") == "# Test spec\n"

        # Delete
        resp = client.delete(
            f"/api/projects/{encoded}/file", params={"path": "specs/test.md"}
        )
        assert resp.status_code == 200

    def test_write_file(self, client, encoded):
        resp = client.put(
            f"/api/projects/{encoded}/file",
            json={"path": "config.yml", "content": 'version: "0.5.1"\n'},
        )
        assert resp.status_code == 200
        assert resp.json().get("ok") is True


# --- Monitor Router ---


class TestMonitorAPI:
    def test_monitor_events(self, client, encoded):
        resp = client.get(f"/api/monitor/{encoded}/events", params={"since": 0})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("ok") is True
        assert "events" in data

    def test_monitor_state(self, client, encoded):
        resp = client.get(f"/api/monitor/{encoded}/state")
        assert resp.status_code == 200

    def test_monitor_clear(self, client, encoded):
        resp = client.post(f"/api/monitor/{encoded}/clear")
        assert resp.status_code == 200
        assert resp.json().get("ok") is True

    def test_recent_events(self, client, encoded):
        resp = client.get(
            f"/api/projects/{encoded}/events/recent", params={"limit": 5}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("ok") is True

    def test_sse_stream_route_registered(self, app, encoded):
        """SSE endpoint is registered in the app routes."""
        routes = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/api/projects/{encoded}/events/stream" in routes


# --- Bugs Router ---


class TestBugsAPI:
    def test_bug_stats(self, client, encoded):
        resp = client.get(f"/api/projects/{encoded}/bugs/stats")
        assert resp.status_code == 200

    def test_list_bugs(self, client, encoded):
        resp = client.get(f"/api/projects/{encoded}/bugs")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("ok") is True
        assert "bugs" in data


# --- Team Router ---


class TestTeamAPI:
    def test_read_team(self, client, encoded):
        resp = client.get(f"/api/projects/{encoded}/team")
        assert resp.status_code == 200


# --- Commands Router ---


class TestCommandsAPI:
    def test_list_commands(self, client):
        resp = client.get("/api/commands")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("ok") is True
        assert "commands" in data

    def test_read_command_not_found(self, client):
        resp = client.get("/api/commands/nonexistent")
        assert resp.status_code == 200
        assert resp.json().get("ok") is False


# --- Browse Router ---


class TestBrowseAPI:
    def test_browse_home(self, client):
        resp = client.get("/api/browse", params={"path": "~"})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("ok") is True
        assert "items" in data

    def test_browse_invalid_path(self, client):
        resp = client.get("/api/browse", params={"path": "/nonexistent_xyz_123"})
        assert resp.status_code == 200
        assert resp.json().get("ok") is False


# --- Logs Router ---


class TestLogsAPI:
    def test_sessions(self, client, encoded):
        resp = client.get(f"/api/projects/{encoded}/sessions")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("ok") is True
        assert "sessions" in data

    def test_changelog(self, client, encoded):
        resp = client.get(f"/api/projects/{encoded}/changelog")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("ok") is True
        assert "entries" in data


# --- Frontend Routes ---


class TestFrontend:
    def test_index(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]

    def test_monitor_page_removed(self, client, encoded):
        """Monitor page route was removed in v0.5 (replaced by inline monitor view)."""
        resp = client.get(f"/monitor/{encoded}")
        assert resp.status_code == 404
