"""Monitor event aggregation and state computation."""

from __future__ import annotations

import json
from pathlib import Path

from aioncode.internal.dashboard.config import MONITOR_EVENTS_DIR, MONITOR_EVENTS_FILE


def read_monitor_events(project_path: str, since: int = 0) -> tuple[list[dict], int]:
    """Read JSONL events from .aion/monitor/events.jsonl after line N.

    Returns:
        (events_list, total_line_count)
    """
    events_file = Path(project_path) / MONITOR_EVENTS_DIR / MONITOR_EVENTS_FILE
    if not events_file.exists():
        return [], 0

    try:
        lines = events_file.read_text(encoding="utf-8").splitlines()
    except OSError:
        return [], 0

    total = len(lines)
    events = []
    for line in lines[since:]:
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events, total


def compute_monitor_state(project_path: str) -> dict:
    """Parse all events and compute aggregate monitor state.

    Returns dict with session info, agent count, tool usage, files changed, etc.
    """
    events, total = read_monitor_events(project_path)
    if not events:
        return {
            "ok": True,
            "active": False,
            "total_events": 0,
            "session": None,
            "agents": [],
            "tools": {},
            "files_changed": [],
        }

    # Aggregate state from events
    tools: dict[str, int] = {}
    files_changed: set[str] = set()
    agents: list[dict] = []
    session_start = None
    last_ts = None

    for evt in events:
        data = evt.get("data", evt)
        ts = evt.get("ts", data.get("ts"))
        if ts:
            last_ts = ts
            if session_start is None:
                session_start = ts

        tool = data.get("tool_name", data.get("tool"))
        if tool:
            tools[tool] = tools.get(tool, 0) + 1

        # Track file changes from Edit/Write tools
        tool_input = data.get("tool_input", {})
        if isinstance(tool_input, dict):
            fp = tool_input.get("file_path", "")
            if fp and tool in ("Edit", "Write"):
                files_changed.add(fp)

        # Track subagents
        hook = data.get("hook_event_name", "")
        if hook in ("SubagentStart", "SubagentStarted"):
            agents.append(
                {
                    "type": data.get("subagent_type", "unknown"),
                    "description": data.get("description", ""),
                    "ts": ts,
                }
            )

    return {
        "ok": True,
        "active": True,
        "total_events": total,
        "session": {
            "start": session_start,
            "last_activity": last_ts,
        },
        "agents": agents[-10:],  # last 10 agents
        "tools": tools,
        "files_changed": sorted(files_changed),
    }
