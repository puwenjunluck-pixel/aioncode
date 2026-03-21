#!/usr/bin/env python3
"""
AionCode Session Digest — Auto-summarize events into session history.

Called by Claude Code Stop hook (after monitor-hook.sh).
Reads events.jsonl from last checkpoint, computes structured digest,
appends to sessions.jsonl. Zero dependencies, pure stdlib.

Must complete in <5 seconds.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_DIR = os.getcwd()
MONITOR_DIR = Path(PROJECT_DIR) / ".aion" / "monitor"
EVENTS_FILE = MONITOR_DIR / "events.jsonl"
SESSIONS_FILE = Path(PROJECT_DIR) / ".aion" / "sessions.jsonl"

MIN_TOOL_CALLS = 3  # skip noisy micro-sessions


def get_last_checkpoint() -> int:
    """Read checkpoint from last line of sessions.jsonl."""
    if not SESSIONS_FILE.exists():
        return 0
    try:
        text = SESSIONS_FILE.read_text(encoding="utf-8").strip()
        if not text:
            return 0
        last_line = text.split("\n")[-1].strip()
        if not last_line:
            return 0
        entry = json.loads(last_line)
        return entry.get("checkpoint", 0)
    except (json.JSONDecodeError, OSError):
        return 0


def read_events_from(checkpoint: int) -> list:
    """Read events.jsonl lines starting from checkpoint."""
    if not EVENTS_FILE.exists():
        return []
    events = []
    with open(EVENTS_FILE, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i < checkpoint:
                continue
            line = line.strip()
            if not line:
                continue
            try:
                events.append((i + 1, json.loads(line)))  # (line_number, event)
            except json.JSONDecodeError:
                continue
    return events


def count_total_lines() -> int:
    """Count total lines in events.jsonl."""
    if not EVENTS_FILE.exists():
        return 0
    with open(EVENTS_FILE, encoding="utf-8") as f:
        return sum(1 for _ in f)


def compute_digest(events: list) -> dict:
    """Compute structured digest from a batch of events."""
    tool_counts = {}
    files_changed = set()
    subagent_count = 0
    first_ts = None
    last_ts = None
    last_file = None
    last_tool = None
    max_line = 0

    for line_num, event in events:
        max_line = max(max_line, line_num)
        ts = event.get("ts", "")
        data = event.get("data", {})
        hook = data.get("hook_event_name", data.get("event", ""))

        if ts:
            if first_ts is None:
                first_ts = ts
            last_ts = ts

        if hook == "PreToolUse":
            tool = data.get("tool_name", "unknown")
            tool_counts[tool] = tool_counts.get(tool, 0) + 1
            last_tool = tool
            # Track file from tool input
            inp = data.get("tool_input", {})
            if isinstance(inp, dict):
                fp = inp.get("file_path") or inp.get("path") or inp.get("file")
                if fp:
                    last_file = fp

        elif hook == "PostToolUse":
            tool = data.get("tool_name", "")
            if tool in ("Write", "Edit", "NotebookEdit"):
                fp = data.get("tool_input", {}).get("file_path", "")
                if fp:
                    files_changed.add(fp)
                    last_file = fp

        elif hook == "SubagentStart":
            subagent_count += 1

    # Calculate duration
    duration_sec = 0
    if first_ts and last_ts and first_ts != last_ts:
        try:
            ft = first_ts.replace("Z", "+00:00") if first_ts.endswith("Z") else first_ts
            lt = last_ts.replace("Z", "+00:00") if last_ts.endswith("Z") else last_ts
            duration_sec = max(0, int((datetime.fromisoformat(lt) - datetime.fromisoformat(ft)).total_seconds()))
        except (ValueError, TypeError):
            pass

    return {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "duration_sec": duration_sec,
        "checkpoint": max_line,
        "tools": tool_counts,
        "files_changed": sorted(files_changed),
        "subagents": subagent_count,
        "ops": len(events),
        "last_file": last_file,
        "last_tool": last_tool,
    }


def main():
    # Exit silently if no events file
    if not EVENTS_FILE.exists():
        sys.exit(0)

    total_lines = count_total_lines()
    if total_lines == 0:
        sys.exit(0)

    checkpoint = get_last_checkpoint()

    # Reset checkpoint if events.jsonl was cleared/truncated
    if checkpoint > total_lines:
        checkpoint = 0

    events = read_events_from(checkpoint)
    if not events:
        sys.exit(0)

    # Count PreToolUse events — skip if < threshold
    pre_tool_count = sum(
        1
        for _, e in events
        if e.get("data", {}).get("hook_event_name", e.get("data", {}).get("event", "")) == "PreToolUse"
    )
    if pre_tool_count < MIN_TOOL_CALLS:
        sys.exit(0)

    digest = compute_digest(events)

    # Ensure .aion/ directory exists
    SESSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Append digest as JSONL
    with open(SESSIONS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(digest, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
