"""API routes for session logs and changelog."""

from __future__ import annotations

import json
import re
from pathlib import Path

from fastapi import APIRouter, Query

from aioncode.internal.dashboard.services.encoding import decode_project_path

router = APIRouter(tags=["logs"])


@router.get("/api/projects/{encoded}/sessions")
async def get_sessions(encoded: str, limit: int = Query(10)) -> dict:
    """Get session digests from sessions.jsonl."""
    project_path = decode_project_path(encoded)
    sessions_file = Path(project_path) / ".aion" / "sessions.jsonl"

    if not sessions_file.exists():
        return {"ok": True, "sessions": []}

    sessions = []
    try:
        lines = sessions_file.read_text(encoding="utf-8").splitlines()
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                sessions.append(json.loads(line))
            except json.JSONDecodeError:
                continue
            if len(sessions) >= limit:
                break
    except OSError:
        pass

    return {"ok": True, "sessions": sessions}


@router.get("/api/projects/{encoded}/changelog")
async def get_changelog(encoded: str, limit: int = Query(10)) -> dict:
    """Get changelog entries parsed from changelog.md."""
    project_path = decode_project_path(encoded)
    changelog_file = Path(project_path) / ".aion" / "changelog.md"

    if not changelog_file.exists():
        return {"ok": True, "entries": []}

    content = changelog_file.read_text(encoding="utf-8")
    entries = []

    # Parse ## YYYY-MM-DD HH:MM | description sections
    pattern = r"## (\d{4}-\d{2}-\d{2}[^\n]*)\n(.*?)(?=\n## |\Z)"
    for match in re.finditer(pattern, content, re.DOTALL):
        header = match.group(1).strip()
        body = match.group(2).strip()
        entries.append({"header": header, "body": body})
        if len(entries) >= limit:
            break

    return {"ok": True, "entries": entries}
