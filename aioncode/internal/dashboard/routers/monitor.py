"""API routes for monitor events and SSE streaming."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from aioncode.internal.dashboard.config import MONITOR_EVENTS_DIR, MONITOR_EVENTS_FILE
from aioncode.internal.dashboard.services.encoding import decode_project_path
from aioncode.internal.dashboard.services.monitor import (
    compute_monitor_state,
    read_monitor_events,
)

router = APIRouter(tags=["monitor"])

# --- Event icon mapping for recent events ---
_TOOL_ICONS = {
    "Edit": "✏️",
    "Write": "📝",
    "Read": "📖",
    "Bash": "💻",
    "Grep": "🔍",
    "Glob": "📁",
    "Agent": "🤖",
}


@router.get("/api/monitor/{encoded}/events")
async def monitor_events(encoded: str, since: int = Query(0)) -> dict:
    """Get monitor events since a given line number."""
    project_path = decode_project_path(encoded)
    events, total = read_monitor_events(project_path, since)
    return {"ok": True, "events": events, "total": total}


@router.get("/api/monitor/{encoded}/state")
async def monitor_state(encoded: str) -> dict:
    """Get computed aggregate monitor state."""
    project_path = decode_project_path(encoded)
    return compute_monitor_state(project_path)


@router.post("/api/monitor/{encoded}/clear")
async def monitor_clear(encoded: str) -> dict:
    """Clear monitor events."""
    project_path = decode_project_path(encoded)
    events_file = Path(project_path) / MONITOR_EVENTS_DIR / MONITOR_EVENTS_FILE
    if events_file.exists():
        events_file.write_text("", encoding="utf-8")
    return {"ok": True, "message": "Events cleared"}


@router.get("/api/projects/{encoded}/events/stream")
async def events_stream(encoded: str) -> StreamingResponse:
    """SSE endpoint for real-time event streaming."""
    project_path = decode_project_path(encoded)

    async def _event_generator():
        last_line = 0
        while True:
            events, total = read_monitor_events(project_path, last_line)
            for event in events:
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            last_line = total
            yield ": keepalive\n\n"
            await asyncio.sleep(2)

    return StreamingResponse(
        _event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/api/projects/{encoded}/events/recent")
async def recent_events(encoded: str, limit: int = Query(20)) -> dict:
    """Get recent events with formatted summaries."""
    project_path = decode_project_path(encoded)
    events, _total = read_monitor_events(project_path)

    # Take last N events
    recent = events[-limit:] if len(events) > limit else events
    recent.reverse()

    formatted = []
    for evt in recent:
        data = evt.get("data", evt)
        tool = data.get("tool_name", data.get("tool", ""))
        icon = _TOOL_ICONS.get(tool, "⚡")
        hook = data.get("hook_event_name", "")

        # Build summary
        summary = f"{icon} {tool}" if tool else hook
        tool_input = data.get("tool_input", {})
        if isinstance(tool_input, dict):
            fp = tool_input.get("file_path", "")
            if fp:
                summary += f" → {Path(fp).name}"
            cmd = tool_input.get("command", "")
            if cmd:
                summary += f" → {cmd[:80]}"

        formatted.append(
            {
                "ts": evt.get("ts", ""),
                "summary": summary,
                "tool": tool,
                "hook": hook,
            }
        )

    return {"ok": True, "events": formatted}
