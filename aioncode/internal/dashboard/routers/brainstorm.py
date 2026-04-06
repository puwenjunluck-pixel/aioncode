"""API routes for design brainstorm collaboration."""

from __future__ import annotations

import json
import time
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

from aioncode.internal.dashboard.config import (
    BRAINSTORM_DIR,
    BRAINSTORM_EVENTS_FILE,
    BRAINSTORM_SCREEN_FILE,
)
from aioncode.internal.dashboard.services.encoding import decode_project_path

router = APIRouter(tags=["brainstorm"])


class BrainstormEvent(BaseModel):

    type: str = "click"
    choice: str = ""


def _read_screen(project_path: str) -> dict | None:
    """Read and parse screen.json. Returns None if missing or invalid."""
    path = Path(project_path) / BRAINSTORM_DIR / BRAINSTORM_SCREEN_FILE
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


@router.get("/api/projects/{encoded}/brainstorm/screen")
async def brainstorm_screen(encoded: str) -> dict:
    """Read current brainstorm screen content."""
    project_path = decode_project_path(encoded)
    data = _read_screen(project_path)
    if data is None:
        return {"ok": True, "active": False, "screen": None}
    return {"ok": True, "active": True, "screen": data}


@router.post("/api/projects/{encoded}/brainstorm/event")
async def brainstorm_event(encoded: str, evt: BrainstormEvent) -> dict:
    """Append a user interaction event to events.jsonl."""
    project_path = decode_project_path(encoded)
    events_path = Path(project_path) / BRAINSTORM_DIR / BRAINSTORM_EVENTS_FILE
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
