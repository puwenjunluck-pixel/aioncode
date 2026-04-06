"""API routes for design brainstorm collaboration."""

from __future__ import annotations

import json
import time
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

from aioncode.internal.dashboard.services.encoding import decode_project_path

router = APIRouter(tags=["brainstorm"])

_BRAINSTORM_DIR = ".aion/brainstorm"
_SCREEN_FILE = "screen.json"
_EVENTS_FILE = "events.jsonl"


class BrainstormEvent(BaseModel):
    """A user interaction event from the Dashboard."""

    type: str = "click"
    choice: str = ""


@router.get("/api/projects/{encoded}/brainstorm/screen")
async def brainstorm_screen(encoded: str) -> dict:
    """Read current brainstorm screen content."""
    project_path = decode_project_path(encoded)
    screen_path = Path(project_path) / _BRAINSTORM_DIR / _SCREEN_FILE
    if not screen_path.exists():
        return {"ok": True, "active": False, "screen": None}
    try:
        data = json.loads(screen_path.read_text(encoding="utf-8"))
        return {"ok": True, "active": True, "screen": data}
    except (json.JSONDecodeError, OSError):
        return {"ok": False, "message": "Failed to read screen.json"}


@router.post("/api/projects/{encoded}/brainstorm/event")
async def brainstorm_event(encoded: str, evt: BrainstormEvent) -> dict:
    """Append a user interaction event to events.jsonl."""
    project_path = decode_project_path(encoded)
    events_path = Path(project_path) / _BRAINSTORM_DIR / _EVENTS_FILE
    try:
        events_path.parent.mkdir(parents=True, exist_ok=True)
        entry = json.dumps(
            {"type": evt.type, "choice": evt.choice, "timestamp": int(time.time())},
            ensure_ascii=False,
        )
        with open(events_path, "a", encoding="utf-8") as f:
            f.write(entry + "\n")
        return {"ok": True}
    except OSError as e:
        return {"ok": False, "message": str(e)}


@router.get("/api/projects/{encoded}/brainstorm/status")
async def brainstorm_status(encoded: str) -> dict:
    """Check if there is an active brainstorm session."""
    project_path = decode_project_path(encoded)
    screen_path = Path(project_path) / _BRAINSTORM_DIR / _SCREEN_FILE
    if not screen_path.exists():
        return {"ok": True, "active": False}
    try:
        data = json.loads(screen_path.read_text(encoding="utf-8"))
        is_ended = data.get("type") == "info" and "已结束" in data.get("title", "")
        return {"ok": True, "active": not is_ended}
    except (json.JSONDecodeError, OSError):
        return {"ok": True, "active": False}
