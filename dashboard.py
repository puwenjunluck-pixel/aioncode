#!/usr/bin/env python3
"""
AionCode Dashboard — Local management UI for AionCode projects.

Single-file, zero-dependency Python web dashboard.
Manually add projects to manage their .aion/ scaffolds,
browse/edit files, and view project statistics.

Usage:
    python dashboard.py
    # Opens http://localhost:19200
"""

import base64
import http.server
import json
import os
import re
import shutil
import socketserver
import sys
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PORT = 19200
AION_DIRS = ["refs", "prototypes", "specs", "plans", "reviews", "contracts", "rules", "bugs"]
MARKER_START = "<!-- AIONCODE:START -->"
MARKER_END = "<!-- AIONCODE:END -->"

# Resolve source paths relative to this script
SCRIPT_DIR = Path(__file__).resolve().parent
COMMANDS_SRC = SCRIPT_DIR / "commands"
TEMPLATES_SRC = SCRIPT_DIR / "templates"
AION_TEMPLATE_DIR = TEMPLATES_SRC / "aion"
CLAUDE_MD_TPL = TEMPLATES_SRC / "CLAUDE.md.tpl"


# ---------------------------------------------------------------------------
# Project registry (JSON file persistence)
# ---------------------------------------------------------------------------

PROJECTS_FILE = SCRIPT_DIR / "projects.json"


def load_projects() -> List[dict]:
    """Load project list from JSON file, refresh status from disk."""
    if not PROJECTS_FILE.is_file():
        return []
    try:
        raw = json.loads(PROJECTS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    projects = []
    for entry in raw:
        path = entry.get("path", "")
        p = Path(path)
        if not p.is_dir():
            continue  # skip removed directories
        projects.append({
            "name": entry.get("name", p.name),
            "path": str(p.resolve()),
            "has_git": (p / ".git").is_dir(),
            "has_aion": (p / ".aion").is_dir(),
        })
    return projects


def save_projects(projects: List[dict]):
    """Persist project list to JSON file."""
    data = [{"name": p["name"], "path": p["path"]} for p in projects]
    PROJECTS_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def add_project(path: str) -> dict:
    """Add a project to the registry. Returns status dict."""
    resolved = Path(path).resolve()
    if not resolved.is_dir():
        return {"ok": False, "error": f"Directory not found: {resolved}"}

    projects = load_projects()
    # Check duplicate
    for p in projects:
        if p["path"] == str(resolved):
            return {"ok": False, "error": "Project already added"}

    projects.append({
        "name": resolved.name,
        "path": str(resolved),
        "has_git": (resolved / ".git").is_dir(),
        "has_aion": (resolved / ".aion").is_dir(),
    })
    projects.sort(key=lambda p: p["name"].lower())
    save_projects(projects)
    return {"ok": True, "name": resolved.name, "path": str(resolved)}


def remove_project(path: str) -> dict:
    """Remove a project from the registry (does NOT delete files)."""
    resolved = str(Path(path).resolve())
    projects = load_projects()
    before = len(projects)
    projects = [p for p in projects if p["path"] != resolved]
    if len(projects) == before:
        return {"ok": False, "error": "Project not found in registry"}
    save_projects(projects)
    return {"ok": True}


# ---------------------------------------------------------------------------
# Project initialization (mirrors install.sh)
# ---------------------------------------------------------------------------

def init_project(project_path: str) -> dict:
    """Initialize AionCode in a project directory. Returns status dict."""
    target = Path(project_path).resolve()
    if not target.is_dir():
        return {"ok": False, "error": f"Directory not found: {target}"}

    log = []

    # 1. Copy commands to .claude/commands/
    cmd_dst = target / ".claude" / "commands"
    cmd_dst.mkdir(parents=True, exist_ok=True)
    if COMMANDS_SRC.is_dir():
        for f in sorted(COMMANDS_SRC.glob("*.md")):
            dst = cmd_dst / f.name
            shutil.copy2(f, dst)
            log.append(f"Copied: .claude/commands/{f.name}")
    else:
        log.append(f"Warning: commands source not found at {COMMANDS_SRC}")

    # 2. Scaffold .aion/ (never overwrite existing files)
    aion_dst = target / ".aion"
    if AION_TEMPLATE_DIR.is_dir():
        for src_file in sorted(AION_TEMPLATE_DIR.rglob("*")):
            if not src_file.is_file():
                continue
            rel = src_file.relative_to(AION_TEMPLATE_DIR)
            dst_file = aion_dst / rel
            if dst_file.exists():
                log.append(f"Exists (skipped): .aion/{rel}")
            else:
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_file, dst_file)
                log.append(f"Created: .aion/{rel}")
    else:
        log.append(f"Warning: aion template not found at {AION_TEMPLATE_DIR}")

    # Create extra directories
    for d in AION_DIRS:
        dpath = aion_dst / d
        if dpath.is_dir():
            log.append(f"Exists (skipped): .aion/{d}/")
        else:
            dpath.mkdir(parents=True, exist_ok=True)
            log.append(f"Created: .aion/{d}/")

    # 3. Merge CLAUDE.md (idempotent via markers)
    claude_dst = target / "CLAUDE.md"
    tpl_content = ""
    if CLAUDE_MD_TPL.is_file():
        tpl_content = CLAUDE_MD_TPL.read_text(encoding="utf-8")

    if not claude_dst.exists():
        claude_dst.write_text(
            f"{MARKER_START}\n{tpl_content}\n{MARKER_END}\n",
            encoding="utf-8",
        )
        log.append("Created: CLAUDE.md")
    elif MARKER_START in claude_dst.read_text(encoding="utf-8"):
        # Replace section between markers
        original = claude_dst.read_text(encoding="utf-8")
        lines = original.split("\n")
        new_lines = []
        skipping = False
        for line in lines:
            if line.strip() == MARKER_START:
                new_lines.append(line)
                new_lines.append(tpl_content)
                skipping = True
                continue
            if line.strip() == MARKER_END:
                new_lines.append(line)
                skipping = False
                continue
            if not skipping:
                new_lines.append(line)
        claude_dst.write_text("\n".join(new_lines), encoding="utf-8")
        log.append("Updated: CLAUDE.md (replaced AionCode section)")
    else:
        with open(claude_dst, "a", encoding="utf-8") as f:
            f.write(f"\n{MARKER_START}\n{tpl_content}\n{MARKER_END}\n")
        log.append("Appended: AionCode section to CLAUDE.md")

    return {"ok": True, "log": log}


# ---------------------------------------------------------------------------
# Project statistics
# ---------------------------------------------------------------------------

def _count_rules_in_file(filepath: Path) -> int:
    """Count rule entries (lines starting with '- **') in a markdown file."""
    if not filepath.is_file():
        return 0
    try:
        content = filepath.read_text(encoding="utf-8")
        # Strip HTML comments to avoid counting format templates
        content = re.sub(r"<!--[\s\S]*?-->", "", content)
        return len(re.findall(r"^- \*\*", content, re.MULTILINE))
    except Exception:
        return 0


def _count_files_in_dir(dirpath: Path, extensions: tuple = (".md", ".yml", ".yaml", ".txt")) -> int:
    """Count files in a directory."""
    if not dirpath.is_dir():
        return 0
    count = 0
    for f in dirpath.iterdir():
        if f.is_file() and (not extensions or f.suffix.lower() in extensions):
            count += 1
    return count


def _last_activity(changelog_path: Path) -> Optional[str]:
    """Extract last activity date from changelog.md."""
    if not changelog_path.is_file():
        return None
    try:
        content = changelog_path.read_text(encoding="utf-8")
        # Look for date patterns like 2026-03-20 or ## 2026-03-20
        dates = re.findall(r"\d{4}-\d{2}-\d{2}", content)
        if dates:
            return dates[-1]
    except Exception:
        pass
    return None


def get_project_stats(project_path: str) -> dict:
    """Compute statistics for a project."""
    aion = Path(project_path) / ".aion"
    if not aion.is_dir():
        return {"installed": False}

    pitfalls = _count_rules_in_file(aion / "rules" / "pitfalls.md")
    style = _count_rules_in_file(aion / "rules" / "style.md")
    perf = _count_rules_in_file(aion / "rules" / "perf.md")

    # Read installed version
    installed_version = "0.0"
    config_file = aion / "config.yml"
    if config_file.is_file():
        for line in config_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("version:"):
                installed_version = line.split('"')[1] if '"' in line else line.split(":")[1].strip()
                break

    # Read source (latest) version
    source_version = "0.0"
    src_config = AION_TEMPLATE_DIR / "config.yml"
    if src_config.is_file():
        for line in src_config.read_text(encoding="utf-8").splitlines():
            if line.startswith("version:"):
                source_version = line.split('"')[1] if '"' in line else line.split(":")[1].strip()
                break

    return {
        "installed": True,
        "installed_version": installed_version,
        "source_version": source_version,
        "upgrade_available": installed_version != source_version,
        "rules_total": pitfalls + style + perf,
        "rules_pitfalls": pitfalls,
        "rules_style": style,
        "rules_perf": perf,
        "specs_count": _count_files_in_dir(aion / "specs"),
        "plans_count": _count_files_in_dir(aion / "plans"),
        "reviews_count": _count_files_in_dir(aion / "reviews"),
        "refs_count": _count_files_in_dir(aion / "refs"),
        "prototypes_count": _count_files_in_dir(aion / "prototypes"),
        "contracts_count": _count_files_in_dir(aion / "contracts"),
        "bugs_count": _count_files_in_dir(aion / "bugs"),
        "last_activity": _last_activity(aion / "changelog.md"),
    }


# ---------------------------------------------------------------------------
# File tree & operations (restricted to .aion/)
# ---------------------------------------------------------------------------

def _validate_aion_path(project_path: str, relative_path: str) -> Optional[Path]:
    """Validate that a file path stays within .aion/. Returns resolved path or None."""
    aion_root = Path(project_path).resolve() / ".aion"
    # Normalize and resolve to prevent traversal
    target = (aion_root / relative_path).resolve()
    try:
        target.relative_to(aion_root)
    except ValueError:
        return None
    return target


def get_file_tree(project_path: str) -> List[dict]:
    """Build a file tree of the .aion/ directory."""
    aion_root = Path(project_path).resolve() / ".aion"
    if not aion_root.is_dir():
        return []

    def _build(directory: Path, prefix: str = "") -> List[dict]:
        items = []
        try:
            entries = sorted(directory.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower()))
        except PermissionError:
            return items

        for entry in entries:
            rel = f"{prefix}{entry.name}" if prefix else entry.name
            if entry.is_dir():
                children = _build(entry, f"{rel}/")
                items.append({
                    "name": entry.name,
                    "path": rel,
                    "type": "dir",
                    "children": children,
                })
            elif entry.is_file():
                items.append({
                    "name": entry.name,
                    "path": rel,
                    "type": "file",
                    "size": entry.stat().st_size,
                    "mtime": datetime.fromtimestamp(entry.stat().st_mtime).isoformat(),
                })
        return items

    return _build(aion_root)


def read_file(project_path: str, relative_path: str) -> dict:
    """Read a file from .aion/."""
    target = _validate_aion_path(project_path, relative_path)
    if target is None:
        return {"ok": False, "error": "Invalid path (traversal blocked)"}
    if not target.is_file():
        return {"ok": False, "error": f"File not found: {relative_path}"}
    try:
        content = target.read_text(encoding="utf-8")
        return {"ok": True, "content": content, "path": relative_path}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def write_file(project_path: str, relative_path: str, content: str) -> dict:
    """Write/update a file in .aion/."""
    target = _validate_aion_path(project_path, relative_path)
    if target is None:
        return {"ok": False, "error": "Invalid path (traversal blocked)"}
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return {"ok": True, "path": relative_path}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def delete_file(project_path: str, relative_path: str) -> dict:
    """Delete a file from .aion/."""
    target = _validate_aion_path(project_path, relative_path)
    if target is None:
        return {"ok": False, "error": "Invalid path (traversal blocked)"}
    if not target.is_file():
        return {"ok": False, "error": f"File not found: {relative_path}"}
    try:
        target.unlink()
        return {"ok": True, "path": relative_path}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def create_file(project_path: str, relative_path: str, content: str = "") -> dict:
    """Create a new file in .aion/."""
    target = _validate_aion_path(project_path, relative_path)
    if target is None:
        return {"ok": False, "error": "Invalid path (traversal blocked)"}
    if target.exists():
        return {"ok": False, "error": f"File already exists: {relative_path}"}
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return {"ok": True, "path": relative_path}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ---------------------------------------------------------------------------
# Path encoding helpers
# ---------------------------------------------------------------------------

def encode_project_path(path: str) -> str:
    """Base64-encode a project path for use in URLs."""
    return base64.urlsafe_b64encode(path.encode("utf-8")).decode("ascii")


def decode_project_path(encoded: str) -> str:
    """Decode a base64-encoded project path."""
    # Add padding if needed
    padding = 4 - len(encoded) % 4
    if padding != 4:
        encoded += "=" * padding
    return base64.urlsafe_b64decode(encoded.encode("ascii")).decode("utf-8")


# ---------------------------------------------------------------------------
# Monitor: event aggregation
# ---------------------------------------------------------------------------

MONITOR_EVENTS_DIR = ".aion/monitor"
MONITOR_EVENTS_FILE = "events.jsonl"


def read_monitor_events(project_path: str, since: int = 0):
    """Read events from JSONL file, returning entries after line `since`."""
    events_file = Path(project_path) / MONITOR_EVENTS_DIR / MONITOR_EVENTS_FILE
    events = []
    total = 0
    if events_file.exists():
        with open(events_file, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                total = i + 1
                if i >= since:
                    line = line.strip()
                    if line:
                        try:
                            events.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
    return {"events": events, "total": total}


def compute_monitor_state(project_path: str) -> dict:
    """Parse all events and compute aggregate state."""
    state = {
        "project_dir": project_path,
        "session_id": None,
        "session_start": None,
        "main_agent": {"status": "STANDBY", "current_tool": None, "current_file": None},
        "subagents": {},
        "tool_counts": {},
        "files_changed": [],
        "total_events": 0,
        "uptime_seconds": 0,
    }
    events_file = Path(project_path) / MONITOR_EVENTS_DIR / MONITOR_EVENTS_FILE
    if not events_file.exists():
        return state

    files_set = set()
    with open(events_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            state["total_events"] += 1
            data = event.get("data", {})
            hook = data.get("hook_event_name", data.get("event", ""))
            ts = event.get("ts", "")

            if not state["session_id"]:
                state["session_id"] = data.get("session_id")
                state["session_start"] = ts

            if hook == "PreToolUse":
                tool = data.get("tool_name", "unknown")
                state["main_agent"]["status"] = "ACTIVE"
                state["main_agent"]["current_tool"] = tool
                inp = data.get("tool_input", {})
                if isinstance(inp, dict):
                    fp = inp.get("file_path") or inp.get("path") or inp.get("file")
                    if fp:
                        state["main_agent"]["current_file"] = fp
                state["tool_counts"][tool] = state["tool_counts"].get(tool, 0) + 1
            elif hook == "PostToolUse":
                tool = data.get("tool_name", "")
                if tool in ("Write", "Edit", "NotebookEdit"):
                    fp = data.get("tool_input", {}).get("file_path", "")
                    if fp:
                        files_set.add(fp)
            elif hook == "SubagentStart":
                aid = data.get("agent_id", data.get("session_id", f"sub-{len(state['subagents'])}"))
                state["subagents"][aid] = {
                    "id": aid,
                    "type": data.get("agent_type", data.get("subagent_type", data.get("description", "general"))),
                    "status": "ACTIVE",
                    "started": ts,
                }
            elif hook == "SubagentStop":
                aid = data.get("agent_id", data.get("session_id", ""))
                if aid in state["subagents"]:
                    state["subagents"][aid]["status"] = "RETURNED"
            elif hook == "Stop":
                state["main_agent"]["status"] = "IDLE"
                state["main_agent"]["current_tool"] = None
            elif hook == "SessionStart":
                state["session_id"] = data.get("session_id")
                state["session_start"] = ts
            elif hook == "SessionEnd":
                state["main_agent"]["status"] = "OFFLINE"

    if state["session_start"]:
        try:
            ss = state["session_start"]
            if ss.endswith("Z"):
                ss = ss[:-1] + "+00:00"
            start = datetime.fromisoformat(ss)
            state["uptime_seconds"] = max(0, int((datetime.now(timezone.utc) - start).total_seconds()))
        except (ValueError, TypeError):
            pass

    state["files_changed"] = sorted(files_set)
    state["subagents"] = list(state["subagents"].values())
    return state


# ---------------------------------------------------------------------------
# Bug management helpers
# ---------------------------------------------------------------------------

BUGS_DIR = ".aion/bugs"
TEAM_FILE = ".aion/team.yml"


def _parse_bug_frontmatter(filepath: Path) -> Optional[dict]:
    """Parse YAML frontmatter from a bug report markdown file."""
    try:
        text = filepath.read_text(encoding="utf-8")
    except OSError:
        return None
    if not text.startswith("---"):
        return None
    end = text.find("---", 3)
    if end == -1:
        return None
    fm = {}
    for line in text[3:end].strip().splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            val = val.strip().strip('"').strip("'")
            fm[key.strip()] = val
    fm["_file"] = filepath.name
    return fm


def list_bugs(project_path: str, filters: Optional[dict] = None) -> List[dict]:
    """List bug reports from .aion/bugs/, optionally filtered."""
    bugs_dir = Path(project_path) / BUGS_DIR
    if not bugs_dir.is_dir():
        return []
    bugs = []
    for f in sorted(bugs_dir.glob("*.md")):
        fm = _parse_bug_frontmatter(f)
        if fm is None:
            continue
        # Apply filters
        if filters:
            if "category" in filters:
                cat = filters["category"].upper()
                if not fm.get("id", "").startswith(cat):
                    continue
            if "status" in filters and fm.get("status") != filters["status"]:
                continue
            if "assignee" in filters and filters["assignee"] not in fm.get("assignee", ""):
                continue
            if "severity" in filters and fm.get("severity") != filters["severity"]:
                continue
        # Compute stale hours
        created = fm.get("created_at", "")
        if created:
            try:
                created_dt = datetime.strptime(created, "%Y-%m-%d")
                delta = datetime.now() - created_dt
                fm["stale_hours"] = int(delta.total_seconds() / 3600)
            except ValueError:
                fm["stale_hours"] = 0
        bugs.append(fm)
    return bugs


def get_bug_stats(project_path: str) -> dict:
    """Compute bug statistics for a project."""
    bugs = list_bugs(project_path)
    stats = {
        "total": len(bugs),
        "by_status": {},
        "by_category": {"F": 0, "B": 0, "X": 0},
        "by_severity": {},
        "financial_risk": 0,
        "team_load": {},
        "longest_open": None,
    }
    for b in bugs:
        st = b.get("status", "open")
        stats["by_status"][st] = stats["by_status"].get(st, 0) + 1
        sev = b.get("severity", "medium")
        stats["by_severity"][sev] = stats["by_severity"].get(sev, 0) + 1
        bid = b.get("id", "")
        if bid.startswith("F"):
            stats["by_category"]["F"] += 1
        elif bid.startswith("B"):
            stats["by_category"]["B"] += 1
        elif bid.startswith("X"):
            stats["by_category"]["X"] += 1
        if b.get("risk_level") == "financial":
            stats["financial_risk"] += 1
        assignee = b.get("assignee", "")
        if assignee and st in ("assigned", "in-progress"):
            stats["team_load"][assignee] = stats["team_load"].get(assignee, 0) + 1
        # Track longest open
        if st not in ("closed", "verified"):
            hours = b.get("stale_hours", 0)
            if stats["longest_open"] is None or hours > stats["longest_open"].get("stale_hours", 0):
                stats["longest_open"] = {"id": bid, "title": b.get("title", ""), "stale_hours": hours}
    return stats


def read_team_config(project_path: str) -> dict:
    """Read team.yml from a project."""
    team_file = Path(project_path) / TEAM_FILE
    if not team_file.is_file():
        return {"team": [], "models": [], "risk_keywords": {}}
    try:
        text = team_file.read_text(encoding="utf-8")
    except OSError:
        return {"team": [], "models": [], "risk_keywords": {}}
    # Simple YAML-like parser for team.yml (avoid external dependency)
    # For full YAML, users would need PyYAML; we parse the essential structure
    result: Dict = {"team": [], "models": [], "risk_keywords": {"critical": [], "low": []}}
    current_section = None
    current_item: Optional[dict] = None
    current_list_key = None
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        # Top-level keys
        if not line.startswith(" ") and not line.startswith("\t"):
            # Flush pending item before switching sections
            if current_item is not None and current_section in ("team", "models"):
                result[current_section].append(current_item)
                current_item = None
            if stripped.startswith("team:"):
                current_section = "team"
                current_list_key = None
            elif stripped.startswith("models:"):
                current_section = "models"
                current_list_key = None
            elif stripped.startswith("risk_keywords:"):
                current_section = "risk_keywords"
                current_list_key = None
            continue
        # Inside sections
        if current_section == "team" or current_section == "models":
            if stripped.startswith("- name:") or stripped.startswith("- name :"):
                if current_item is not None:
                    result[current_section].append(current_item)
                val = stripped.split(":", 1)[1].strip()
                current_item = {"name": val}
                current_list_key = None
            elif current_item is not None and ":" in stripped and not stripped.startswith("-"):
                key, _, val = stripped.partition(":")
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if val == "[]":
                    current_item[key] = []
                elif val.isdigit():
                    current_item[key] = int(val)
                else:
                    current_item[key] = val
                current_list_key = None
            elif current_item is not None and stripped.startswith("- ") and current_list_key:
                current_item.setdefault(current_list_key, []).append(stripped[2:].strip())
        elif current_section == "risk_keywords":
            if stripped.startswith("critical:"):
                current_list_key = "critical"
            elif stripped.startswith("low:"):
                current_list_key = "low"
            elif stripped.startswith("- ") and current_list_key:
                result["risk_keywords"].setdefault(current_list_key, []).append(stripped[2:].strip())
    # Don't forget last item
    if current_item is not None and current_section in ("team", "models"):
        result[current_section].append(current_item)
    return result


def write_team_config(project_path: str, config: dict) -> dict:
    """Write team.yml to a project."""
    team_file = Path(project_path) / TEAM_FILE
    # Ensure parent directory exists
    team_file.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# AionCode Team Configuration",
        "# Managed via Dashboard or manually edited.",
        "",
    ]
    # Team section
    team = config.get("team", [])
    if not team:
        lines.append("team: []")
    else:
        lines.append("team:")
        for member in team:
            lines.append(f"  - name: {member.get('name', '')}")
            lines.append(f"    role: {member.get('role', 'fullstack')}")
            lines.append(f"    git_email: {member.get('git_email', '')}")
            lines.append(f"    expertise: {member.get('expertise', '[]')}")
            lines.append(f"    active_bugs: {member.get('active_bugs', 0)}")
            lines.append("")
    lines.append("")
    # Models section
    models = config.get("models", [])
    if not models:
        lines.append("models: []")
    else:
        lines.append("models:")
        for model in models:
            lines.append(f"  - name: {model.get('name', '')}")
            lines.append(f"    provider: {model.get('provider', '')}")
            lines.append(f"    endpoint: {model.get('endpoint', '')}")
            lines.append(f"    api_key_env: {model.get('api_key_env', '')}")
            lines.append(f"    default_model: {model.get('default_model', '')}")
            lines.append("")
    lines.append("")
    # Risk keywords
    rk = config.get("risk_keywords", {})
    lines.append("risk_keywords:")
    lines.append("  critical:")
    for kw in rk.get("critical", []):
        lines.append(f"    - {kw}")
    lines.append("  low:")
    for kw in rk.get("low", []):
        lines.append(f"    - {kw}")
    lines.append("")
    team_file.write_text("\n".join(lines), encoding="utf-8")
    return {"ok": True}


def is_admin(request=None) -> bool:
    """Check if the current request has admin privileges.
    Phase 1: Always returns True (local deployment, everyone is admin).
    Phase 2+: Will check team.yml role via git config or auth token.
    """
    return True


# ---------------------------------------------------------------------------
# HTTP Request Handler
# ---------------------------------------------------------------------------

# Global state
_cached_projects: Optional[List[dict]] = None


def _reload():
    global _cached_projects
    _cached_projects = load_projects()


class DashboardHandler(http.server.BaseHTTPRequestHandler):
    """HTTP handler for the AionCode Dashboard."""

    def log_message(self, format, *args):
        """Suppress default request logging for cleaner output."""
        pass

    # -- Routing -----------------------------------------------------------

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")
        query = dict(urllib.parse.parse_qsl(parsed.query))

        if path == "" or path == "/":
            self._serve_html()
        elif path == "/api/projects":
            self._handle_list_projects()
        # -- Bug stats (must come before generic /stats) --
        elif path.startswith("/api/projects/") and path.endswith("/bugs/stats"):
            encoded = path[len("/api/projects/"):-len("/bugs/stats")]
            self._handle_bug_stats(encoded)
        elif path.startswith("/api/projects/") and path.endswith("/stats"):
            encoded = path[len("/api/projects/"):-len("/stats")]
            self._handle_stats(encoded)
        elif path.startswith("/api/projects/") and path.endswith("/files"):
            encoded = path[len("/api/projects/"):-len("/files")]
            self._handle_file_tree(encoded)
        elif path.startswith("/api/projects/") and path.endswith("/file"):
            encoded = path[len("/api/projects/"):-len("/file")]
            self._handle_read_file(encoded, query)
        elif path == "/api/browse":
            self._handle_browse(query)
        elif path == "/api/commands":
            self._handle_list_commands()
        elif path.startswith("/api/commands/"):
            name = path[len("/api/commands/"):]
            self._handle_read_command(name)
        elif path.startswith("/api/projects/") and path.endswith("/sessions"):
            encoded = path[len("/api/projects/"):-len("/sessions")]
            self._handle_sessions(encoded, query)
        elif path.startswith("/api/projects/") and path.endswith("/changelog"):
            encoded = path[len("/api/projects/"):-len("/changelog")]
            self._handle_changelog(encoded, query)
        # -- Monitor routes --
        elif path.startswith("/monitor/"):
            encoded = path[len("/monitor/"):]
            self._serve_monitor_html(encoded)
        elif path.startswith("/api/monitor/") and path.endswith("/events"):
            encoded = path[len("/api/monitor/"):-len("/events")]
            self._handle_monitor_events(encoded, query)
        elif path.startswith("/api/monitor/") and path.endswith("/state"):
            encoded = path[len("/api/monitor/"):-len("/state")]
            self._handle_monitor_state(encoded)
        elif path.startswith("/api/projects/") and path.endswith("/events/stream"):
            encoded = path[len("/api/projects/"):-len("/events/stream")]
            self._handle_events_stream(encoded)
        elif path.startswith("/api/projects/") and path.endswith("/events/recent"):
            encoded = path[len("/api/projects/"):-len("/events/recent")]
            self._handle_recent_events(encoded, query)
        # -- Bug routes --
        elif path.startswith("/api/projects/") and path.endswith("/bugs"):
            encoded = path[len("/api/projects/"):-len("/bugs")]
            self._handle_list_bugs(encoded, query)
        # -- Team/Admin routes --
        elif path.startswith("/api/projects/") and path.endswith("/team"):
            encoded = path[len("/api/projects/"):-len("/team")]
            self._handle_read_team(encoded)
        else:
            self._json_response(404, {"error": "Not found"})

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path == "/api/projects/add":
            body = self._read_json_body()
            if body is None:
                return
            self._handle_add_project(body)
        elif path == "/api/projects/remove":
            body = self._read_json_body()
            if body is None:
                return
            self._handle_remove_project(body)
        elif path == "/api/projects/init":
            body = self._read_json_body()
            if body is None:
                return
            self._handle_init_project(body)
        elif path.startswith("/api/projects/") and path.endswith("/file"):
            encoded = path[len("/api/projects/"):-len("/file")]
            body = self._read_json_body()
            if body is None:
                return
            self._handle_create_file(encoded, body)
        # -- Monitor routes --
        elif path.startswith("/api/monitor/") and path.endswith("/clear"):
            encoded = path[len("/api/monitor/"):-len("/clear")]
            self._handle_monitor_clear(encoded)
        # -- Team/Admin routes --
        elif path.startswith("/api/projects/") and path.endswith("/team"):
            encoded = path[len("/api/projects/"):-len("/team")]
            body = self._read_json_body()
            if body is None:
                return
            self._handle_write_team(encoded, body)
        # -- Upgrade route --
        elif path.startswith("/api/projects/") and path.endswith("/upgrade"):
            encoded = path[len("/api/projects/"):-len("/upgrade")]
            self._handle_upgrade_project(encoded)
        else:
            self._json_response(404, {"error": "Not found"})

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path.startswith("/api/projects/") and path.endswith("/file"):
            encoded = path[len("/api/projects/"):-len("/file")]
            body = self._read_json_body()
            if body is None:
                return
            self._handle_write_file(encoded, body)
        else:
            self._json_response(404, {"error": "Not found"})

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path.startswith("/api/projects/") and path.endswith("/file"):
            encoded = path[len("/api/projects/"):-len("/file")]
            query = dict(urllib.parse.parse_qsl(parsed.query))
            self._handle_delete_file(encoded, query)
        else:
            self._json_response(404, {"error": "Not found"})

    # -- Handlers ----------------------------------------------------------

    def _handle_list_commands(self):
        """List all AionCode command files from the source commands/ directory."""
        cmds = []
        if COMMANDS_SRC.is_dir():
            for f in sorted(COMMANDS_SRC.glob("*.md")):
                # Extract first line as title, second non-empty line as description
                try:
                    lines = f.read_text(encoding="utf-8").split("\n")
                    title = ""
                    desc = ""
                    for line in lines:
                        line_s = line.strip()
                        if not title and line_s.startswith("# "):
                            title = line_s[2:].strip()
                        elif title and not desc and line_s and not line_s.startswith("#") and not line_s.startswith("$"):
                            desc = line_s
                            break
                    cmds.append({
                        "name": f.stem,
                        "filename": f.name,
                        "title": title,
                        "description": desc,
                    })
                except Exception:
                    cmds.append({"name": f.stem, "filename": f.name, "title": f.stem, "description": ""})
        self._json_response(200, {"commands": cmds})

    def _handle_read_command(self, name: str):
        """Read a specific command file content."""
        # Sanitize name
        safe_name = name.replace("/", "").replace("\\", "").replace("..", "")
        if not safe_name.endswith(".md"):
            safe_name += ".md"
        target = COMMANDS_SRC / safe_name
        if not target.is_file():
            self._json_response(404, {"error": f"Command not found: {safe_name}"})
            return
        try:
            content = target.read_text(encoding="utf-8")
            self._json_response(200, {"ok": True, "name": safe_name, "content": content})
        except Exception as e:
            self._json_response(500, {"error": str(e)})

    def _handle_browse(self, query: dict):
        """Browse directories on the filesystem for the folder picker."""
        target = query.get("path", "")
        if not target:
            target = str(Path.home())
        target_path = Path(target).resolve()
        if not target_path.is_dir():
            self._json_response(400, {"error": "Not a directory"})
            return
        dirs = []
        try:
            for entry in sorted(target_path.iterdir(), key=lambda e: e.name.lower()):
                if not entry.is_dir():
                    continue
                name = entry.name
                # Skip hidden dirs (except common ones) and system dirs
                if name.startswith(".") and name not in (".aion",):
                    continue
                if name in ("node_modules", "__pycache__", "venv", ".venv", "Library", "Applications"):
                    continue
                has_git = (entry / ".git").is_dir()
                has_aion = (entry / ".aion").is_dir()
                dirs.append({
                    "name": name,
                    "path": str(entry),
                    "has_git": has_git,
                    "has_aion": has_aion,
                })
        except PermissionError:
            pass
        parent = str(target_path.parent) if target_path != target_path.parent else None
        self._json_response(200, {
            "current": str(target_path),
            "parent": parent,
            "dirs": dirs,
        })

    def _handle_list_projects(self):
        _reload()
        self._json_response(200, {"projects": _cached_projects})

    def _handle_add_project(self, body: dict):
        project_path = body.get("path", "")
        if not project_path:
            self._json_response(400, {"error": "Missing 'path'"})
            return
        result = add_project(project_path)
        self._json_response(200 if result["ok"] else 400, result)

    def _handle_remove_project(self, body: dict):
        project_path = body.get("path", "")
        if not project_path:
            self._json_response(400, {"error": "Missing 'path'"})
            return
        result = remove_project(project_path)
        self._json_response(200 if result["ok"] else 400, result)

    def _handle_init_project(self, body: dict):
        project_path = body.get("path", "")
        if not project_path:
            self._json_response(400, {"error": "Missing 'path'"})
            return
        resolved = str(Path(project_path).resolve())
        result = init_project(resolved)
        if result["ok"]:
            _reload()
        self._json_response(200 if result["ok"] else 500, result)

    def _handle_stats(self, encoded: str):
        try:
            project_path = decode_project_path(encoded)
        except Exception:
            self._json_response(400, {"error": "Invalid project path encoding"})
            return
        stats = get_project_stats(project_path)
        self._json_response(200, stats)

    def _handle_file_tree(self, encoded: str):
        try:
            project_path = decode_project_path(encoded)
        except Exception:
            self._json_response(400, {"error": "Invalid project path encoding"})
            return
        tree = get_file_tree(project_path)
        self._json_response(200, {"tree": tree})

    def _handle_read_file(self, encoded: str, query: dict):
        try:
            project_path = decode_project_path(encoded)
        except Exception:
            self._json_response(400, {"error": "Invalid project path encoding"})
            return
        file_path = query.get("path", "")
        if not file_path:
            self._json_response(400, {"error": "Missing 'path' query parameter"})
            return
        result = read_file(project_path, file_path)
        self._json_response(200 if result["ok"] else 404, result)

    def _handle_write_file(self, encoded: str, body: dict):
        try:
            project_path = decode_project_path(encoded)
        except Exception:
            self._json_response(400, {"error": "Invalid project path encoding"})
            return
        file_path = body.get("path", "")
        content = body.get("content", "")
        if not file_path:
            self._json_response(400, {"error": "Missing 'path'"})
            return
        result = write_file(project_path, file_path, content)
        self._json_response(200 if result["ok"] else 400, result)

    def _handle_create_file(self, encoded: str, body: dict):
        try:
            project_path = decode_project_path(encoded)
        except Exception:
            self._json_response(400, {"error": "Invalid project path encoding"})
            return
        file_path = body.get("path", "")
        content = body.get("content", "")
        if not file_path:
            self._json_response(400, {"error": "Missing 'path'"})
            return
        result = create_file(project_path, file_path, content)
        self._json_response(200 if result["ok"] else 400, result)

    def _handle_delete_file(self, encoded: str, query: dict):
        try:
            project_path = decode_project_path(encoded)
        except Exception:
            self._json_response(400, {"error": "Invalid project path encoding"})
            return
        file_path = query.get("path", "")
        if not file_path:
            self._json_response(400, {"error": "Missing 'path' query parameter"})
            return
        result = delete_file(project_path, file_path)
        self._json_response(200 if result["ok"] else 400, result)

    # -- Monitor Handlers --------------------------------------------------

    def _serve_monitor_html(self, encoded: str):
        try:
            project_path = decode_project_path(encoded)
        except Exception:
            self._json_response(400, {"error": "Invalid project path encoding"})
            return
        html = MONITOR_HTML.replace("__ENCODED__", encoded)
        html = html.replace("__PROJECT_NAME__", Path(project_path).name)
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle_monitor_events(self, encoded: str, query: dict):
        try:
            project_path = decode_project_path(encoded)
        except Exception:
            self._json_response(400, {"error": "Invalid project path encoding"})
            return
        since = int(query.get("since", "0"))
        result = read_monitor_events(project_path, since)
        self._json_response(200, result)

    def _handle_sessions(self, encoded: str, query: dict):
        try:
            project_path = decode_project_path(encoded)
        except Exception:
            self._json_response(400, {"error": "Invalid project path encoding"})
            return
        limit = int(query.get("limit", "10"))
        sessions_file = Path(project_path) / ".aion" / "sessions.jsonl"
        entries = []
        if sessions_file.exists():
            for line in sessions_file.read_text(encoding="utf-8").strip().split("\n"):
                if line.strip():
                    try:
                        entries.append(json.loads(line))
                    except (json.JSONDecodeError, ValueError):
                        pass
        self._json_response(200, {"sessions": entries[-limit:][::-1]})

    def _handle_changelog(self, encoded: str, query: dict):
        try:
            project_path = decode_project_path(encoded)
        except Exception:
            self._json_response(400, {"error": "Invalid project path encoding"})
            return
        limit = int(query.get("limit", "20"))
        changelog_file = Path(project_path) / ".aion" / "changelog.md"
        entries = []
        if changelog_file.exists():
            content = changelog_file.read_text(encoding="utf-8")
            # Parse changelog entries separated by "## " or "---"
            current = None
            for line in content.split("\n"):
                if line.startswith("## ") and "|" in line:
                    if current:
                        current["body"] = current["body"].strip()
                        entries.append(current)
                    # Format: ## 2026-03-21 17:00 | feat: description
                    header = line[3:].strip()
                    parts = header.split("|", 1)
                    date_str = parts[0].strip()
                    summary = parts[1].strip() if len(parts) > 1 else ""
                    current = {"date": date_str, "summary": summary, "body": ""}
                elif current is not None and line.strip() != "---":
                    current["body"] += line + "\n"
            if current:
                current["body"] = current["body"].strip()
                entries.append(current)
        entries.reverse()
        self._json_response(200, {"entries": entries[:limit], "total": len(entries)})

    def _handle_monitor_state(self, encoded: str):
        try:
            project_path = decode_project_path(encoded)
        except Exception:
            self._json_response(400, {"error": "Invalid project path encoding"})
            return
        state = compute_monitor_state(project_path)
        self._json_response(200, state)

    def _handle_monitor_clear(self, encoded: str):
        try:
            project_path = decode_project_path(encoded)
        except Exception:
            self._json_response(400, {"error": "Invalid project path encoding"})
            return
        events_file = Path(project_path) / MONITOR_EVENTS_DIR / MONITOR_EVENTS_FILE
        if events_file.exists():
            events_file.write_text("")
        self._json_response(200, {"status": "cleared"})

    def _handle_events_stream(self, encoded: str):
        """SSE endpoint: streams new events from events.jsonl in real-time."""
        try:
            project_path = decode_project_path(encoded)
        except Exception:
            self._json_response(400, {"error": "Invalid project path encoding"})
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        events_file = Path(project_path) / MONITOR_EVENTS_DIR / MONITOR_EVENTS_FILE
        last_line = 0
        try:
            import time as _time
            while True:
                if events_file.exists():
                    with open(events_file, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                    total = len(lines)
                    if total > last_line:
                        for i in range(last_line, total):
                            line = lines[i].strip()
                            if line:
                                try:
                                    event = json.loads(line)
                                    sse_data = json.dumps(event, ensure_ascii=False)
                                    self.wfile.write(f"data: {sse_data}\n\n".encode("utf-8"))
                                except json.JSONDecodeError:
                                    pass
                        self.wfile.flush()
                        last_line = total
                # Send keepalive comment every cycle
                self.wfile.write(b": keepalive\n\n")
                self.wfile.flush()
                _time.sleep(2)
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass  # Client disconnected

    def _handle_recent_events(self, encoded: str, query: dict):
        """Return the most recent N events for a project, formatted for dashboard display."""
        try:
            project_path = decode_project_path(encoded)
        except Exception:
            self._json_response(400, {"error": "Invalid project path encoding"})
            return
        limit = int(query.get("limit", "20"))
        events_file = Path(project_path) / MONITOR_EVENTS_DIR / MONITOR_EVENTS_FILE
        events = []
        if events_file.exists():
            try:
                file_size = events_file.stat().st_size
                # For large files, only read the tail
                with open(events_file, "r", encoding="utf-8") as f:
                    if file_size > 1_000_000:  # > 1MB, read last 200KB
                        f.seek(max(0, file_size - 200_000))
                        f.readline()  # skip partial line
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                events.append(json.loads(line))
                            except json.JSONDecodeError:
                                pass
            except OSError:
                pass
        # Return only the most recent N
        recent = events[-limit:][::-1]
        # Summarize each event for dashboard display
        summary = []
        for ev in recent:
            data = ev.get("data", {})
            hook = data.get("hook_event_name", data.get("event", ""))
            ts = ev.get("ts", "")
            tool = data.get("tool_name", "")
            desc = ""
            icon = ""
            if hook == "PreToolUse":
                inp = data.get("tool_input", {})
                fp = ""
                if isinstance(inp, dict):
                    fp = inp.get("file_path") or inp.get("path") or inp.get("command", "")
                desc = f"{tool}"
                if fp:
                    desc += f" → {Path(fp).name if '/' in str(fp) else fp}"
                icon = "tool"
            elif hook == "PostToolUse":
                desc = f"{tool} completed"
                icon = "done"
            elif hook == "SubagentStart":
                agent_type = data.get("agent_type", data.get("subagent_type", data.get("description", "")))
                desc = f"Subagent: {agent_type}"
                icon = "agent"
            elif hook == "SubagentStop":
                desc = "Subagent returned"
                icon = "agent_done"
            elif hook == "Stop":
                desc = "Session cycle complete"
                icon = "stop"
            elif hook == "SessionStart":
                desc = "Session started"
                icon = "start"
            elif hook == "SessionEnd":
                desc = "Session ended"
                icon = "end"
            else:
                desc = hook or "unknown"
                icon = "info"
            summary.append({"ts": ts, "type": hook, "desc": desc, "icon": icon, "tool": tool})
        self._json_response(200, {"events": summary, "total": len(events)})

    # -- Bug & Team handlers ------------------------------------------------

    def _handle_list_bugs(self, encoded: str, query: dict):
        """List bugs for a project with optional filters."""
        try:
            project_path = decode_project_path(encoded)
        except Exception:
            self._json_response(400, {"error": "Invalid project path"})
            return
        filters = {}
        for key in ("category", "status", "assignee", "severity"):
            if key in query:
                filters[key] = query[key]
        bugs = list_bugs(project_path, filters if filters else None)
        self._json_response(200, {"bugs": bugs, "total": len(bugs)})

    def _handle_bug_stats(self, encoded: str):
        """Return bug statistics for a project."""
        try:
            project_path = decode_project_path(encoded)
        except Exception:
            self._json_response(400, {"error": "Invalid project path"})
            return
        stats = get_bug_stats(project_path)
        self._json_response(200, stats)

    def _handle_read_team(self, encoded: str):
        """Read team.yml for a project."""
        try:
            project_path = decode_project_path(encoded)
        except Exception:
            self._json_response(400, {"error": "Invalid project path"})
            return
        config = read_team_config(project_path)
        self._json_response(200, config)

    def _handle_write_team(self, encoded: str, body: dict):
        """Write team.yml for a project (admin only)."""
        if not is_admin():
            self._json_response(403, {"error": "Admin access required"})
            return
        try:
            project_path = decode_project_path(encoded)
        except Exception:
            self._json_response(400, {"error": "Invalid project path"})
            return
        result = write_team_config(project_path, body)
        self._json_response(200, result)

    # -- Upgrade handler ---------------------------------------------------

    def _handle_upgrade_project(self, encoded: str):
        """Execute install.sh --upgrade for a project."""
        if not is_admin():
            self._json_response(403, {"error": "Admin access required"})
            return
        try:
            project_path = decode_project_path(encoded)
        except Exception:
            self._json_response(400, {"error": "Invalid project path"})
            return
        import subprocess
        install_script = SCRIPT_DIR / "install.sh"
        if not install_script.is_file():
            self._json_response(500, {"error": "install.sh not found"})
            return
        try:
            result = subprocess.run(
                ["bash", str(install_script), "--upgrade", project_path],
                capture_output=True, text=True, timeout=30
            )
            _reload()  # refresh project cache
            self._json_response(200, {
                "ok": result.returncode == 0,
                "output": result.stdout,
                "errors": result.stderr,
            })
        except subprocess.TimeoutExpired:
            self._json_response(500, {"error": "Upgrade timed out"})
        except Exception as e:
            self._json_response(500, {"error": str(e)})

    # -- Helpers -----------------------------------------------------------

    def _read_json_body(self) -> Optional[dict]:
        try:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length)
            return json.loads(raw) if raw else {}
        except (ValueError, json.JSONDecodeError) as e:
            self._json_response(400, {"error": f"Invalid JSON: {e}"})
            return None

    def _json_response(self, status: int, data: dict):
        body = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def _serve_html(self):
        body = HTML_PAGE.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


# ---------------------------------------------------------------------------
# Embedded Frontend
# ---------------------------------------------------------------------------

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AionCode 管理面板</title>
<style>
/* ===== Reset & Base ===== */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body { height: 100%; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
  background: #0d1117;
  color: #e6edf3;
  font-size: 14px;
  line-height: 1.5;
  overflow: hidden;
}
a { color: #8b5cf6; text-decoration: none; }
a:hover { text-decoration: underline; }

/* ===== Scrollbar ===== */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: #0d1117; }
::-webkit-scrollbar-thumb { background: #30363d; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #484f58; }

/* ===== Layout ===== */
#app {
  display: flex;
  flex-direction: column;
  height: 100vh;
}
header {
  display: flex;
  align-items: center;
  padding: 0 20px;
  height: 48px;
  min-height: 48px;
  background: #161b22;
  border-bottom: 1px solid #30363d;
  gap: 12px;
}
header .logo {
  font-size: 16px;
  font-weight: 700;
  color: #8b5cf6;
  letter-spacing: -0.3px;
}
header .nav-tabs {
  display: flex;
  gap: 2px;
  margin-left: 16px;
}
header .nav-tab {
  background: none;
  border: none;
  color: #8b949e;
  padding: 6px 14px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.15s;
}
header .nav-tab:hover { background: #1c2128; color: #e6edf3; }
header .nav-tab.active { background: #1c2128; color: #8b5cf6; font-weight: 600; }
header .spacer {
  flex: 1;
}
header .refresh-btn {
  background: none;
  border: 1px solid #30363d;
  color: #8b949e;
  padding: 4px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.15s;
}
header .refresh-btn:hover {
  border-color: #8b5cf6;
  color: #e6edf3;
}

.main-layout {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* ===== Sidebar (Projects) ===== */
.sidebar {
  width: 240px;
  min-width: 240px;
  background: #0d1117;
  border-right: 1px solid #30363d;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px 8px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #8b949e;
}
.btn-add-project {
  background: none;
  border: 1px solid #30363d;
  color: #8b949e;
  width: 22px;
  height: 22px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}
.btn-add-project:hover { border-color: #8b5cf6; color: #e6edf3; }
.sidebar-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 8px 8px;
}
.project-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s;
  font-size: 13px;
}
.project-item:hover { background: #1c2128; }
.project-item.active { background: #1c2128; border-left: 2px solid #7c3aed; }
.project-item .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.project-item .dot.green { background: #3fb950; }
.project-item .dot.gray { background: #484f58; }
.project-item .name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.project-item .btn-remove {
  background: none;
  border: none;
  color: transparent;
  cursor: pointer;
  font-size: 14px;
  padding: 0 2px;
  line-height: 1;
  transition: color 0.15s;
  flex-shrink: 0;
}
.project-item:hover .btn-remove { color: #484f58; }
.project-item .btn-remove:hover { color: #f85149; }

/* ===== Content Area ===== */
.content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.content-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #484f58;
  font-size: 16px;
  flex-direction: column;
  gap: 8px;
}
.content-empty .hint { font-size: 13px; color: #30363d; }

/* ===== Stats Row ===== */
.stats-row {
  display: flex;
  gap: 12px;
  padding: 16px 20px;
  flex-wrap: wrap;
  min-height: fit-content;
  border-bottom: 1px solid #30363d;
  background: #0d1117;
}
.stat-card {
  flex: 1;
  min-width: 140px;
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 8px;
  padding: 14px 16px;
}
.stat-card .label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #8b949e;
  margin-bottom: 4px;
}
.stat-card .value {
  font-size: 24px;
  font-weight: 700;
  color: #e6edf3;
}
.stat-card .sub {
  font-size: 11px;
  color: #8b949e;
  margin-top: 2px;
}
.stat-card.accent .value { color: #8b5cf6; }

/* ===== Sessions Row ===== */
.sessions-row {
  padding: 12px 20px;
  border-bottom: 1px solid #30363d;
  background: #0d1117;
}
.sessions-header {
  font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;
  color: #8b949e; margin-bottom: 8px;
}
.session-item {
  display: flex; align-items: center; gap: 10px;
  padding: 5px 0; font-size: 12px; color: #c9d1d9;
}
.session-dot {
  width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0;
}
.dot-today { background: #3fb950; }
.dot-past { background: #484f58; }
.session-time { width: 50px; color: #8b949e; flex-shrink: 0; }
.session-dur { width: 35px; color: #8b949e; flex-shrink: 0; }
.session-tools { flex: 1; color: #8b5cf6; font-family: 'SF Mono', 'Fira Code', monospace; font-size: 11px; }
.session-file { color: #58a6ff; font-size: 11px; text-align: right; }
.session-empty { font-size: 12px; color: #484f58; padding: 4px 0; }

/* ===== Log Center ===== */
.log-tab-bar { display: flex; gap: 4px; }
.log-tab {
  background: transparent; border: 1px solid #30363d; color: #8b949e;
  padding: 4px 12px; border-radius: 6px; cursor: pointer; font-size: 12px;
}
.log-tab:hover { border-color: #58a6ff; color: #c9d1d9; }
.log-tab.active { background: #1f6feb; border-color: #1f6feb; color: #fff; }
.log-section { margin-bottom: 24px; }
.log-section-title {
  font-size: 13px; font-weight: 600; color: #8b949e; text-transform: uppercase;
  letter-spacing: 0.5px; margin-bottom: 12px; padding-bottom: 8px;
  border-bottom: 1px solid #21262d; display: flex; align-items: center; gap: 8px;
}
.log-section-title .badge {
  background: #30363d; color: #8b949e; padding: 1px 8px; border-radius: 10px;
  font-size: 11px; font-weight: 400;
}
.log-entry {
  padding: 10px 14px; margin-bottom: 6px; border-radius: 8px;
  background: #161b22; border: 1px solid #21262d; font-size: 13px;
}
.log-entry:hover { border-color: #30363d; }
.log-entry-header { display: flex; align-items: center; gap: 10px; margin-bottom: 4px; }
.log-entry-date { color: #8b949e; font-size: 12px; font-family: 'SF Mono', monospace; flex-shrink: 0; }
.log-entry-type {
  font-size: 11px; padding: 1px 8px; border-radius: 4px; font-weight: 500;
}
.log-type-changelog { background: #1a3a2a; color: #3fb950; }
.log-type-session { background: #1a2a3a; color: #58a6ff; }
.log-type-event { background: #2a1a3a; color: #8b5cf6; }
.log-entry-summary { color: #e6edf3; font-weight: 500; }
.log-entry-body { color: #8b949e; font-size: 12px; margin-top: 6px; line-height: 1.5; }
.log-entry-body code { background: #21262d; padding: 1px 5px; border-radius: 3px; font-size: 11px; }
.log-entry-meta { display: flex; gap: 12px; color: #484f58; font-size: 11px; margin-top: 4px; }

/* ===== Live Activity Feed ===== */
.activity-row {
  padding: 12px 20px;
  border-bottom: 1px solid #30363d;
  background: #0d1117;
}
.activity-header {
  display: flex; align-items: center; justify-content: space-between;
  font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;
  color: #8b949e; margin-bottom: 8px;
}
.activity-live-dot {
  width: 6px; height: 6px; border-radius: 50%; background: #3fb950;
  display: inline-block; margin-right: 6px;
  animation: livePulse 2s ease-in-out infinite;
}
.activity-live-dot.offline { background: #484f58; animation: none; }
@keyframes livePulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}
.activity-list { max-height: 140px; overflow-y: auto; }
.activity-item {
  display: flex; align-items: center; gap: 8px;
  padding: 4px 0; font-size: 12px; color: #c9d1d9;
  border-bottom: 1px solid #161b22;
}
.activity-icon {
  width: 20px; text-align: center; flex-shrink: 0; font-size: 13px;
}
.activity-time {
  width: 55px; color: #8b949e; flex-shrink: 0; font-size: 11px;
  font-family: 'SF Mono', 'Fira Code', monospace;
}
.activity-desc { flex: 1; }
.activity-desc .tool-name { color: #8b5cf6; }
.activity-desc .file-name { color: #58a6ff; }
.activity-empty { font-size: 12px; color: #484f58; padding: 4px 0; }
.activity-count {
  font-size: 10px; color: #484f58; font-weight: normal;
  text-transform: none; letter-spacing: 0;
}

/* ===== Init Panel ===== */
.init-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 16px;
  padding: 40px;
}
.init-panel .title {
  font-size: 18px;
  font-weight: 600;
}
.init-panel .desc {
  color: #8b949e;
  text-align: center;
  max-width: 400px;
  line-height: 1.6;
}
.init-panel .btn-install {
  background: #7c3aed;
  color: #fff;
  border: none;
  padding: 10px 28px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
}
.init-panel .btn-install:hover { background: #6d28d9; }
.init-panel .btn-install:disabled { opacity: 0.5; cursor: not-allowed; }
.init-log {
  margin-top: 16px;
  max-width: 520px;
  width: 100%;
  max-height: 300px;
  overflow-y: auto;
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 8px;
  padding: 12px 16px;
  font-size: 12px;
  font-family: 'SF Mono', 'Fira Code', monospace;
  color: #3fb950;
  white-space: pre-wrap;
  display: none;
}
.init-log.visible { display: block; }

/* ===== File Browser Area ===== */
.browser-area {
  display: flex;
  flex: 1;
  min-height: 300px;
  overflow: hidden;
}

/* File Tree */
.file-tree-panel {
  width: 260px;
  min-width: 260px;
  border-right: 1px solid #30363d;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #0d1117;
}
.file-tree-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  border-bottom: 1px solid #30363d;
  font-size: 12px;
  font-weight: 600;
  color: #8b949e;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.file-tree-header .btn-new {
  background: none;
  border: 1px solid #30363d;
  color: #8b949e;
  padding: 2px 10px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 11px;
  transition: all 0.15s;
}
.file-tree-header .btn-new:hover {
  border-color: #8b5cf6;
  color: #e6edf3;
}
.file-tree-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 6px 0;
}
.tree-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 14px;
  cursor: pointer;
  font-size: 13px;
  transition: background 0.1s;
  white-space: nowrap;
}
.tree-item:hover { background: #1c2128; }
.tree-item.active { background: #1c2128; color: #8b5cf6; }
.tree-item .icon { color: #8b949e; font-size: 12px; flex-shrink: 0; width: 16px; text-align: center; }
.tree-item.dir .icon { color: #d29922; }
.tree-item .fname {
  overflow: hidden;
  text-overflow: ellipsis;
}

/* File Editor */
.file-editor-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.editor-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-bottom: 1px solid #30363d;
  background: #161b22;
  min-height: 44px;
}
.editor-toolbar .file-name {
  flex: 1;
  font-size: 13px;
  font-weight: 600;
  color: #e6edf3;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.editor-toolbar .file-meta {
  font-size: 11px;
  color: #484f58;
  margin-left: 8px;
  font-weight: 400;
}
.editor-toolbar button {
  background: none;
  border: 1px solid #30363d;
  color: #8b949e;
  padding: 4px 14px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.15s;
}
.editor-toolbar button:hover { border-color: #8b5cf6; color: #e6edf3; }
.editor-toolbar button.primary {
  background: #7c3aed;
  border-color: #7c3aed;
  color: #fff;
}
.editor-toolbar button.primary:hover { background: #6d28d9; }
.editor-toolbar button.danger:hover { border-color: #f85149; color: #f85149; }

.editor-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
}

/* Markdown rendered view */
.md-view {
  line-height: 1.7;
  color: #e6edf3;
}
.md-view h1 { font-size: 24px; font-weight: 700; margin: 20px 0 10px; padding-bottom: 6px; border-bottom: 1px solid #30363d; }
.md-view h2 { font-size: 20px; font-weight: 600; margin: 18px 0 8px; padding-bottom: 4px; border-bottom: 1px solid #21262d; }
.md-view h3 { font-size: 16px; font-weight: 600; margin: 14px 0 6px; }
.md-view h4 { font-size: 14px; font-weight: 600; margin: 12px 0 4px; color: #8b949e; }
.md-view p { margin: 8px 0; }
.md-view ul, .md-view ol { margin: 8px 0; padding-left: 24px; }
.md-view li { margin: 4px 0; }
.md-view code {
  background: #1c2128;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 13px;
  color: #f0883e;
}
.md-view pre {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 8px;
  padding: 14px 16px;
  overflow-x: auto;
  margin: 10px 0;
}
.md-view pre code {
  background: none;
  padding: 0;
  color: #e6edf3;
  font-size: 13px;
}
.md-view hr {
  border: none;
  border-top: 1px solid #30363d;
  margin: 16px 0;
}
.md-view strong { color: #fff; }
.md-view blockquote {
  border-left: 3px solid #30363d;
  padding-left: 14px;
  color: #8b949e;
  margin: 8px 0;
}
.md-view a { color: #8b5cf6; }

/* Textarea (edit mode) */
.editor-textarea {
  width: 100%;
  height: 100%;
  background: #0d1117;
  color: #e6edf3;
  border: none;
  padding: 16px 20px;
  font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
  font-size: 13px;
  line-height: 1.6;
  resize: none;
  outline: none;
  tab-size: 2;
}

.editor-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #484f58;
  font-size: 14px;
}

/* ===== Toast ===== */
.toast-container {
  position: fixed;
  top: 16px;
  right: 16px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.toast {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 8px;
  padding: 10px 16px;
  font-size: 13px;
  color: #e6edf3;
  min-width: 240px;
  max-width: 400px;
  animation: toast-in 0.2s ease;
  box-shadow: 0 8px 24px rgba(0,0,0,0.4);
}
.toast.success { border-left: 3px solid #3fb950; }
.toast.error { border-left: 3px solid #f85149; }
.toast.info { border-left: 3px solid #8b5cf6; }
@keyframes toast-in {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ===== Modal ===== */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.modal {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 12px;
  padding: 24px;
  min-width: 380px;
  max-width: 560px;
  width: 90vw;
  box-shadow: 0 16px 48px rgba(0,0,0,0.5);
}
.modal h3 { margin-bottom: 12px; font-size: 16px; }
.modal p { color: #8b949e; margin-bottom: 16px; font-size: 13px; }
.modal input, .modal select {
  width: 100%;
  background: #0d1117;
  border: 1px solid #30363d;
  color: #e6edf3;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 13px;
  margin-bottom: 12px;
  outline: none;
}
.modal input:focus, .modal select:focus { border-color: #8b5cf6; }
.modal .modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 16px;
}
.modal .modal-actions button {
  padding: 8px 20px;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  border: 1px solid #30363d;
  background: none;
  color: #8b949e;
  transition: all 0.15s;
}
.modal .modal-actions button:hover { border-color: #8b5cf6; color: #e6edf3; }
.modal .modal-actions button.primary {
  background: #7c3aed;
  border-color: #7c3aed;
  color: #fff;
}
.modal .modal-actions button.primary:hover { background: #6d28d9; }
.modal .modal-actions button.danger {
  background: #da3633;
  border-color: #da3633;
  color: #fff;
}
.modal .modal-actions button.danger:hover { background: #f85149; }

/* ===== Command Page ===== */
.cmd-viewer {
  flex: 1; overflow-y: auto; padding: 24px 32px;
}
.cmd-viewer .cmd-header {
  font-size: 22px; font-weight: 700; color: #e6edf3; margin-bottom: 4px;
}
.cmd-viewer .cmd-desc {
  font-size: 14px; color: #8b949e; margin-bottom: 20px;
}
.cmd-viewer .cmd-body {
  line-height: 1.7; color: #e6edf3;
}
.cmd-viewer .cmd-body h1 { font-size: 22px; font-weight: 700; margin: 20px 0 10px; padding-bottom: 6px; border-bottom: 1px solid #30363d; }
.cmd-viewer .cmd-body h2 { font-size: 18px; font-weight: 600; margin: 24px 0 10px; padding-bottom: 4px; border-bottom: 1px solid #21262d; color: #8b5cf6; }
.cmd-viewer .cmd-body h3 { font-size: 15px; font-weight: 600; margin: 18px 0 8px; }
.cmd-viewer .cmd-body h4 { font-size: 14px; font-weight: 600; margin: 14px 0 6px; color: #8b949e; }
.cmd-viewer .cmd-body p { margin: 8px 0; }
.cmd-viewer .cmd-body ul, .cmd-viewer .cmd-body ol { margin: 8px 0; padding-left: 24px; }
.cmd-viewer .cmd-body li { margin: 4px 0; }
.cmd-viewer .cmd-body code {
  background: #1c2128; padding: 2px 6px; border-radius: 4px;
  font-family: 'SF Mono','Fira Code',monospace; font-size: 13px; color: #f0883e;
}
.cmd-viewer .cmd-body pre {
  background: #161b22; border: 1px solid #30363d; border-radius: 8px;
  padding: 14px 16px; overflow-x: auto; margin: 10px 0;
}
.cmd-viewer .cmd-body pre code { background: none; padding: 0; color: #e6edf3; font-size: 13px; }
.cmd-viewer .cmd-body blockquote {
  border-left: 3px solid #d29922; padding: 10px 14px; margin: 12px 0;
  background: #161b22; border-radius: 0 6px 6px 0; color: #e6edf3;
}
.cmd-viewer .cmd-body table { width: 100%; border-collapse: collapse; margin: 12px 0; }
.cmd-viewer .cmd-body th {
  text-align: left; padding: 8px 12px; background: #161b22;
  border-bottom: 2px solid #30363d; font-size: 12px; color: #8b949e;
}
.cmd-viewer .cmd-body td {
  padding: 8px 12px; border-bottom: 1px solid #21262d; font-size: 13px;
}
.cmd-viewer .cmd-body tr:hover td { background: #1c2128; }
.cmd-viewer .cmd-body strong { color: #fff; }
.cmd-viewer .cmd-body hr { border: none; border-top: 1px solid #30363d; margin: 16px 0; }
.cmd-item { font-size: 12px; }
.cmd-item .cmd-subtitle { font-size: 11px; color: #484f58; margin-top: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

/* ===== Guide / Help Page ===== */
.guide-page {
  padding: 40px 56px 80px;
  max-width: 1100px; margin: 0 auto;
}
.guide-page h1 {
  font-size: 32px; font-weight: 800; color: #e6edf3; margin-bottom: 8px;
  background: linear-gradient(135deg, #e6edf3 0%, #8b5cf6 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.guide-page .subtitle { font-size: 15px; color: #8b949e; margin-bottom: 40px; }
.guide-page h2 {
  font-size: 20px; font-weight: 700; color: #e6edf3; margin: 48px 0 20px;
  display: flex; align-items: center; gap: 10px;
}
.guide-page h2::before {
  content: ''; display: inline-block; width: 4px; height: 22px;
  background: linear-gradient(180deg, #8b5cf6, #58a6ff); border-radius: 2px;
}
.guide-page h3 { font-size: 16px; font-weight: 600; color: #e6edf3; margin: 20px 0 10px; }
.guide-page p { color: #c9d1d9; line-height: 1.7; margin: 8px 0; }
.guide-page ul, .guide-page ol { color: #c9d1d9; padding-left: 24px; margin: 8px 0; line-height: 1.8; }
.guide-page li { margin: 6px 0; }
.guide-page li strong { color: #e6edf3; }
.guide-page code {
  background: #1c2128; padding: 2px 6px; border-radius: 4px;
  font-family: 'SF Mono','Fira Code',monospace; font-size: 13px; color: #f0883e;
}
.guide-page pre {
  background: #161b22; border: 1px solid #30363d; border-radius: 8px;
  padding: 16px; overflow-x: auto; margin: 12px 0;
}
.guide-page pre code { background: none; padding: 0; color: #e6edf3; display: block; }
.guide-page .tip-box {
  background: linear-gradient(135deg, rgba(139,92,246,0.08) 0%, rgba(88,166,255,0.06) 100%);
  border: 1px solid rgba(139,92,246,0.25); border-radius: 12px;
  padding: 18px 22px; margin: 20px 0;
}
.guide-page .tip-box .tip-label { font-weight: 700; color: #8b5cf6; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }
.guide-page .warn-box {
  background: linear-gradient(135deg, rgba(210,153,34,0.08) 0%, rgba(210,153,34,0.04) 100%);
  border: 1px solid rgba(210,153,34,0.25); border-radius: 12px;
  padding: 18px 22px; margin: 20px 0;
}
.guide-page .warn-box .warn-label { font-weight: 700; color: #d29922; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }
.guide-page .cmd-table { width: 100%; border-collapse: collapse; margin: 16px 0; }
.guide-page .cmd-table th {
  text-align: left; padding: 12px 16px; background: #161b22;
  border-bottom: 2px solid #30363d; font-size: 12px; color: #8b949e;
  text-transform: uppercase; letter-spacing: 0.5px;
}
.guide-page .cmd-table td {
  padding: 10px 16px; border-bottom: 1px solid #21262d; font-size: 13px; color: #c9d1d9;
}
.guide-page .cmd-table tr:hover td { background: #1c2128; }
.guide-page .flywheel {
  text-align: center; padding: 28px; margin: 24px 0;
  background: linear-gradient(135deg, rgba(139,92,246,0.1) 0%, rgba(88,166,255,0.08) 100%);
  border: 1px solid rgba(139,92,246,0.3); border-radius: 16px;
  font-family: 'SF Mono','Fira Code',monospace; font-size: 15px; color: #8b949e; line-height: 2.2;
}
.guide-page .flywheel .highlight { color: #8b5cf6; font-weight: 700; }

/* Role cards grid */
.role-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; margin: 20px 0; }
.role-card {
  background: #161b22; border: 1px solid #30363d; border-radius: 12px;
  padding: 22px 24px; transition: border-color 0.2s, transform 0.2s;
}
.role-card:hover { border-color: #8b5cf6; transform: translateY(-2px); }
.role-card .role-icon { font-size: 28px; margin-bottom: 12px; }
.role-card .role-title { font-size: 16px; font-weight: 700; color: #e6edf3; margin-bottom: 6px; }
.role-card .role-desc { font-size: 13px; color: #8b949e; margin-bottom: 14px; line-height: 1.5; }
.role-card ul { padding-left: 18px; margin: 0; }
.role-card li { font-size: 13px; color: #c9d1d9; margin: 6px 0; line-height: 1.6; }
.role-card li strong { color: #e6edf3; }

/* Scenario cards */
.scenario-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 16px; margin: 20px 0; }
.guide-page .scenario-box {
  background: #0d1117; border: 1px solid #21262d; border-radius: 12px;
  padding: 22px 24px; margin: 0; transition: border-color 0.2s;
}
.guide-page .scenario-box:hover { border-color: #58a6ff; }
.guide-page .scenario-box .scenario-label {
  font-weight: 700; color: #58a6ff; font-size: 15px; margin-bottom: 10px;
  padding-bottom: 8px; border-bottom: 1px solid #21262d;
}
.guide-page .scenario-box p { font-size: 13px; line-height: 1.7; }
.guide-page .scenario-box ol { font-size: 13px; margin: 8px 0; }
.guide-page .scenario-box .key-principle {
  margin-top: 12px; padding: 10px 14px; border-radius: 8px;
  background: rgba(139,92,246,0.08); border: 1px solid rgba(139,92,246,0.15);
  font-size: 13px; color: #c9d1d9;
}
.guide-page .scenario-box .key-principle strong { color: #8b5cf6; }

/* Collab cards */
.collab-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; margin: 20px 0; }
.collab-card {
  background: #161b22; border: 1px solid #30363d; border-radius: 12px;
  padding: 20px 22px; transition: border-color 0.2s;
}
.collab-card:hover { border-color: #3fb950; }
.collab-card .collab-title { font-size: 15px; font-weight: 700; color: #e6edf3; margin-bottom: 10px; }
.collab-card p { font-size: 13px; color: #c9d1d9; line-height: 1.7; margin: 0; }
.collab-card strong { color: #3fb950; }

/* Help Center: narrower for readability */
.help-page { max-width: 860px; }
.help-page h2 { margin-top: 36px; }
.help-two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin: 16px 0; }
@media (max-width: 900px) { .help-two-col { grid-template-columns: 1fr; } }

/* ===== Folder Picker ===== */
.folder-picker { display: flex; flex-direction: column; gap: 8px; }
.folder-picker .fp-path-bar {
  display: flex; align-items: center; gap: 6px;
  background: #0d1117; border: 1px solid #30363d; border-radius: 6px;
  padding: 6px 10px; font-size: 12px; color: #8b949e;
  font-family: 'SF Mono','Fira Code',monospace;
  overflow: hidden; white-space: nowrap; text-overflow: ellipsis;
}
.folder-picker .fp-path-bar .fp-path-text { flex: 1; overflow: hidden; text-overflow: ellipsis; }
.folder-picker .fp-path-bar button {
  background: none; border: 1px solid #30363d; color: #8b949e;
  padding: 2px 8px; border-radius: 4px; cursor: pointer; font-size: 11px;
  flex-shrink: 0; transition: all 0.15s;
}
.folder-picker .fp-path-bar button:hover { border-color: #8b5cf6; color: #e6edf3; }
.folder-picker .fp-list {
  max-height: 320px; overflow-y: auto;
  background: #0d1117; border: 1px solid #30363d; border-radius: 6px;
}
.folder-picker .fp-item {
  display: flex; align-items: center; gap: 8px;
  padding: 7px 12px; cursor: pointer; font-size: 13px;
  transition: background 0.1s; border-bottom: 1px solid #21262d;
}
.folder-picker .fp-item:last-child { border-bottom: none; }
.folder-picker .fp-item:hover { background: #1c2128; }
.folder-picker .fp-item.selected { background: #1c2128; color: #8b5cf6; }
.folder-picker .fp-item .fp-icon { color: #d29922; font-size: 14px; flex-shrink: 0; }
.folder-picker .fp-item .fp-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.folder-picker .fp-item .fp-badge {
  font-size: 10px; padding: 1px 6px; border-radius: 3px;
  background: #1c2128; color: #8b949e; flex-shrink: 0;
}
.folder-picker .fp-item .fp-badge.git { color: #f0883e; }
.folder-picker .fp-item .fp-badge.aion { color: #3fb950; }
.folder-picker .fp-empty {
  padding: 20px; text-align: center; color: #484f58; font-size: 13px;
}

/* ===== Responsive ===== */
@media (max-width: 900px) {
  .sidebar { width: 180px; min-width: 180px; }
  .file-tree-panel { width: 200px; min-width: 200px; }
}
</style>
</head>
<body>
<div id="app">
  <header>
    <div class="logo">AionCode</div>
    <div class="nav-tabs">
      <button class="nav-tab active" id="tabProjects" onclick="switchPage('projects')">项目管理</button>
      <button class="nav-tab" id="tabBugs" onclick="switchPage('bugs')">Bug 看板</button>
      <button class="nav-tab" id="tabAdmin" onclick="switchPage('admin')">团队管理</button>
      <button class="nav-tab" id="tabCommands" onclick="switchPage('commands')">命令管理</button>
      <button class="nav-tab" id="tabLogs" onclick="switchPage('logs')">日志中心</button>
      <button class="nav-tab" id="tabGuide" onclick="switchPage('guide')">最佳实践</button>
      <button class="nav-tab" id="tabHelp" onclick="switchPage('help')">帮助中心</button>
    </div>
    <div class="spacer"></div>
    <button class="refresh-btn" id="btnRefresh" onclick="loadProjects()">刷新</button>
  </header>
  <!-- Projects Page -->
  <div class="main-layout" id="pageProjects">
    <aside class="sidebar">
      <div class="sidebar-header">
        <span>项目</span>
        <button class="btn-add-project" onclick="showAddProjectModal()">+</button>
      </div>
      <div class="sidebar-list" id="projectList"></div>
    </aside>
    <main class="content" id="mainContent">
      <div class="content-empty">
        <div>选择一个项目开始</div>
        <div class="hint">点击左侧 + 添加项目</div>
      </div>
    </main>
  </div>
  <!-- Commands Page -->
  <div id="pageCommands" style="display:none;flex:1;overflow:hidden;">
    <div class="main-layout">
      <aside class="sidebar">
        <div class="sidebar-header"><span>命令列表</span></div>
        <div class="sidebar-list" id="cmdList"><div style="padding:16px;color:#484f58;font-size:13px;">加载中...</div></div>
      </aside>
      <main class="content" id="cmdContent">
        <div class="content-empty">
          <div>选择一个命令查看 Prompt</div>
          <div class="hint">左侧列出所有 AionCode 命令</div>
        </div>
      </main>
    </div>
  </div>
  <!-- Guide Page -->
  <div id="pageGuide" style="display:none;flex:1;overflow-y:auto;">
    <div class="guide-page">

      <h1>AionCode 最佳实践</h1>
      <p class="subtitle">从不同角色和真实场景出发，帮你找到最适合的 AI 协作方式。具体命令用法请见「帮助中心」。</p>

      <h2>核心理念：让 AI 越用越聪明</h2>
      <p>大多数 AI 编程工具每次对话都从零开始。AionCode 不同 &mdash; 它有一个<strong>学习飞轮</strong>：</p>
      <div class="flywheel">
        编写代码 &rarr; <span class="highlight">审查发现问题</span> &rarr; <span class="highlight">沉淀为规则</span> &rarr; 下次自动避免<br>
        &uarr; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&darr;<br>
        &larr;&larr;&larr; 同样的错误不再重犯 &larr;&larr;&larr;&larr;&larr;&larr;&larr;&larr;&larr;&larr;
      </div>

      <div class="tip-box">
        <div class="tip-label">核心洞察</div>
        <p>规则一旦被提取，<strong>每次会话都会自动加载</strong>，不需要你做任何事。第一周你可能有 0 条规则，一个月后可能有 20 条 &mdash; 这时候 AI 已经像一个了解项目历史的老员工。</p>
      </div>

      <h2>不同角色怎么用</h2>
      <div class="role-grid">
        <div class="role-card">
          <div class="role-icon">&#x1F527;</div>
          <div class="role-title">后端开发者</div>
          <div class="role-desc">写 API、处理数据库、解决并发问题</div>
          <ul>
            <li><strong>写完代码一定要审查</strong> &mdash; 审查是规则积累的唯一入口，跳过 = 放弃学习</li>
            <li><strong>接口约定写成文档</strong> &mdash; 放到共享目录，前端 AI 自动读取</li>
            <li><strong>声明工作范围</strong> &mdash; 标注"后端"，防止与前端文件冲突</li>
            <li><strong>调完 bug 必提炼</strong> &mdash; 2 小时的定位 = 10 秒的规则 = 永不再犯</li>
          </ul>
        </div>
        <div class="role-card">
          <div class="role-icon">&#x1F3A8;</div>
          <div class="role-title">前端开发者</div>
          <div class="role-desc">写组件、调样式、对接 API</div>
          <ul>
            <li><strong>先出原型再写代码</strong> &mdash; AI 生成可交互原型，确认后再实现</li>
            <li><strong>对照合约开发</strong> &mdash; AI 自动读取接口文档，按约定生成</li>
            <li><strong>声明工作范围</strong> &mdash; 标注"前端"，同功能互不覆盖</li>
            <li><strong>关注无障碍</strong> &mdash; AI 自动扫描模板，找出 a11y 问题</li>
          </ul>
        </div>
        <div class="role-card">
          <div class="role-icon">&#x1F50D;</div>
          <div class="role-title">测试工程师</div>
          <div class="role-desc">找 bug、写测试、验证修复</div>
          <ul>
            <li><strong>先扫描再补测试</strong> &mdash; AI 分析覆盖率，有针对性地补</li>
            <li><strong>多 AI 交叉验证</strong> &mdash; 换个 AI 审查，盲点更少</li>
            <li><strong>Bug 报告标准化</strong> &mdash; 统一格式，自动定位责任人</li>
            <li><strong>edge case 为王</strong> &mdash; 好测试验证行为，不验证实现</li>
          </ul>
        </div>
        <div class="role-card">
          <div class="role-icon">&#x1F4CA;</div>
          <div class="role-title">技术负责人</div>
          <div class="role-desc">团队效率、代码质量、项目健康度</div>
          <ul>
            <li><strong>定期检查规则质量</strong> &mdash; 15 条精准 &gt; 50 条模糊</li>
            <li><strong>增量扫描项目</strong> &mdash; 哪些变了、哪些需更新，一目了然</li>
            <li><strong>Dashboard 看全局</strong> &mdash; Bug、工作量、日志，不用逐个问</li>
            <li><strong>规则 = 团队标准</strong> &mdash; 新人第一天就拥有全部经验</li>
          </ul>
        </div>
        <div class="role-card">
          <div class="role-icon">&#x1F331;</div>
          <div class="role-title">新人入职</div>
          <div class="role-desc">刚加入项目，需要快速上手</div>
          <ul>
            <li><strong>规则 = 前辈经验</strong> &mdash; AI 自动遵守所有历史教训</li>
            <li><strong>不用读完所有代码</strong> &mdash; AI 先探索，再设计方案</li>
            <li><strong>你也会反哺团队</strong> &mdash; 你的审查产生新规则</li>
            <li><strong>历史都在</strong> &mdash; 需求、决策、日志随时可查</li>
          </ul>
        </div>
      </div>

      <h2>真实场景</h2>
      <div class="scenario-grid">
        <div class="scenario-box">
          <div class="scenario-label">新功能开发</div>
          <p>把想法变成需求，设计技术方案，逐步实现，验证通过后审查并提交。AI 在每一步都遵循项目规则，审查时自动提炼新规则。</p>
          <div class="key-principle"><strong>关键原则：</strong>先想清楚再动手。5 分钟的质疑可能省 5 小时的返工。</div>
        </div>
        <div class="scenario-box">
          <div class="scenario-label">诡异 Bug 修复</div>
          <p>遇到难题先让 AI 挑战你的假设，列出多种可能原因。修完后一定提炼教训 &mdash; 2 小时的定位换一条永久生效的规则。</p>
          <div class="key-principle"><strong>关键原则：</strong>每个 bug 都是学习机会。不提炼 = 白修。</div>
        </div>
        <div class="scenario-box">
          <div class="scenario-label">前后端同步开发</div>
          <p>后端写接口合约到共享目录，前端 AI 自动读取。各自标注工作范围，同名文件自动重命名，不会互相覆盖。</p>
          <div class="key-principle"><strong>关键原则：</strong>合约先行、范围隔离、通过 git 同步。</div>
        </div>
        <div class="scenario-box">
          <div class="scenario-label">自动化流水线</div>
          <p>需求和计划就绪后，AI 全自动执行实现、验证、审查、修复循环。失败自动修复（最多 3 轮），提交前必须等你确认。</p>
          <div class="key-principle"><strong>关键原则：</strong>自动化是为了加速，不是失控。人拥有最终决策权。</div>
        </div>
        <div class="scenario-box">
          <div class="scenario-label">实时监控 AI 工作</div>
          <p>AI 跑大任务时，通过 Mission Control 大屏实时观察进度：当前工具、子任务状态、事件流。看到异常及时干预。</p>
          <div class="key-principle"><strong>关键原则：</strong>信任但验证。让 AI 干活，保持可见性。</div>
        </div>
        <div class="scenario-box">
          <div class="scenario-label">项目体检</div>
          <p>项目演进后增量扫描，保护已有规则和自定义文件，只补充新发现，输出变更报告告诉你哪些变了。</p>
          <div class="key-principle"><strong>关键原则：</strong>定期体检，增量更新优于推倒重来。</div>
        </div>
      </div>

      <h2>规则写作指南</h2>
      <p>规则是飞轮的燃料。一条好规则需要满足四个标准：</p>
      <ul>
        <li><strong>可操作</strong> &mdash; 明确告诉你该做什么或不该做什么，而不是"注意一下"</li>
        <li><strong>项目相关</strong> &mdash; 引用你项目的具体文件、函数或约定</li>
        <li><strong>有证据</strong> &mdash; 来自真实事故或审查发现，而不是假设性担忧</li>
        <li><strong>持久有效</strong> &mdash; 3 个月后依然适用，不是临时方案</li>
      </ul>

      <div class="tip-box">
        <div class="tip-label">好规则 vs 坏规则</div>
        <p><strong>好：</strong>"访问 steps 数组前必须检查长度，因为 plan 初次创建时 steps 为空，第 47 行曾因此崩溃。"<br>
        <strong>坏：</strong>"小心使用数组" &mdash; 太模糊，无法执行。<br><br>
        <strong>好：</strong>"数值默认值用 ?? 而非 ||，因为 || 会把 0 当作 falsy，审查中发现 3 处此问题。"<br>
        <strong>坏：</strong>"使用有意义的变量名" &mdash; 这是通用建议，不是项目规则。</p>
      </div>

      <div class="warn-box">
        <div class="warn-label">规则卫生</div>
        <p>质量胜于数量。15 条精准规则好过 50 条模糊规则。超过 25 条时应合并相关规则。太久没被引用的规则可能已经过时，及时清理。</p>
      </div>

      <h2>团队协作模式</h2>
      <div class="collab-grid">
        <div class="collab-card">
          <div class="collab-title">设计师 &rarr; 开发者</div>
          <p>需求文档和原型放入共享目录，AI 自动理解设计意图。<strong>文件就是沟通，不需要开会对齐。</strong></p>
        </div>
        <div class="collab-card">
          <div class="collab-title">后端 &rarr; 前端</div>
          <p>接口合约共享，AI 按合约生成代码并自动检查一致性。<strong>接口不一致在编码阶段就被发现。</strong></p>
        </div>
        <div class="collab-card">
          <div class="collab-title">上下文传递</div>
          <p>保存对话中的重要决策，下次 AI 自动加载所有历史。<strong>不再需要每次从头解释背景。</strong></p>
        </div>
      </div>

      <div class="tip-box">
        <div class="tip-label">团队最佳实践</div>
        <p>把项目智能目录提交到 git（排除监控日志），团队成员 pull 后 AI 立即获得所有规则和文档。<strong>知识属于团队，不属于个人。</strong></p>
      </div>

    </div>
  </div>
  <!-- Logs Page -->
  <div id="pageLogs" style="display:none;flex:1;overflow:hidden;">
    <div style="display:flex;flex-direction:column;height:100%;padding:24px;overflow-y:auto;">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;">
        <h2 style="font-size:18px;font-weight:600;color:#e6edf3;">日志中心</h2>
        <div style="display:flex;gap:8px;align-items:center;">
          <select id="logProjectSelect" onchange="loadLogs()" style="background:#161b22;border:1px solid #30363d;color:#e6edf3;padding:6px 12px;border-radius:6px;font-size:13px;">
            <option value="">选择项目</option>
          </select>
          <div class="log-tab-bar">
            <button class="log-tab active" id="logTabAll" onclick="switchLogTab('all')">全部</button>
            <button class="log-tab" id="logTabChangelog" onclick="switchLogTab('changelog')">Changelog</button>
            <button class="log-tab" id="logTabSessions" onclick="switchLogTab('sessions')">Sessions</button>
            <button class="log-tab" id="logTabEvents" onclick="switchLogTab('events')">Events</button>
          </div>
        </div>
      </div>
      <div id="logContent" style="flex:1;">
        <div style="color:#484f58;font-size:13px;text-align:center;padding:40px;">选择一个项目查看日志</div>
      </div>
    </div>
  </div>
  <!-- Help Center Page -->
  <div id="pageHelp" style="display:none;flex:1;overflow-y:auto;">
    <div class="guide-page help-page">
      <h1>帮助中心</h1>
      <p class="subtitle">AionCode 使用说明与版本更新记录。</p>

      <div class="help-tab-bar" style="display:flex;gap:8px;margin-bottom:24px;">
        <button class="log-tab active" id="helpTabUsage" onclick="switchHelpTab('usage')">使用说明</button>
        <button class="log-tab" id="helpTabChangelog" onclick="switchHelpTab('changelog')">更新日志</button>
      </div>

      <!-- 使用说明 -->
      <div id="helpUsage">
        <h2>安装</h2>
        <pre><code># 克隆 AionCode
git clone https://github.com/user/aioncode.git

# 安装到你的项目
bash aioncode/install.sh /path/to/your/project

# 检查安装
bash aioncode/install.sh --check /path/to/your/project

# 升级到最新版
bash aioncode/install.sh --upgrade /path/to/your/project

# 卸载（需输入 "aioncode" 确认，.aion/ 目录保留）
bash aioncode/uninstall.sh /path/to/your/project</code></pre>

        <h2>安装产物</h2>
        <ul>
          <li><code>.claude/commands/</code> &mdash; 18 个 slash 命令文件</li>
          <li><code>.aion/</code> &mdash; 项目智能目录（规则、规格、计划、评审等，应提交到 git）</li>
          <li><code>.aion/refs/write-protocol.md</code> &mdash; 写入保护协议（控制文件覆盖行为）</li>
          <li><code>CLAUDE.md</code> &mdash; 规则自动加载（Claude 每次会话自动读取）</li>
          <li><code>.claude/hooks.json</code> &mdash; 监控 Hook（自动收集事件到 events.jsonl）</li>
        </ul>

        <h2>核心工作流</h2>
        <p>完整流程 8 步，按需取用。核心链路是 <strong>实现 &rarr; 验证 &rarr; 审查</strong>。</p>
        <pre><code># 新项目
think &rarr; design &rarr; (demo) &rarr; plan &rarr; impl &rarr; (test) &rarr; verify &rarr; review &rarr; learn &rarr; commit

# 已有项目
scan &rarr; design/impl &rarr; verify &rarr; review &rarr; commit

# Bug 修复
bug report &rarr; impl {BUG-ID} &rarr; verify &rarr; review &rarr; commit

# 自动化流水线
aion-loop &rarr; 自动执行 impl &rarr; verify &rarr; review &rarr; fix loop &rarr; commit</code></pre>

        <h2>命令速查表</h2>
        <table class="cmd-table">
          <thead><tr><th>命令</th><th>用途</th><th>产出</th></tr></thead>
          <tbody>
            <tr><td><code>aion-scan</code></td><td>扫描项目，生成规则和文档</td><td><code>.aion/refs/</code> + <code>.aion/rules/</code></td></tr>
            <tr><td><code>aion-think</code></td><td>质疑假设，防过度设计</td><td>替代方案分析</td></tr>
            <tr><td><code>aion-design</code></td><td>需求分析与规格设计</td><td><code>.aion/specs/*.md</code></td></tr>
            <tr><td><code>aion-demo</code></td><td>交互式 HTML 原型</td><td><code>.aion/prototypes/*/index.html</code></td></tr>
            <tr><td><code>aion-plan</code></td><td>基于代码的技术规划</td><td><code>.aion/plans/*.md</code></td></tr>
            <tr><td><code>aion-impl</code></td><td>分步代码实现</td><td>源代码 + 计划进度</td></tr>
            <tr><td><code>aion-test</code></td><td>测试生成 + 覆盖率 + 性能</td><td>测试文件 + <code>.aion/tests/</code></td></tr>
            <tr><td><code>aion-verify</code></td><td>build / lint / test 验证</td><td>验证报告 + 错误定位</td></tr>
            <tr><td><code>aion-review</code></td><td>代码审查 + 自动学习</td><td><code>.aion/reviews/*.md</code> + 规则</td></tr>
            <tr><td><code>aion-learn</code></td><td>深度规则提取</td><td><code>.aion/rules/*.md</code></td></tr>
            <tr><td><code>aion-bug</code></td><td>Bug 管理（报告/分配/关闭）</td><td><code>.aion/bugs/*.md</code></td></tr>
            <tr><td><code>aion-crosscheck</code></td><td>交叉模型验证</td><td>Bug 报告</td></tr>
            <tr><td><code>aion-loop</code></td><td>自动化流水线</td><td>全流程自动执行</td></tr>
            <tr><td><code>aion-save</code></td><td>保存对话上下文</td><td>多个 <code>.aion/</code> 文件</td></tr>
            <tr><td><code>aion-commit</code></td><td>安全 git 提交</td><td>Git commit + changelog</td></tr>
            <tr><td><code>aion-status</code></td><td>项目智能概览</td><td>终端输出</td></tr>
            <tr><td><code>aion-upgrade</code></td><td>版本检查与升级</td><td>升级报告</td></tr>
            <tr><td><code>aion-help</code></td><td>命令帮助与引导</td><td>终端输出</td></tr>
          </tbody>
        </table>

        <h2>写入保护协议</h2>
        <p>AionCode 通过 Write Protocol 防止文件覆盖和数据丢失。所有写入操作按文件类别自动适用不同策略：</p>
        <table class="cmd-table">
          <thead><tr><th>类别</th><th>文件</th><th>策略</th></tr></thead>
          <tbody>
            <tr><td><strong>Accumulative</strong></td><td>rules/*.md, changelog.md</td><td>只追加，写前去重，禁止覆盖</td></tr>
            <tr><td><strong>Versioned</strong></td><td>specs/*.md, plans/*.md</td><td>同名检查 &rarr; 归档/覆盖/换名三选一，scope 冲突检测</td></tr>
            <tr><td><strong>Regenerable</strong></td><td>refs/*, checklists/*, tests/*</td><td>Fingerprint 校验 &rarr; 未修改静默更新，已修改需确认</td></tr>
            <tr><td><strong>Unique-by-ID</strong></td><td>bugs/*.md, reviews/*.md</td><td>ID 唯一，无需保护</td></tr>
          </tbody>
        </table>

        <h2>Dashboard</h2>
        <ul>
          <li><strong>项目管理</strong> &mdash; 添加/初始化项目，查看统计和文件</li>
          <li><strong>Bug 看板</strong> &mdash; 按状态/分类/严重度筛选 Bug</li>
          <li><strong>团队管理</strong> &mdash; 配置团队成员、AI 模型、风险关键词</li>
          <li><strong>命令管理</strong> &mdash; 浏览和查看命令源码</li>
          <li><strong>日志中心</strong> &mdash; Changelog / Sessions / Events 三源聚合</li>
          <li><strong>最佳实践</strong> &mdash; 角色和场景导向的使用指南</li>
          <li><strong>Mission Control</strong> &mdash; 实时监控 Agent 工作状态（太空指挥中心风格）</li>
        </ul>

        <h2>常见问题</h2>
        <ul>
          <li><strong>跳过验证直接审查</strong> &mdash; verify 是客观检查（编译/测试），review 是主观评审。先 verify 再 review。</li>
          <li><strong>跳过审查</strong> &mdash; 审查是飞轮关键环节。没有审查，规则就不会积累。</li>
          <li><strong>不保存上下文</strong> &mdash; 有重要决策时执行 <code>aion-save</code>，否则下次对话丢失背景。</li>
          <li><strong>在 main 分支跑 loop</strong> &mdash; aion-loop 应在功能分支上执行。</li>
          <li><strong>参考文档堆积</strong> &mdash; 保持 <code>.aion/refs/</code> 精简，过期文档增加上下文噪音。</li>
        </ul>
      </div>

      <!-- 更新日志 -->
      <div id="helpChangelog" style="display:none;">
        <h2>更新日志</h2>

        <div class="scenario-box">
          <div class="scenario-label">v0.2 (2026-03-21)</div>
          <p><strong>Bug 追踪 + 交叉验证 + 写入保护</strong></p>
          <ul>
            <li><strong>新增命令</strong>：aion-bug（Bug 管理）、aion-crosscheck（交叉验证）、aion-upgrade（版本升级）</li>
            <li><strong>Write Protocol</strong>：统一写入保护协议，四类文件分级保护（Accumulative / Versioned / Regenerable / Unique-by-ID）</li>
            <li><strong>Fingerprint 机制</strong>：Regenerable 文件自动追加 MD5 指纹，重生成前校验，用户修改过的文件不被覆盖</li>
            <li><strong>Scope 冲突检测</strong>：Versioned 文件 frontmatter 声明 scope（api/web/mobile/infra/full），不同 scope 同名文件强制换名</li>
            <li><strong>Stale File Warning</strong>：修改他人 2 天前的文件时警告，建议先 git pull</li>
            <li><strong>Scan 双模式</strong>：首次扫描（FIRST_SCAN）生成全部产物；重新扫描（RE_SCAN）保护已有规则和用户自定义 checklist，输出 Delta Report</li>
            <li><strong>Learn 边界强化</strong>：Evidence Gate 门控，证据源全空时返回 BLOCKED，不越界做全量扫描</li>
            <li><strong>Design 版本检查</strong>：新增 Step 3.5，复用 Plan 的归档模式</li>
            <li><strong>卸载安全</strong>：uninstall.sh 重写，动态扫描命令、CLAUDE.md 只删标记区域、hooks/settings 备份、防误卸载确认</li>
            <li><strong>Dashboard</strong>：新增日志中心（Changelog/Sessions/Events 三源聚合）、帮助中心</li>
            <li><strong>aion-save</strong>：三层持久化（.aion/ + CLAUDE.md + Claude memory）</li>
            <li>命令总数：15 &rarr; 18</li>
          </ul>
        </div>

        <div class="scenario-box">
          <div class="scenario-label">v0.1 (2026-03-20)</div>
          <p><strong>初始版本</strong></p>
          <ul>
            <li>核心命令：design, plan, impl, verify, review, learn, save, commit, status, think, demo, test, loop, scan, help</li>
            <li>学习飞轮：review &rarr; 提取规则 &rarr; 下次加载</li>
            <li>Dashboard：项目管理、命令管理、Mission Control 实时监控</li>
            <li>install.sh：CLAUDE.md marker 合并策略</li>
            <li>零外部依赖设计</li>
          </ul>
        </div>
      </div>

    </div>
  </div>
  <!-- Bug Board Page -->
  <div id="pageBugs" style="display:none;flex:1;overflow:hidden;">
    <div style="display:flex;flex-direction:column;height:100%;padding:24px;overflow-y:auto;">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;">
        <h2 style="font-size:18px;font-weight:600;color:#e6edf3;">Bug 看板</h2>
        <div style="display:flex;gap:8px;align-items:center;">
          <select id="bugProjectSelect" onchange="loadBugs()" style="background:#161b22;border:1px solid #30363d;color:#e6edf3;padding:6px 12px;border-radius:6px;font-size:13px;">
            <option value="">选择项目</option>
          </select>
          <select id="bugFilterStatus" onchange="loadBugs()" style="background:#161b22;border:1px solid #30363d;color:#e6edf3;padding:6px 12px;border-radius:6px;font-size:13px;">
            <option value="">全部状态</option>
            <option value="open">Open</option>
            <option value="assigned">Assigned</option>
            <option value="in-progress">In Progress</option>
            <option value="fixed">Fixed</option>
            <option value="closed">Closed</option>
          </select>
          <select id="bugFilterCategory" onchange="loadBugs()" style="background:#161b22;border:1px solid #30363d;color:#e6edf3;padding:6px 12px;border-radius:6px;font-size:13px;">
            <option value="">全部分类</option>
            <option value="F">Frontend</option>
            <option value="B">Backend</option>
            <option value="X">Mixed</option>
          </select>
        </div>
      </div>
      <!-- Bug Stats Summary -->
      <div id="bugStatsBar" style="display:flex;gap:12px;margin-bottom:20px;flex-wrap:wrap;"></div>
      <!-- Bug List -->
      <div id="bugList" style="flex:1;">
        <div style="color:#484f58;font-size:13px;text-align:center;padding:40px;">选择一个项目查看 Bug</div>
      </div>
    </div>
  </div>
  <!-- Admin Page -->
  <div id="pageAdmin" style="display:none;flex:1;overflow:hidden;">
    <div style="display:flex;flex-direction:column;height:100%;padding:24px;overflow-y:auto;">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;">
        <h2 style="font-size:18px;font-weight:600;color:#e6edf3;">团队管理</h2>
        <div style="display:flex;gap:8px;align-items:center;">
          <select id="adminProjectSelect" onchange="loadTeamConfig()" style="background:#161b22;border:1px solid #30363d;color:#e6edf3;padding:6px 12px;border-radius:6px;font-size:13px;">
            <option value="">选择项目</option>
          </select>
        </div>
      </div>
      <!-- Team Members -->
      <div style="margin-bottom:32px;">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
          <h3 style="font-size:15px;font-weight:600;color:#e6edf3;">团队成员</h3>
          <button onclick="addTeamMember()" style="background:#238636;border:none;color:#fff;padding:6px 14px;border-radius:6px;cursor:pointer;font-size:13px;">+ 添加成员</button>
        </div>
        <div id="teamMemberList" style="display:grid;gap:12px;">
          <div style="color:#484f58;font-size:13px;text-align:center;padding:20px;">选择一个项目查看团队配置</div>
        </div>
      </div>
      <!-- AI Models -->
      <div style="margin-bottom:32px;">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
          <h3 style="font-size:15px;font-weight:600;color:#e6edf3;">AI 模型配置</h3>
          <button onclick="addModel()" style="background:#238636;border:none;color:#fff;padding:6px 14px;border-radius:6px;cursor:pointer;font-size:13px;">+ 添加模型</button>
        </div>
        <div id="modelList" style="display:grid;gap:12px;">
          <div style="color:#484f58;font-size:13px;text-align:center;padding:20px;">选择一个项目查看模型配置</div>
        </div>
      </div>
    </div>
  </div>
</div>
<div class="toast-container" id="toasts"></div>

<script>
// ===== State =====
let state = {
  projects: [],
  selected: null,      // project object
  stats: null,
  tree: [],
  openFile: null,      // { path, content }
  editMode: false,
  editContent: '',
  commands: [],        // command list
  commandsLoaded: false,
  selectedCmd: null,   // selected command filename
};

// ===== API Helpers =====
function encodeProjectPath(path) {
  // btoa with UTF-8 support
  const bytes = new TextEncoder().encode(path);
  let binary = '';
  for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i]);
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

async function api(method, url, body) {
  const opts = { method, headers: {} };
  if (body !== undefined) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(body);
  }
  const res = await fetch(url, opts);
  return res.json();
}

// ===== Toast =====
function toast(msg, type = 'info') {
  const el = document.createElement('div');
  el.className = 'toast ' + type;
  el.textContent = msg;
  document.getElementById('toasts').appendChild(el);
  setTimeout(() => el.remove(), 3500);
}

// ===== Markdown Renderer =====
function renderMarkdown(text) {
  if (!text) return '';
  let html = text;

  // Escape HTML first (but preserve our generated tags later)
  html = html.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

  // Code blocks (fenced)
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, function(_, lang, code) {
    return '<pre><code>' + code.trimEnd() + '</code></pre>';
  });

  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

  // Headings (must be after code blocks to avoid matching inside them)
  html = html.replace(/^#### (.+)$/gm, '<h4>$1</h4>');
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');

  // Horizontal rules
  html = html.replace(/^---+$/gm, '<hr>');

  // Bold and italic
  html = html.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

  // Links
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');

  // Blockquotes
  html = html.replace(/^&gt; (.+)$/gm, '<blockquote>$1</blockquote>');

  // Unordered lists: convert consecutive "- " lines into <ul>
  html = html.replace(/(^- .+$(\n- .+$)*)/gm, function(block) {
    const items = block.split('\n').map(l => '<li>' + l.replace(/^- /, '') + '</li>').join('');
    return '<ul>' + items + '</ul>';
  });

  // Ordered lists: convert consecutive "N. " lines into <ol>
  html = html.replace(/(^\d+\. .+$(\n\d+\. .+$)*)/gm, function(block) {
    const items = block.split('\n').map(l => '<li>' + l.replace(/^\d+\. /, '') + '</li>').join('');
    return '<ol>' + items + '</ol>';
  });

  // Tables: convert | col | col | rows into <table>
  html = html.replace(/(^\|.+\|$\n?)+/gm, function(block) {
    const rows = block.trim().split('\n').filter(r => r.trim());
    if (rows.length < 2) return block;
    // Check if row 2 is a separator (|---|---|)
    const isSep = /^\|[\s\-:]+\|/.test(rows[1]);
    let thead = '', tbody = '';
    const parseRow = (row, tag) => {
      const cells = row.split('|').filter((_, i, a) => i > 0 && i < a.length - 1);
      return '<tr>' + cells.map(c => '<' + tag + '>' + c.trim() + '</' + tag + '>').join('') + '</tr>';
    };
    if (isSep) {
      thead = '<thead>' + parseRow(rows[0], 'th') + '</thead>';
      tbody = '<tbody>' + rows.slice(2).map(r => parseRow(r, 'td')).join('') + '</tbody>';
    } else {
      tbody = '<tbody>' + rows.map(r => parseRow(r, 'td')).join('') + '</tbody>';
    }
    return '<table>' + thead + tbody + '</table>';
  });

  // Paragraphs: wrap remaining bare lines (skip lines that start with <)
  html = html.replace(/^([^<\n].+)$/gm, function(_, line) {
    // Don't wrap if it's inside a block element
    if (/^<\/?(?:h[1-4]|ul|ol|li|pre|code|blockquote|hr|div|p|table|thead|tbody|tr|th|td)/.test(line.trim())) return line;
    return '<p>' + line + '</p>';
  });

  // Clean up extra newlines between block elements
  html = html.replace(/\n{2,}/g, '\n');

  // Remove HTML comments
  html = html.replace(/&lt;!--[\s\S]*?--&gt;/g, '');

  return html;
}

// ===== Project List =====
async function loadProjects() {
  const data = await api('GET', '/api/projects');
  state.projects = data.projects || [];
  renderProjectList();
}

function renderProjectList() {
  const el = document.getElementById('projectList');
  if (!state.projects.length) {
    el.innerHTML = '<div style="padding:16px;color:#484f58;font-size:13px;line-height:1.6;">暂无项目<br>点击 <b>+</b> 添加项目</div>';
    return;
  }
  el.innerHTML = state.projects.map(p => {
    const active = state.selected && state.selected.path === p.path ? ' active' : '';
    const dotClass = p.has_aion ? 'green' : 'gray';
    return `<div class="project-item${active}" onclick="selectProject('${escapeAttr(p.path)}')">
      <span class="dot ${dotClass}"></span>
      <span class="name" title="${escapeAttr(p.path)}">${esc(p.name)}</span>
      <span class="btn-remove" onclick="event.stopPropagation();confirmRemoveProject('${escapeAttr(p.path)}','${escapeAttr(p.name)}')" title="从列表移除">&times;</span>
    </div>`;
  }).join('');
}

function escapeAttr(s) { return s.replace(/'/g, "\\'").replace(/"/g, '&quot;'); }
function esc(s) { return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

// ===== Project Selection =====
async function selectProject(path) {
  const proj = state.projects.find(p => p.path === path);
  if (!proj) return;
  stopActivityFeed();
  state.selected = proj;
  state.openFile = null;
  state.editMode = false;
  renderProjectList();

  if (proj.has_aion) {
    await loadProjectData();
  } else {
    renderInitPanel();
  }
}

async function loadProjectData() {
  const enc = encodeProjectPath(state.selected.path);
  const [statsData, treeData, sessionsData] = await Promise.all([
    api('GET', `/api/projects/${enc}/stats`),
    api('GET', `/api/projects/${enc}/files`),
    api('GET', `/api/projects/${enc}/sessions`),
  ]);
  state.stats = statsData;
  state.tree = treeData.tree || [];
  state.sessions = sessionsData.sessions || [];
  renderProjectView();
  startActivityFeed();
}

// ===== Init Panel =====
function renderInitPanel() {
  const main = document.getElementById('mainContent');
  main.innerHTML = `<div class="init-panel">
    <div class="title">安装 AionCode</div>
    <div class="desc">该项目有 .git/ 仓库但尚未初始化 .aion/ 目录。
    安装 AionCode 将添加工作流脚手架、命令文件和 CLAUDE.md 集成。</div>
    <button class="btn-install" id="btnInstall" onclick="doInstall()">安装 AionCode</button>
    <div class="init-log" id="initLog"></div>
  </div>`;
}

async function doInstall() {
  const btn = document.getElementById('btnInstall');
  const log = document.getElementById('initLog');
  btn.disabled = true;
  btn.textContent = '安装中...';
  log.classList.add('visible');
  log.textContent = '正在安装...\n';

  try {
    const data = await api('POST', '/api/projects/init', { path: state.selected.path });
    if (data.ok) {
      log.textContent += (data.log || []).join('\n') + '\n\n安装完成！';
      toast('AionCode 安装成功', 'success');
      // Refresh
      await loadProjects();
      state.selected = state.projects.find(p => p.path === state.selected.path) || state.selected;
      state.selected.has_aion = true;
      await loadProjectData();
    } else {
      log.textContent += '错误: ' + (data.error || '未知错误');
      toast('安装失败: ' + (data.error || '未知'), 'error');
      btn.disabled = false;
      btn.textContent = '重试安装';
    }
  } catch (e) {
    log.textContent += '错误: ' + e.message;
    toast('安装失败', 'error');
    btn.disabled = false;
    btn.textContent = '重试安装';
  }
}

// ===== Project View (Stats + Browser) =====
function renderProjectView() {
  const main = document.getElementById('mainContent');
  const s = state.stats || {};

  main.innerHTML = `
    <div class="stats-row">
      <div class="stat-card accent">
        <div class="label">规则</div>
        <div class="value">${s.rules_total || 0}</div>
        <div class="sub">陷阱 ${s.rules_pitfalls||0} / 风格 ${s.rules_style||0} / 性能 ${s.rules_perf||0}</div>
      </div>
      <div class="stat-card">
        <div class="label">需求规格</div>
        <div class="value">${s.specs_count || 0}</div>
      </div>
      <div class="stat-card">
        <div class="label">实施计划</div>
        <div class="value">${s.plans_count || 0}</div>
      </div>
      <div class="stat-card">
        <div class="label">审查报告</div>
        <div class="value">${s.reviews_count || 0}</div>
      </div>
      <div class="stat-card">
        <div class="label">最近活动</div>
        <div class="value" style="font-size:16px;">${s.last_activity || '无'}</div>
      </div>
      <div class="stat-card" style="cursor:pointer" onclick="openMonitor()">
        <div class="label">实时监控</div>
        <div class="value" style="font-size:16px;">Mission Control</div>
        <div class="sub">点击打开大屏</div>
      </div>
    </div>
    <div class="sessions-row">
      <div class="sessions-header">最近会话</div>
      <div class="sessions-list">${renderSessions()}</div>
    </div>
    <div class="activity-row">
      <div class="activity-header">
        <span><span class="activity-live-dot offline" id="activityDot"></span>实时活动</span>
        <span class="activity-count" id="activityCount"></span>
      </div>
      <div class="activity-list" id="activityList">
        <div class="activity-empty">加载中...</div>
      </div>
    </div>
    <div class="browser-area">
      <div class="file-tree-panel">
        <div class="file-tree-header">
          <span>.aion/</span>
          <button class="btn-new" onclick="showNewFileModal()">+ 新建</button>
        </div>
        <div class="file-tree-scroll" id="fileTree"></div>
      </div>
      <div class="file-editor-panel" id="editorPanel">
        <div class="editor-empty">从左侧文件树选择文件</div>
      </div>
    </div>`;

  renderFileTree();
}

function renderFileTree() {
  const el = document.getElementById('fileTree');
  if (!el) return;
  el.innerHTML = renderTreeItems(state.tree, 0);
}

function renderTreeItems(items, depth) {
  return items.map(item => {
    const pad = 14 + depth * 16;
    if (item.type === 'dir') {
      const icon = '&#128193;';
      const childHtml = item.children ? renderTreeItems(item.children, depth + 1) : '';
      return `<div class="tree-item dir" style="padding-left:${pad}px" onclick="toggleDir(this)">
          <span class="icon">${icon}</span>
          <span class="fname">${esc(item.name)}/</span>
        </div>
        <div class="tree-children">${childHtml}</div>`;
    } else {
      const icon = '&#128196;';
      const active = state.openFile && state.openFile.path === item.path ? ' active' : '';
      return `<div class="tree-item${active}" style="padding-left:${pad}px"
          onclick="openFile('${escapeAttr(item.path)}')">
          <span class="icon">${icon}</span>
          <span class="fname">${esc(item.name)}</span>
        </div>`;
    }
  }).join('');
}

function toggleDir(el) {
  const children = el.nextElementSibling;
  if (children && children.classList.contains('tree-children')) {
    children.style.display = children.style.display === 'none' ? '' : 'none';
  }
}

// ===== File Operations =====
async function openFile(relPath) {
  const enc = encodeProjectPath(state.selected.path);
  try {
    const data = await api('GET', `/api/projects/${enc}/file?path=${encodeURIComponent(relPath)}`);
    if (data.ok) {
      state.openFile = { path: relPath, content: data.content || '' };
      state.editMode = false;
      renderEditor();
      renderFileTree();
    } else {
      toast('打开文件失败: ' + (data.error || '未知'), 'error');
    }
  } catch(e) {
    toast('打开文件失败: ' + e.message, 'error');
  }
}

function renderEditor() {
  const panel = document.getElementById('editorPanel');
  if (!panel || !state.openFile) return;

  const f = state.openFile;
  const isEditing = state.editMode;

  let toolbar = `<div class="editor-toolbar">
    <div class="file-name">${esc(f.path)}</div>`;

  if (isEditing) {
    toolbar += `<button class="primary" onclick="saveFile()">保存</button>
      <button onclick="cancelEdit()">取消</button>`;
  } else {
    toolbar += `<button onclick="startEdit()">编辑</button>
      <button class="danger" onclick="confirmDelete()">删除</button>`;
  }
  toolbar += '</div>';

  let content;
  if (isEditing) {
    content = `<textarea class="editor-textarea" id="editArea">${esc(state.editContent)}</textarea>`;
  } else {
    const ext = f.path.split('.').pop().toLowerCase();
    if (['md', 'markdown'].includes(ext)) {
      content = `<div class="editor-content"><div class="md-view">${renderMarkdown(f.content)}</div></div>`;
    } else {
      content = `<div class="editor-content"><pre style="white-space:pre-wrap;color:#e6edf3;font-family:'SF Mono','Fira Code',monospace;font-size:13px;line-height:1.6;">${esc(f.content)}</pre></div>`;
    }
  }

  panel.innerHTML = toolbar + content;

  if (isEditing) {
    const ta = document.getElementById('editArea');
    if (ta) {
      ta.addEventListener('keydown', function(e) {
        if (e.key === 'Tab') {
          e.preventDefault();
          const start = this.selectionStart;
          const end = this.selectionEnd;
          this.value = this.value.substring(0, start) + '  ' + this.value.substring(end);
          this.selectionStart = this.selectionEnd = start + 2;
        }
        if ((e.metaKey || e.ctrlKey) && e.key === 's') {
          e.preventDefault();
          saveFile();
        }
      });
    }
  }
}

function startEdit() {
  state.editMode = true;
  state.editContent = state.openFile.content;
  renderEditor();
}

function cancelEdit() {
  state.editMode = false;
  renderEditor();
}

async function saveFile() {
  const ta = document.getElementById('editArea');
  if (!ta) return;
  const content = ta.value;
  const enc = encodeProjectPath(state.selected.path);
  const data = await api('PUT', `/api/projects/${enc}/file`, {
    path: state.openFile.path,
    content: content,
  });
  if (data.ok) {
    state.openFile.content = content;
    state.editMode = false;
    toast('文件已保存', 'success');
    renderEditor();
    // Refresh stats in case rules changed
    const statsData = await api('GET', `/api/projects/${enc}/stats`);
    state.stats = statsData;
    renderStatsOnly();
  } else {
    toast('保存失败: ' + (data.error || '未知'), 'error');
  }
}

function renderSessions() {
  if (!state.sessions || state.sessions.length === 0) {
    return '<div class="session-empty">暂无会话记录</div>';
  }
  return state.sessions.slice(0, 5).map(s => {
    const date = new Date(s.ts);
    const isToday = new Date().toDateString() === date.toDateString();
    const timeStr = isToday
      ? date.toLocaleTimeString('zh-CN', {hour:'2-digit',minute:'2-digit'})
      : date.toLocaleDateString('zh-CN', {month:'short',day:'numeric'});
    const durMin = Math.floor((s.duration_sec||0) / 60);
    const durStr = durMin > 0 ? durMin + 'm' : '<1m';
    const topTools = Object.entries(s.tools||{})
      .sort((a,b) => b[1]-a[1]).slice(0,3)
      .map(([t,c]) => t+'\\u00d7'+c).join(' ');
    const dotCls = isToday ? 'dot-today' : 'dot-past';
    const lastFile = s.last_file ? s.last_file.split('/').pop() : '';
    return '<div class="session-item">' +
      '<span class="session-dot ' + dotCls + '"></span>' +
      '<span class="session-time">' + timeStr + '</span>' +
      '<span class="session-dur">' + durStr + '</span>' +
      '<span class="session-tools">' + topTools + '</span>' +
      '<span class="session-file">' + esc(lastFile) + '</span>' +
    '</div>';
  }).join('');
}

function openMonitor() {
  const enc = encodeProjectPath(state.selected.path);
  window.open('/monitor/' + enc, '_blank');
}

// ===== Live Activity Feed =====
let activityTimer = null;
let activityEvents = [];
let activityLastTotal = 0;

function startActivityFeed() {
  stopActivityFeed();
  if (!state.selected) return;
  pollActivity();
  activityTimer = setInterval(pollActivity, 3000);
}

async function pollActivity() {
  if (!state.selected) return;
  const enc = encodeProjectPath(state.selected.path);
  try {
    const data = await api('GET', `/api/projects/${enc}/events/recent?limit=20`);
    if (data && data.events) {
      const dot = document.getElementById('activityDot');
      if (dot) dot.classList.remove('offline');
      // Only update if new events arrived
      if (data.total !== activityLastTotal || activityEvents.length === 0) {
        activityEvents = data.events;
        activityLastTotal = data.total;
        const countEl = document.getElementById('activityCount');
        if (countEl) countEl.textContent = `${data.total} 条事件`;
        renderActivityList();
      }
    }
  } catch(e) {
    const dot = document.getElementById('activityDot');
    if (dot) dot.classList.add('offline');
  }
}

function stopActivityFeed() {
  if (activityTimer) {
    clearInterval(activityTimer);
    activityTimer = null;
  }
  activityEvents = [];
  activityLastTotal = 0;
}

function summarizeEvent(ev) {
  const data = ev.data || {};
  const hook = data.hook_event_name || data.event || '';
  const ts = ev.ts || '';
  const tool = data.tool_name || '';
  let desc = '', icon = '';
  if (hook === 'PreToolUse') {
    const inp = data.tool_input || {};
    const fp = inp.file_path || inp.path || inp.command || '';
    desc = tool;
    if (fp) { const name = typeof fp === 'string' && fp.includes('/') ? fp.split('/').pop() : fp; desc += ' \\u2192 ' + name; }
    icon = 'tool';
  } else if (hook === 'PostToolUse') { desc = tool + ' completed'; icon = 'done';
  } else if (hook === 'SubagentStart') { desc = 'Subagent: ' + (data.agent_type || data.subagent_type || data.description || ''); icon = 'agent';
  } else if (hook === 'SubagentStop') { desc = 'Subagent returned'; icon = 'agent_done';
  } else if (hook === 'Stop') { desc = 'Session cycle complete'; icon = 'stop';
  } else if (hook === 'SessionStart') { desc = 'Session started'; icon = 'start';
  } else if (hook === 'SessionEnd') { desc = 'Session ended'; icon = 'end';
  } else { desc = hook || 'unknown'; icon = 'info'; }
  return { ts, type: hook, desc, icon, tool };
}

function renderActivityList() {
  const el = document.getElementById('activityList');
  if (!el) return;
  if (activityEvents.length === 0) {
    el.innerHTML = '<div class="activity-empty">\\u6682\\u65E0\\u4E8B\\u4EF6\\u8BB0\\u5F55</div>';
    return;
  }
  const iconMap = { tool: '\\u2699', done: '\\u2705', agent: '\\uD83E\\uDD16', agent_done: '\\u2194', stop: '\\u23F9', start: '\\u25B6', end: '\\u23F9', info: '\\u2139' };
  el.innerHTML = activityEvents.slice(0, 20).map(ev => {
    const timeStr = ev.ts ? formatEventTime(ev.ts) : '';
    const ic = iconMap[ev.icon] || '\\u2022';
    const descHtml = ev.desc.replace(/(Read|Write|Edit|Glob|Grep|Bash|Agent)/g, '<span class="tool-name">$1</span>');
    return '<div class="activity-item">' +
      '<span class="activity-icon">' + ic + '</span>' +
      '<span class="activity-time">' + timeStr + '</span>' +
      '<span class="activity-desc">' + descHtml + '</span>' +
    '</div>';
  }).join('');
}

function formatEventTime(ts) {
  try {
    const d = new Date(ts);
    const now = new Date();
    const diffSec = Math.floor((now - d) / 1000);
    if (diffSec < 60) return diffSec + 's ago';
    if (diffSec < 3600) return Math.floor(diffSec / 60) + 'm ago';
    return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
  } catch(e) { return ''; }
}

function renderStatsOnly() {
  const row = document.querySelector('.stats-row');
  if (!row || !state.stats) return;
  const s = state.stats;
  row.innerHTML = `
    <div class="stat-card accent">
      <div class="label">规则</div>
      <div class="value">${s.rules_total || 0}</div>
      <div class="sub">陷阱 ${s.rules_pitfalls||0} / 风格 ${s.rules_style||0} / 性能 ${s.rules_perf||0}</div>
    </div>
    <div class="stat-card">
      <div class="label">需求规格</div>
      <div class="value">${s.specs_count || 0}</div>
    </div>
    <div class="stat-card">
      <div class="label">实施计划</div>
      <div class="value">${s.plans_count || 0}</div>
    </div>
    <div class="stat-card">
      <div class="label">审查报告</div>
      <div class="value">${s.reviews_count || 0}</div>
    </div>
    <div class="stat-card">
      <div class="label">最近活动</div>
      <div class="value" style="font-size:16px;">${s.last_activity || '无'}</div>
    </div>
    <div class="stat-card">
      <div class="label">Bug</div>
      <div class="value">${s.bugs_count || 0}</div>
    </div>
    <div class="stat-card" style="cursor:pointer" onclick="openMonitor()">
      <div class="label">实时监控</div>
      <div class="value" style="font-size:16px;">Mission Control</div>
      <div class="sub">点击打开大屏</div>
    </div>
    ${s.upgrade_available ? `<div class="stat-card" style="cursor:pointer;border-color:#d29922;" onclick="upgradeProject()">
      <div class="label" style="color:#d29922;">有新版本</div>
      <div class="value" style="font-size:14px;color:#d29922;">v${esc(s.installed_version||'?')} → v${esc(s.source_version||'?')}</div>
      <div class="sub">点击升级</div>
    </div>` : `<div class="stat-card">
      <div class="label">版本</div>
      <div class="value" style="font-size:16px;">v${esc(s.installed_version||'?')}</div>
      <div class="sub" style="color:#3fb950;">已是最新</div>
    </div>`}`;
}

function confirmDelete() {
  if (!state.openFile) return;
  showModal(
    '删除文件',
    `确定要删除 <strong>${esc(state.openFile.path)}</strong> 吗？此操作不可撤销。`,
    [
      { label: '取消', cls: '', action: hideModal },
      { label: '删除', cls: 'danger', action: doDelete },
    ]
  );
}

async function doDelete() {
  hideModal();
  const enc = encodeProjectPath(state.selected.path);
  const data = await api('DELETE', `/api/projects/${enc}/file?path=${encodeURIComponent(state.openFile.path)}`);
  if (data.ok) {
    toast('文件已删除', 'success');
    state.openFile = null;
    state.editMode = false;
    // Refresh tree
    const treeData = await api('GET', `/api/projects/${enc}/files`);
    state.tree = treeData.tree || [];
    renderProjectView();
  } else {
    toast('删除失败: ' + (data.error || '未知'), 'error');
  }
}

// ===== Add / Remove Project =====
let _fpSelected = null; // selected path in folder picker

function showAddProjectModal() {
  const body = `<div class="folder-picker">
    <div class="fp-path-bar">
      <button onclick="fpUp()" title="上级目录">&#8593;</button>
      <span class="fp-path-text" id="fpCurrentPath">加载中...</span>
    </div>
    <div class="fp-list" id="fpList"><div class="fp-empty">加载中...</div></div>
  </div>`;

  showModal('添加项目', body, [
    { label: '取消', cls: '', action: hideModal },
    { label: '选择此文件夹', cls: 'primary', action: doAddProject },
  ]);

  _fpSelected = null;
  fpBrowse('');
}

async function fpBrowse(path) {
  const url = '/api/browse' + (path ? '?path=' + encodeURIComponent(path) : '');
  const data = await api('GET', url);
  if (data.error) { toast(data.error, 'error'); return; }

  _fpSelected = data.current;
  document.getElementById('fpCurrentPath').textContent = data.current;

  const list = document.getElementById('fpList');
  if (!data.dirs || data.dirs.length === 0) {
    list.innerHTML = '<div class="fp-empty">无子目录</div>';
    return;
  }
  list.innerHTML = data.dirs.map(d => {
    let badges = '';
    if (d.has_aion) badges += '<span class="fp-badge aion">.aion</span>';
    else if (d.has_git) badges += '<span class="fp-badge git">.git</span>';
    return `<div class="fp-item" ondblclick="fpBrowse('${escapeAttr(d.path)}')" onclick="fpSelect(this,'${escapeAttr(d.path)}')">
      <span class="fp-icon">&#128193;</span>
      <span class="fp-name">${esc(d.name)}</span>
      ${badges}
    </div>`;
  }).join('');
}

function fpSelect(el, path) {
  document.querySelectorAll('.fp-item.selected').forEach(e => e.classList.remove('selected'));
  el.classList.add('selected');
  _fpSelected = path;
  document.getElementById('fpCurrentPath').textContent = path;
}

function fpUp() {
  if (!_fpSelected) return;
  const parent = _fpSelected.substring(0, _fpSelected.lastIndexOf('/')) || '/';
  fpBrowse(parent);
}

async function doAddProject() {
  if (!_fpSelected) { toast('未选择文件夹', 'error'); return; }
  hideModal();
  const data = await api('POST', '/api/projects/add', { path: _fpSelected });
  if (data.ok) {
    toast('项目已添加: ' + data.name, 'success');
    await loadProjects();
    selectProject(data.path);
  } else {
    toast(data.error || '添加失败', 'error');
  }
}

function confirmRemoveProject(path, name) {
  showModal(
    '移除项目',
    `<p>从面板移除 <strong>${esc(name)}</strong>？</p><p style="color:#8b949e;font-size:12px;">仅从列表移除，不会删除任何文件。</p>`,
    [
      { label: '取消', cls: '', action: hideModal },
      { label: '移除', cls: 'danger', action: () => doRemoveProject(path) },
    ]
  );
}

async function doRemoveProject(path) {
  hideModal();
  const data = await api('POST', '/api/projects/remove', { path });
  if (data.ok) {
    toast('项目已移除', 'success');
    if (state.selected && state.selected.path === path) {
      state.selected = null;
      document.getElementById('mainContent').innerHTML = `<div class="content-empty">
        <div>选择一个项目开始</div>
        <div class="hint">点击 + 添加项目</div>
      </div>`;
    }
    await loadProjects();
  } else {
    toast(data.error || '移除失败', 'error');
  }
}

// ===== New File Modal =====
function showNewFileModal() {
  const dirs = ['rules', 'specs', 'plans', 'reviews', 'contracts', 'refs', 'prototypes'];
  const optionsHtml = dirs.map(d => `<option value="${d}">${d}/</option>`).join('');

  const body = `<p>在 .aion/ 中新建文件</p>
    <label style="font-size:12px;color:#8b949e;display:block;margin-bottom:4px;">目录</label>
    <select id="newFileDir">
      <option value="">（根目录）</option>
      ${optionsHtml}
    </select>
    <label style="font-size:12px;color:#8b949e;display:block;margin-bottom:4px;">文件名</label>
    <input type="text" id="newFileName" placeholder="例如 my-spec.md" autofocus>`;

  showModal('新建文件', body, [
    { label: '取消', cls: '', action: hideModal },
    { label: '创建', cls: 'primary', action: doCreateFile },
  ]);

  setTimeout(() => {
    const inp = document.getElementById('newFileName');
    if (inp) inp.focus();
  }, 100);
}

async function doCreateFile() {
  const dir = document.getElementById('newFileDir').value;
  const name = document.getElementById('newFileName').value.trim();
  if (!name) {
    toast('请输入文件名', 'error');
    return;
  }
  // Basic validation
  if (/[\/\\]/.test(name) || name.startsWith('.')) {
    toast('无效的文件名', 'error');
    return;
  }
  const relPath = dir ? `${dir}/${name}` : name;
  hideModal();

  const enc = encodeProjectPath(state.selected.path);
  const data = await api('POST', `/api/projects/${enc}/file`, { path: relPath, content: '' });
  if (data.ok) {
    toast('文件已创建', 'success');
    const treeData = await api('GET', `/api/projects/${enc}/files`);
    state.tree = treeData.tree || [];
    renderFileTree();
    await openFile(relPath);
    startEdit();
  } else {
    toast('创建失败: ' + (data.error || '未知'), 'error');
  }
}

// ===== Modal System =====
function showModal(title, bodyHtml, actions) {
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay';
  overlay.id = 'modalOverlay';
  overlay.onclick = function(e) { if (e.target === overlay) hideModal(); };

  const btns = actions.map(a =>
    `<button class="${a.cls}" data-action="${a.label}">${a.label}</button>`
  ).join('');

  overlay.innerHTML = `<div class="modal">
    <h3>${title}</h3>
    ${bodyHtml}
    <div class="modal-actions">${btns}</div>
  </div>`;

  document.body.appendChild(overlay);

  // Wire up buttons
  overlay.querySelectorAll('.modal-actions button').forEach(btn => {
    const act = actions.find(a => a.label === btn.dataset.action);
    if (act) btn.onclick = act.action;
  });
}

function hideModal() {
  const el = document.getElementById('modalOverlay');
  if (el) el.remove();
}

// ===== Page Switching =====
function switchPage(page) {
  const pages = { projects: 'pageProjects', commands: 'pageCommands', guide: 'pageGuide', bugs: 'pageBugs', admin: 'pageAdmin', logs: 'pageLogs', help: 'pageHelp' };
  const tabs = { projects: 'tabProjects', commands: 'tabCommands', guide: 'tabGuide', bugs: 'tabBugs', admin: 'tabAdmin', logs: 'tabLogs', help: 'tabHelp' };

  // Hide all pages, deactivate all tabs
  Object.values(pages).forEach(id => { document.getElementById(id).style.display = 'none'; });
  Object.values(tabs).forEach(id => { document.getElementById(id).classList.remove('active'); });

  // Show selected
  document.getElementById(pages[page]).style.display = page === 'projects' ? 'flex' : 'flex';
  document.getElementById(tabs[page]).classList.add('active');
  document.getElementById('btnRefresh').style.display = page === 'projects' ? '' : 'none';

  // Load commands on first visit
  if (page === 'commands' && !state.commandsLoaded) {
    loadCommands();
  }
  // Populate project selects on bug/admin/logs pages
  if (page === 'bugs' || page === 'admin' || page === 'logs') {
    populateProjectSelects();
  }
}

// ===== Commands Page =====
async function loadCommands() {
  const data = await api('GET', '/api/commands');
  state.commands = data.commands || [];
  state.commandsLoaded = true;
  state.selectedCmd = null;
  renderCmdList();
}

function renderCmdList() {
  const el = document.getElementById('cmdList');
  if (!state.commands.length) {
    el.innerHTML = '<div style="padding:16px;color:#484f58;font-size:13px;">未找到命令文件</div>';
    return;
  }
  el.innerHTML = state.commands.map(c => {
    const active = state.selectedCmd === c.filename ? ' active' : '';
    const label = c.name.replace('aion-', '');
    return `<div class="project-item cmd-item${active}" onclick="openCommand('${escapeAttr(c.filename)}')">
      <span class="dot green"></span>
      <span class="name">
        <div>${esc(label)}</div>
        <div class="cmd-subtitle">${esc(c.description || c.title)}</div>
      </span>
    </div>`;
  }).join('');
}

async function openCommand(filename) {
  state.selectedCmd = filename;
  renderCmdList();
  const data = await api('GET', '/api/commands/' + encodeURIComponent(filename));
  if (!data.ok) {
    toast('加载失败: ' + (data.error || '未知'), 'error');
    return;
  }
  const panel = document.getElementById('cmdContent');
  panel.innerHTML = `<div class="cmd-viewer">
    <div class="cmd-body">${renderMarkdown(data.content)}</div>
  </div>`;
}

// ===== Upgrade =====
async function upgradeProject() {
  if (!state.selected) { toast('请先选择项目', 'error'); return; }
  const s = state.stats;
  if (!s || !s.upgrade_available) { toast('已是最新版本', 'info'); return; }
  if (!confirm(`确定将 AionCode 从 v${s.installed_version} 升级到 v${s.source_version}？\n\n升级内容：\n- 更新所有命令文件\n- 刷新 CLAUDE.md\n- 创建新目录和模板\n\n你的规则、规格、计划等数据不会受影响。`)) return;
  const enc = encodeProjectPath(state.selected.path);
  try {
    const data = await api('POST', `/api/projects/${enc}/upgrade`);
    if (data.ok) {
      toast('升级成功！', 'success');
      selectProject(state.selected.path);  // reload stats
    } else {
      toast('升级失败: ' + (data.errors || '未知错误'), 'error');
    }
  } catch(e) {
    toast('升级失败: ' + String(e), 'error');
  }
}

// ===== Help Center =====
function switchHelpTab(tab) {
  document.getElementById('helpUsage').style.display = tab === 'usage' ? '' : 'none';
  document.getElementById('helpChangelog').style.display = tab === 'changelog' ? '' : 'none';
  document.getElementById('helpTabUsage').classList.toggle('active', tab === 'usage');
  document.getElementById('helpTabChangelog').classList.toggle('active', tab === 'changelog');
}

// ===== Log Center =====
let logState = { changelog: [], sessions: [], events: [], tab: 'all' };

async function loadLogs() {
  const projectPath = document.getElementById('logProjectSelect').value;
  if (!projectPath) {
    document.getElementById('logContent').innerHTML = '<div style="color:#484f58;font-size:13px;text-align:center;padding:40px;">选择一个项目查看日志</div>';
    return;
  }
  const enc = encodeProjectPath(projectPath);
  try {
    const [changelogData, sessionsData, eventsData] = await Promise.all([
      api('GET', `/api/projects/${enc}/changelog?limit=50`),
      api('GET', `/api/projects/${enc}/sessions?limit=50`),
      api('GET', `/api/projects/${enc}/events/recent?limit=100`),
    ]);
    logState.changelog = changelogData.entries || [];
    logState.sessions = sessionsData.sessions || [];
    logState.events = eventsData.events || [];
    renderLogs();
  } catch(e) {
    document.getElementById('logContent').innerHTML = '<div style="color:#f85149;padding:20px;">加载失败: ' + esc(String(e)) + '</div>';
  }
}

function switchLogTab(tab) {
  logState.tab = tab;
  document.querySelectorAll('.log-tab').forEach(el => el.classList.remove('active'));
  document.getElementById('logTab' + tab.charAt(0).toUpperCase() + tab.slice(1)).classList.add('active');
  renderLogs();
}

function renderLogs() {
  const el = document.getElementById('logContent');
  const tab = logState.tab;
  let html = '';

  if (tab === 'all' || tab === 'changelog') {
    html += renderChangelogSection();
  }
  if (tab === 'all' || tab === 'sessions') {
    html += renderSessionsSection();
  }
  if (tab === 'all' || tab === 'events') {
    html += renderEventsSection();
  }

  if (!html.trim()) {
    html = '<div style="color:#484f58;font-size:13px;text-align:center;padding:40px;">暂无日志数据</div>';
  }
  el.innerHTML = html;
}

function renderChangelogSection() {
  const entries = logState.changelog;
  let html = '<div class="log-section">';
  html += '<div class="log-section-title">Changelog <span class="badge">' + entries.length + '</span></div>';
  if (entries.length === 0) {
    html += '<div style="color:#484f58;font-size:12px;padding:8px 0;">暂无 changelog 记录</div>';
  } else {
    entries.forEach(e => {
      const typeMatch = (e.summary || '').match(/^(feat|fix|enhance|refactor|docs|test|chore):/i);
      const typeLabel = typeMatch ? typeMatch[1].toLowerCase() : 'update';
      const summaryText = typeMatch ? e.summary.slice(typeMatch[0].length).trim() : (e.summary || '');
      const bodyHtml = (e.body || '').split('\\n').slice(0, 6).map(l =>
        l.replace(/`([^`]+)`/g, '<code>$1</code>').replace(/^### /, '<strong>').replace(/^- /, '&bull; ')
      ).join('<br>');
      html += '<div class="log-entry">' +
        '<div class="log-entry-header">' +
          '<span class="log-entry-date">' + esc(e.date) + '</span>' +
          '<span class="log-entry-type log-type-changelog">' + esc(typeLabel) + '</span>' +
          '<span class="log-entry-summary">' + esc(summaryText) + '</span>' +
        '</div>';
      if (bodyHtml) {
        html += '<div class="log-entry-body">' + bodyHtml + '</div>';
      }
      html += '</div>';
    });
  }
  html += '</div>';
  return html;
}

function renderSessionsSection() {
  const entries = logState.sessions;
  let html = '<div class="log-section">';
  html += '<div class="log-section-title">Sessions <span class="badge">' + entries.length + '</span></div>';
  if (entries.length === 0) {
    html += '<div style="color:#484f58;font-size:12px;padding:8px 0;">暂无会话记录</div>';
  } else {
    entries.forEach(s => {
      const date = new Date(s.ts);
      const dateStr = date.toLocaleString('zh-CN', {month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'});
      const durMin = Math.floor((s.duration_sec||0) / 60);
      const durStr = durMin > 0 ? durMin + 'min' : '<1min';
      const tools = Object.entries(s.tools||{}).sort((a,b) => b[1]-a[1]).slice(0,5).map(([t,c]) => t + ' x' + c).join(', ');
      const files = (s.files_changed||[]).slice(0,3).map(f => f.split('/').pop()).join(', ');
      html += '<div class="log-entry">' +
        '<div class="log-entry-header">' +
          '<span class="log-entry-date">' + dateStr + '</span>' +
          '<span class="log-entry-type log-type-session">session</span>' +
          '<span class="log-entry-summary">' + durStr + '</span>' +
        '</div>' +
        '<div class="log-entry-meta">';
      if (tools) html += '<span>Tools: ' + esc(tools) + '</span>';
      if (files) html += '<span>Files: ' + esc(files) + '</span>';
      html += '</div></div>';
    });
  }
  html += '</div>';
  return html;
}

function renderEventsSection() {
  const entries = logState.events;
  let html = '<div class="log-section">';
  html += '<div class="log-section-title">Events <span class="badge">' + entries.length + '</span></div>';
  if (entries.length === 0) {
    html += '<div style="color:#484f58;font-size:12px;padding:8px 0;">暂无事件记录</div>';
  } else {
    entries.forEach(e => {
      const time = e.time || e.ts || '';
      const desc = e.description || e.hook || e.event || '';
      const icon = e.icon || '';
      html += '<div class="log-entry">' +
        '<div class="log-entry-header">' +
          '<span class="log-entry-date">' + esc(String(time).slice(0,16)) + '</span>' +
          '<span class="log-entry-type log-type-event">' + esc(icon || 'event') + '</span>' +
          '<span class="log-entry-summary">' + esc(desc) + '</span>' +
        '</div>' +
      '</div>';
    });
  }
  html += '</div>';
  return html;
}

// ===== Bug Board =====
function populateProjectSelects() {
  const selects = ['bugProjectSelect', 'adminProjectSelect', 'logProjectSelect'];
  selects.forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    const current = el.value;
    el.innerHTML = '<option value="">选择项目</option>';
    state.projects.filter(p => p.has_aion).forEach(p => {
      el.innerHTML += `<option value="${esc(p.path)}">${esc(p.name)}</option>`;
    });
    if (current) el.value = current;
  });
}

async function loadBugs() {
  const projectPath = document.getElementById('bugProjectSelect').value;
  if (!projectPath) {
    document.getElementById('bugList').innerHTML = '<div style="color:#484f58;font-size:13px;text-align:center;padding:40px;">选择一个项目查看 Bug</div>';
    document.getElementById('bugStatsBar').innerHTML = '';
    return;
  }
  const encoded = btoa(projectPath).replace(/\+/g,'-').replace(/\//g,'_').replace(/=/g,'');
  const status = document.getElementById('bugFilterStatus').value;
  const category = document.getElementById('bugFilterCategory').value;
  let qs = '';
  if (status) qs += '&status=' + status;
  if (category) qs += '&category=' + category;
  if (qs) qs = '?' + qs.slice(1);
  try {
    const [bugsData, statsData] = await Promise.all([
      api('GET', '/api/projects/' + encoded + '/bugs' + qs),
      api('GET', '/api/projects/' + encoded + '/bugs/stats')
    ]);
    renderBugStats(statsData);
    renderBugList(bugsData.bugs || []);
  } catch(e) {
    document.getElementById('bugList').innerHTML = '<div style="color:#f85149;padding:20px;">加载失败: ' + esc(String(e)) + '</div>';
  }
}

function renderBugStats(stats) {
  const el = document.getElementById('bugStatsBar');
  const byStatus = stats.by_status || {};
  const byCat = stats.by_category || {};
  const items = [
    { label: 'Open', count: byStatus.open || 0, color: '#f85149' },
    { label: 'Assigned', count: byStatus.assigned || 0, color: '#d29922' },
    { label: 'Fixing', count: (byStatus['in-progress'] || 0), color: '#58a6ff' },
    { label: 'Fixed', count: byStatus.fixed || 0, color: '#3fb950' },
    { label: 'Closed', count: byStatus.closed || 0, color: '#484f58' },
    { label: 'Financial Risk', count: stats.financial_risk || 0, color: '#f85149' },
  ];
  el.innerHTML = items.map(i =>
    `<div style="background:#161b22;border:1px solid #30363d;border-radius:8px;padding:12px 16px;min-width:100px;">
      <div style="font-size:22px;font-weight:700;color:${i.color};">${i.count}</div>
      <div style="font-size:12px;color:#8b949e;">${i.label}</div>
    </div>`
  ).join('');
  // Team load
  const load = stats.team_load || {};
  if (Object.keys(load).length > 0) {
    el.innerHTML += `<div style="background:#161b22;border:1px solid #30363d;border-radius:8px;padding:12px 16px;min-width:140px;">
      <div style="font-size:12px;color:#8b949e;margin-bottom:4px;">团队负载</div>
      ${Object.entries(load).map(([name, count]) =>
        `<div style="font-size:13px;color:#e6edf3;">${esc(name)}: <strong>${count}</strong> active</div>`
      ).join('')}
    </div>`;
  }
}

function renderBugList(bugs) {
  const el = document.getElementById('bugList');
  if (!bugs.length) {
    el.innerHTML = '<div style="color:#484f58;font-size:13px;text-align:center;padding:40px;">没有匹配的 Bug</div>';
    return;
  }
  const sevColors = { critical: '#f85149', high: '#d29922', medium: '#58a6ff', low: '#3fb950' };
  const sevIcons = { critical: '\u{1F534}', high: '\u{1F7E1}', medium: '\u{1F535}', low: '\u{1F7E2}' };
  const statusBadge = (s) => {
    const colors = { open: '#f85149', assigned: '#d29922', 'in-progress': '#58a6ff', fixed: '#3fb950', verified: '#3fb950', closed: '#484f58' };
    return `<span style="background:${colors[s]||'#484f58'}22;color:${colors[s]||'#484f58'};padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;">${s}</span>`;
  };
  el.innerHTML = `<div style="display:grid;gap:8px;">
    ${bugs.map(b => {
      const sev = b.severity || 'medium';
      const risk = b.risk_level === 'financial' ? '<span style="background:#f8514922;color:#f85149;padding:2px 6px;border-radius:4px;font-size:10px;margin-left:6px;">FINANCIAL RISK</span>' : '';
      const staleH = b.stale_hours || 0;
      const staleTxt = staleH > 24 ? Math.floor(staleH/24) + 'd' : staleH + 'h';
      const source = b.source_model && b.source_model !== 'manual' ? `<span style="color:#484f58;font-size:11px;margin-left:6px;">via ${esc(b.source_model)}</span>` : '';
      return `<div style="background:#161b22;border:1px solid #30363d;border-radius:8px;padding:14px 16px;display:flex;align-items:center;gap:12px;">
        <div style="font-size:14px;">${sevIcons[sev]||''}</div>
        <div style="flex:1;min-width:0;">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
            <span style="font-weight:600;color:#8b5cf6;font-size:13px;">${esc(b.id||'')}</span>
            ${statusBadge(b.status||'open')}
            <span style="color:${sevColors[sev]||'#58a6ff'};font-size:12px;">${sev}</span>
            ${risk}${source}
          </div>
          <div style="font-size:14px;color:#e6edf3;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${esc(b.title||'')}</div>
          <div style="font-size:12px;color:#484f58;margin-top:4px;">
            assignee: ${esc(b.assignee||'--')} &nbsp;|&nbsp; reporter: ${esc(b.reporter||'--')} &nbsp;|&nbsp; ${staleTxt} ago
          </div>
        </div>
      </div>`;
    }).join('')}
  </div>`;
}

// ===== Admin / Team Management =====
let teamConfig = { team: [], models: [], risk_keywords: { critical: [], low: [] } };
let adminProjectPath = '';

async function loadTeamConfig() {
  adminProjectPath = document.getElementById('adminProjectSelect').value;
  if (!adminProjectPath) {
    document.getElementById('teamMemberList').innerHTML = '<div style="color:#484f58;font-size:13px;text-align:center;padding:20px;">选择一个项目查看团队配置</div>';
    document.getElementById('modelList').innerHTML = '<div style="color:#484f58;font-size:13px;text-align:center;padding:20px;">选择一个项目查看模型配置</div>';
    return;
  }
  const encoded = btoa(adminProjectPath).replace(/\+/g,'-').replace(/\//g,'_').replace(/=/g,'');
  try {
    teamConfig = await api('GET', '/api/projects/' + encoded + '/team');
    renderTeamMembers();
    renderModels();
  } catch(e) {
    document.getElementById('teamMemberList').innerHTML = '<div style="color:#f85149;padding:20px;">加载失败: ' + esc(String(e)) + '</div>';
  }
}

function renderTeamMembers() {
  const el = document.getElementById('teamMemberList');
  const team = teamConfig.team || [];
  if (!team.length) {
    el.innerHTML = '<div style="color:#484f58;font-size:13px;text-align:center;padding:20px;">暂无团队成员。点击 "+ 添加成员" 开始配置。</div>';
    return;
  }
  const roleColors = { frontend: '#58a6ff', backend: '#3fb950', fullstack: '#d29922', tester: '#f85149' };
  el.innerHTML = team.map((m, i) =>
    `<div style="background:#161b22;border:1px solid #30363d;border-radius:8px;padding:14px 16px;display:flex;align-items:center;gap:12px;">
      <div style="width:36px;height:36px;background:#1c2128;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:16px;color:#8b949e;">
        ${esc((m.name||'?')[0])}
      </div>
      <div style="flex:1;">
        <div style="font-weight:600;color:#e6edf3;font-size:14px;">${esc(m.name||'')}</div>
        <div style="font-size:12px;color:#8b949e;">
          <span style="color:${roleColors[m.role]||'#8b949e'};font-weight:600;">${esc(m.role||'')}</span>
          &nbsp;|&nbsp; ${esc(m.git_email||'')}
        </div>
      </div>
      <button onclick="removeTeamMember(${i})" style="background:none;border:1px solid #30363d;color:#f85149;padding:4px 10px;border-radius:6px;cursor:pointer;font-size:12px;">删除</button>
    </div>`
  ).join('');
}

function renderModels() {
  const el = document.getElementById('modelList');
  const models = teamConfig.models || [];
  if (!models.length) {
    el.innerHTML = '<div style="color:#484f58;font-size:13px;text-align:center;padding:20px;">暂无模型配置。点击 "+ 添加模型" 配置交叉验证。</div>';
    return;
  }
  el.innerHTML = models.map((m, i) =>
    `<div style="background:#161b22;border:1px solid #30363d;border-radius:8px;padding:14px 16px;display:flex;align-items:center;gap:12px;">
      <div style="flex:1;">
        <div style="font-weight:600;color:#e6edf3;font-size:14px;">${esc(m.name||'')}</div>
        <div style="font-size:12px;color:#8b949e;">
          ${esc(m.provider||'')} &nbsp;|&nbsp; ${esc(m.default_model||'')} &nbsp;|&nbsp; env: ${esc(m.api_key_env||'')}
        </div>
      </div>
      <button onclick="removeModel(${i})" style="background:none;border:1px solid #30363d;color:#f85149;padding:4px 10px;border-radius:6px;cursor:pointer;font-size:12px;">删除</button>
    </div>`
  ).join('');
}

function addTeamMember() {
  if (!adminProjectPath) { toast('请先选择一个项目', 'error'); return; }
  const name = prompt('成员姓名:');
  if (!name) return;
  const role = prompt('角色 (frontend/backend/fullstack/tester):', 'frontend');
  if (!role) return;
  const email = prompt('Git Email:');
  if (!email) return;
  teamConfig.team = teamConfig.team || [];
  teamConfig.team.push({ name, role, git_email: email, expertise: [], active_bugs: 0 });
  saveTeamConfig();
}

function removeTeamMember(index) {
  if (!confirm('确定删除该成员?')) return;
  teamConfig.team.splice(index, 1);
  saveTeamConfig();
}

function addModel() {
  if (!adminProjectPath) { toast('请先选择一个项目', 'error'); return; }
  const name = prompt('模型名称 (如 gemini, gpt, deepseek):');
  if (!name) return;
  const provider = prompt('Provider (google/openai/openai-compatible):', 'openai');
  if (!provider) return;
  const endpoint = prompt('API Endpoint URL:');
  if (!endpoint) return;
  const keyEnv = prompt('API Key 环境变量名 (如 GEMINI_API_KEY):');
  if (!keyEnv) return;
  const model = prompt('默认模型 ID (如 gemini-2.5-pro):');
  if (!model) return;
  teamConfig.models = teamConfig.models || [];
  teamConfig.models.push({ name, provider, endpoint, api_key_env: keyEnv, default_model: model });
  saveTeamConfig();
}

function removeModel(index) {
  if (!confirm('确定删除该模型配置?')) return;
  teamConfig.models.splice(index, 1);
  saveTeamConfig();
}

async function saveTeamConfig() {
  const encoded = btoa(adminProjectPath).replace(/\+/g,'-').replace(/\//g,'_').replace(/=/g,'');
  try {
    await api('POST', '/api/projects/' + encoded + '/team', teamConfig);
    toast('团队配置已保存', 'success');
    renderTeamMembers();
    renderModels();
  } catch(e) {
    toast('保存失败: ' + String(e), 'error');
  }
}

// ===== Init =====
document.addEventListener('DOMContentLoaded', async function() {
  await loadProjects();
});
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Monitor HTML (Space Command Center)
# ---------------------------------------------------------------------------

MONITOR_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AIONCODE MISSION CONTROL</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --space-bg: #0b1426;
    --panel-bg: rgba(15, 25, 50, 0.85);
    --border: rgba(66, 133, 244, 0.25);
    --border-bright: rgba(66, 133, 244, 0.5);
    --white: #e8eaed;
    --blue: #4285f4;
    --amber: #fbbc04;
    --red: #ea4335;
    --green: #34a853;
    --muted: #8a9ab5;
    --font: 'Courier New', 'Consolas', monospace;
  }

  body {
    background: var(--space-bg);
    color: var(--white);
    font-family: var(--font);
    font-size: 13px;
    line-height: 1.5;
    overflow: hidden;
    height: 100vh;
  }

  /* -- Starfield -- */
  .starfield { position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: 0; pointer-events: none; }
  .star { position: absolute; background: #fff; border-radius: 50%; animation: twinkle linear infinite; }
  @keyframes twinkle { 0%, 100% { opacity: 0.2; } 50% { opacity: 1; } }

  /* -- Layout -- */
  .app { position: relative; z-index: 1; display: flex; flex-direction: column; height: 100vh; }

  /* -- Header -- */
  .header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 10px 24px;
    border-bottom: 1px solid var(--border);
    background: rgba(10, 18, 36, 0.95);
  }
  .header-left { display: flex; align-items: center; gap: 16px; }
  .logo-mark {
    width: 36px; height: 36px; border: 2px solid var(--blue);
    border-radius: 50%; display: flex; align-items: center; justify-content: center;
    font-size: 14px; font-weight: bold; color: var(--blue);
  }
  .header-title { font-size: 18px; font-weight: bold; letter-spacing: 4px; color: var(--white); }
  .header-subtitle { font-size: 10px; color: var(--muted); letter-spacing: 2px; margin-top: 2px; }
  .header-right { display: flex; align-items: center; gap: 24px; }
  .met-display { text-align: right; }
  .met-label { font-size: 10px; color: var(--muted); letter-spacing: 1px; }
  .met-value { font-size: 22px; color: var(--blue); font-weight: bold; letter-spacing: 2px; }
  .conn-status { display: flex; align-items: center; gap: 8px; font-size: 11px; }
  .conn-dot {
    width: 8px; height: 8px; border-radius: 50%; background: var(--green);
    animation: pulse-dot 2s ease-in-out infinite;
  }
  .conn-dot.offline { background: var(--red); animation: none; }
  @keyframes pulse-dot {
    0%, 100% { box-shadow: 0 0 0 0 rgba(52, 168, 83, 0.5); }
    50% { box-shadow: 0 0 0 6px rgba(52, 168, 83, 0); }
  }

  /* -- Telemetry Bar -- */
  .telemetry-bar {
    display: flex; align-items: stretch; gap: 1px;
    padding: 8px 24px;
    border-bottom: 1px solid var(--border);
    background: rgba(10, 18, 36, 0.9);
  }
  .telemetry-bar .panel-label {
    font-size: 10px; color: var(--blue); letter-spacing: 2px;
    margin-right: 16px; display: flex; align-items: center;
  }
  .metric-box {
    flex: 1; padding: 8px 14px;
    border: 1px solid var(--border);
    border-radius: 4px; margin: 0 4px;
    background: rgba(66, 133, 244, 0.04);
  }
  .metric-label { font-size: 9px; color: var(--muted); letter-spacing: 1px; text-transform: uppercase; }
  .metric-value { font-size: 18px; font-weight: bold; margin-top: 2px; }
  .metric-value.blue { color: var(--blue); }
  .metric-value.green { color: var(--green); }
  .metric-value.amber { color: var(--amber); }
  .metric-sub { font-size: 10px; color: var(--muted); margin-top: 1px; }

  /* -- Main Content -- */
  .main-content { flex: 1; display: flex; gap: 1px; padding: 12px 24px; overflow: hidden; }

  /* -- Panels -- */
  .panel {
    border: 1px solid var(--border); border-radius: 6px;
    background: var(--panel-bg);
    display: flex; flex-direction: column; overflow: hidden;
  }
  .panel-header {
    padding: 10px 16px;
    border-bottom: 1px solid var(--border);
    display: flex; align-items: center; justify-content: space-between;
    background: rgba(66, 133, 244, 0.06);
  }
  .panel-header h2 { font-size: 11px; font-weight: bold; letter-spacing: 2px; color: var(--blue); }
  .panel-header .count { font-size: 10px; color: var(--muted); }
  .panel-body { flex: 1; overflow-y: auto; padding: 12px 16px; }

  .panel-left { flex: 1.1; margin-right: 12px; }
  .panel-right { flex: 0.9; position: relative; }

  .panel-body::-webkit-scrollbar { width: 4px; }
  .panel-body::-webkit-scrollbar-track { background: transparent; }
  .panel-body::-webkit-scrollbar-thumb { background: var(--border-bright); border-radius: 2px; }

  /* -- Fleet Status: Main Craft -- */
  .main-craft {
    border: 1px solid var(--border-bright); border-radius: 6px;
    padding: 14px; margin-bottom: 16px;
    background: rgba(66, 133, 244, 0.05);
  }
  .craft-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
  .craft-name { font-size: 14px; font-weight: bold; color: var(--blue); }
  .craft-status {
    font-size: 10px; padding: 2px 10px; border-radius: 10px;
    text-transform: uppercase; letter-spacing: 1px; font-weight: bold;
  }
  .status-standby { background: rgba(138, 154, 181, 0.15); color: var(--muted); border: 1px solid rgba(138, 154, 181, 0.3); }
  .status-active { background: rgba(52, 168, 83, 0.15); color: var(--green); border: 1px solid rgba(52, 168, 83, 0.3); }
  .status-idle { background: rgba(251, 188, 4, 0.15); color: var(--amber); border: 1px solid rgba(251, 188, 4, 0.3); }
  .status-returned { background: rgba(138, 154, 181, 0.15); color: var(--muted); border: 1px solid rgba(138, 154, 181, 0.3); }
  .status-offline { background: rgba(234, 67, 53, 0.15); color: var(--red); border: 1px solid rgba(234, 67, 53, 0.3); }
  .craft-detail { font-size: 11px; color: var(--muted); margin-bottom: 6px; }
  .craft-detail span { color: var(--white); }
  .craft-detail span.highlight { color: var(--green); }

  /* -- Fleet Grid -- */
  .fleet-section-title {
    font-size: 10px; color: var(--blue); letter-spacing: 2px;
    margin-bottom: 8px; padding-bottom: 6px;
    border-bottom: 1px solid var(--border);
  }
  .fleet-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 16px; }
  .fleet-unit {
    border: 1px solid var(--border); border-radius: 4px;
    padding: 10px 12px; background: rgba(15, 25, 50, 0.6);
    transition: border-color 0.3s;
  }
  .fleet-unit:hover { border-color: var(--border-bright); }
  .fleet-unit-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; }
  .fleet-unit-name { font-size: 11px; font-weight: bold; color: var(--white); }
  .fleet-unit-status { font-size: 9px; padding: 1px 6px; border-radius: 8px; }
  .fleet-unit-task { font-size: 10px; color: var(--muted); }

  /* -- Tool Stats -- */
  .section-divider { height: 1px; background: var(--border); margin: 12px 0; }
  .tool-row { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; font-size: 10px; }
  .tool-name { width: 70px; color: var(--muted); text-align: right; overflow: hidden; text-overflow: ellipsis; }
  .tool-bar-bg { flex: 1; height: 4px; background: rgba(66, 133, 244, 0.1); border-radius: 2px; overflow: hidden; }
  .tool-bar-fill { height: 100%; background: linear-gradient(90deg, var(--blue), #64b5f6); border-radius: 2px; transition: width 0.5s; }
  .tool-count { width: 30px; color: var(--muted); font-size: 9px; }

  /* -- Comms Log -- */
  .comms-entry {
    padding: 8px 0; border-bottom: 1px solid rgba(66, 133, 244, 0.1);
    animation: comm-in 0.4s ease-out;
  }
  .comms-entry:last-child { border-bottom: none; }
  @keyframes comm-in { from { opacity: 0; transform: translateY(-8px); } to { opacity: 1; transform: translateY(0); } }
  .comms-time { font-size: 10px; color: var(--blue); margin-bottom: 3px; }
  .comms-source { font-size: 10px; font-weight: bold; display: inline; margin-right: 6px; }
  .comms-source.src-tool { color: var(--blue); }
  .comms-source.src-fleet { color: #bb86fc; }
  .comms-source.src-sys { color: var(--green); }
  .comms-source.src-cmd { color: var(--amber); }
  .comms-source.src-file { color: #64b5f6; }
  .comms-text { font-size: 11px; color: var(--muted); display: inline; }
  .comms-text.priority-high { color: var(--red); }
  .comms-text.priority-ok { color: var(--green); }

  /* -- Radar -- */
  .radar-container { position: absolute; bottom: 12px; right: 16px; width: 110px; height: 110px; }
  .radar {
    width: 100%; height: 100%; border-radius: 50%;
    border: 1px solid var(--border-bright);
    position: relative; overflow: hidden;
    background: radial-gradient(circle, rgba(66, 133, 244, 0.05) 0%, transparent 70%);
  }
  .radar-cross-h, .radar-cross-v { position: absolute; background: rgba(66, 133, 244, 0.15); }
  .radar-cross-h { width: 100%; height: 1px; top: 50%; }
  .radar-cross-v { height: 100%; width: 1px; left: 50%; }
  .radar-ring { position: absolute; border: 1px solid rgba(66, 133, 244, 0.12); border-radius: 50%; }
  .radar-ring-1 { width: 33%; height: 33%; top: 33.5%; left: 33.5%; }
  .radar-ring-2 { width: 66%; height: 66%; top: 17%; left: 17%; }
  .radar-sweep {
    position: absolute; top: 50%; left: 50%;
    width: 50%; height: 2px;
    background: linear-gradient(90deg, var(--blue), transparent);
    transform-origin: 0 50%;
    animation: sweep 4s linear infinite;
  }
  @keyframes sweep { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
  .radar-blip {
    position: absolute; width: 4px; height: 4px;
    background: var(--green); border-radius: 50%;
    animation: blip-pulse 2s ease-in-out infinite;
  }
  .radar-blip.returned { background: var(--muted); animation: none; opacity: 0.5; }
  @keyframes blip-pulse { 0%, 100% { opacity: 0.4; } 50% { opacity: 1; } }

  /* -- Footer -- */
  .footer {
    padding: 6px 24px; font-size: 10px; color: var(--muted);
    display: flex; justify-content: space-between; align-items: center;
    border-top: 1px solid var(--border);
    background: rgba(10, 18, 36, 0.9);
  }
  .clear-btn {
    font-family: var(--font); font-size: 10px;
    color: var(--muted); border: 1px solid var(--border);
    padding: 2px 10px; border-radius: 2px; cursor: pointer;
    letter-spacing: 1px; background: transparent; transition: all 0.2s;
  }
  .clear-btn:hover { color: var(--red); border-color: rgba(234, 67, 53, 0.4); }
  .back-link {
    color: var(--blue); text-decoration: none; font-size: 10px;
    letter-spacing: 1px; opacity: 0.7; transition: opacity 0.2s;
  }
  .back-link:hover { opacity: 1; }

  @media(max-width:900px) { .main-content { flex-direction: column; } .radar-container { display: none; } }
</style>
</head>
<body>

<div class="starfield" id="starfield"></div>

<div class="app">
  <!-- Header -->
  <div class="header">
    <div class="header-left">
      <div class="logo-mark">AC</div>
      <div>
        <div class="header-title">AIONCODE MISSION CONTROL</div>
        <div class="header-subtitle">__PROJECT_NAME__</div>
      </div>
    </div>
    <div class="header-right">
      <div class="conn-status">
        <div class="conn-dot" id="conn-dot"></div>
        <span id="conn-text">CONNECTING</span>
      </div>
      <div class="met-display">
        <div class="met-label">MISSION ELAPSED TIME</div>
        <div class="met-value" id="met">00:00:00</div>
      </div>
    </div>
  </div>

  <!-- Telemetry Bar -->
  <div class="telemetry-bar">
    <div class="panel-label">TELEMETRY</div>
    <div class="metric-box">
      <div class="metric-label">MET</div>
      <div class="metric-value blue" id="tel-met">00:00</div>
    </div>
    <div class="metric-box">
      <div class="metric-label">Operations</div>
      <div class="metric-value green" id="tel-ops">0</div>
      <div class="metric-sub">tool calls executed</div>
    </div>
    <div class="metric-box">
      <div class="metric-label">Fleet</div>
      <div class="metric-value amber" id="tel-fleet">1</div>
      <div class="metric-sub" id="tel-fleet-sub">standby</div>
    </div>
    <div class="metric-box">
      <div class="metric-label">Tokens</div>
      <div class="metric-value blue" id="tel-tokens">&mdash;</div>
      <div class="metric-sub">estimated</div>
    </div>
    <div class="metric-box">
      <div class="metric-label">Payload</div>
      <div class="metric-value green" id="tel-files">0</div>
      <div class="metric-sub">files modified</div>
    </div>
  </div>

  <!-- Main Content -->
  <div class="main-content">
    <!-- Left Panel: Fleet Status -->
    <div class="panel panel-left">
      <div class="panel-header">
        <h2>FLEET STATUS</h2>
        <span class="count" id="fleet-count-label">1 UNIT TRACKED</span>
      </div>
      <div class="panel-body">
        <!-- Main Craft -->
        <div class="main-craft">
          <div class="craft-header">
            <span class="craft-name">ALPHA-1 &mdash; PRIMARY</span>
            <span class="craft-status status-standby" id="craft-status">STANDBY</span>
          </div>
          <div class="craft-detail">CURRENT OP: <span id="craft-tool">&mdash;</span></div>
          <div class="craft-detail">TARGET: <span id="craft-file">&mdash;</span></div>
          <div class="craft-detail">DURATION: <span id="craft-dur">00:00</span> &middot; OPS: <span id="craft-ops">0</span></div>
        </div>

        <!-- Fleet Grid (dynamic) -->
        <div id="fleet-section" style="display:none">
          <div class="fleet-section-title">SUBAGENT FLEET</div>
          <div class="fleet-grid" id="fleet-grid"></div>
        </div>

        <div class="section-divider"></div>

        <!-- Tool Usage -->
        <div>
          <div class="fleet-section-title">TOOL USAGE</div>
          <div id="tool-stats"><div style="color:var(--muted);font-size:10px">Awaiting telemetry...</div></div>
        </div>
      </div>
    </div>

    <!-- Right Panel: Comms Log -->
    <div class="panel panel-right">
      <div class="panel-header">
        <h2>COMMS LOG</h2>
        <span class="count" id="comms-count">0 ENTRIES</span>
      </div>
      <div class="panel-body" id="comms-log">
        <div class="comms-entry">
          <div class="comms-time">T+00:00:00</div>
          <span class="comms-source src-sys">[SYS]</span>
          <span class="comms-text priority-ok">Mission Control online &mdash; awaiting telemetry uplink</span>
        </div>
      </div>
      <!-- Radar -->
      <div class="radar-container">
        <div class="radar">
          <div class="radar-cross-h"></div>
          <div class="radar-cross-v"></div>
          <div class="radar-ring radar-ring-1"></div>
          <div class="radar-ring radar-ring-2"></div>
          <div class="radar-sweep"></div>
          <div id="radar-blips"></div>
        </div>
      </div>
    </div>
  </div>

  <!-- Footer -->
  <div class="footer">
    <div><a class="back-link" href="/">&larr; DASHBOARD</a></div>
    <div id="footer-events">0 events</div>
    <button class="clear-btn" onclick="clearEvents()">[ CLEAR LOG ]</button>
  </div>
</div>

<script>
(function() {
  var ENC = '__ENCODED__';
  var API = '/api/monitor/' + ENC;

  // ===== STATE =====
  var S = {
    lastLine: 0,
    metStart: null,
    mainAgent: { status: 'STANDBY', tool: null, file: null },
    subagents: {},
    toolCounts: {},
    filesChanged: {},
    totalOps: 0,
    connected: false,
    commsEntries: [],
    maxComms: 200
  };

  // ===== CALLSIGNS =====
  var CALLSIGNS = ['BRAVO','CHARLIE','DELTA','ECHO','FOXTROT','GOLF','HOTEL','INDIA','JULIET','KILO','LIMA','MIKE'];
  var callsignMap = {};
  var callsignIdx = 0;

  function getCallsign(id) {
    if (!callsignMap[id]) {
      callsignMap[id] = CALLSIGNS[callsignIdx % CALLSIGNS.length] + '-' + (callsignIdx + 1);
      callsignIdx++;
    }
    return callsignMap[id];
  }

  // ===== STARFIELD =====
  var sf = document.getElementById('starfield');
  for (var i = 0; i < 160; i++) {
    var star = document.createElement('div');
    star.className = 'star';
    var sz = Math.random() * 2 + 0.5;
    star.style.width = sz + 'px';
    star.style.height = sz + 'px';
    star.style.left = Math.random() * 100 + '%';
    star.style.top = Math.random() * 100 + '%';
    star.style.animationDuration = (Math.random() * 4 + 2) + 's';
    star.style.animationDelay = (Math.random() * 4) + 's';
    sf.appendChild(star);
  }

  // ===== POLLING =====
  function poll() {
    fetch(API + '/events?since=' + S.lastLine)
      .then(function(r) { return r.json(); })
      .then(function(data) {
        S.connected = true;
        for (var i = 0; i < data.events.length; i++) {
          processEvent(data.events[i]);
        }
        S.lastLine = data.total;
        updateUI();
      })
      .catch(function() {
        S.connected = false;
        updateConn();
      });
  }
  setInterval(poll, 1000);
  poll();

  // ===== EVENT PROCESSING =====
  function processEvent(event) {
    var d = event.data || event;
    var hook = d.hook_event_name || d.event || '';
    var ts = event.ts || new Date().toISOString();
    var metTime = formatMET(ts);

    S.totalOps++;
    if (!S.metStart) S.metStart = new Date(ts);

    switch (hook) {
      case 'PreToolUse':
        var tool = d.tool_name || 'unknown';
        S.mainAgent.status = 'ACTIVE';
        S.mainAgent.tool = tool;
        var inp = d.tool_input || {};
        var file = inp.file_path || inp.path || inp.file || inp.pattern || inp.command || null;
        if (file) S.mainAgent.file = file;
        S.toolCounts[tool] = (S.toolCounts[tool] || 0) + 1;
        addComm(metTime, 'ALPHA-1', 'tool', 'Tool call: ' + tool + ' \u2192 ' + trunc(file || 'system', 50), '');
        break;
      case 'PostToolUse':
        var t2 = d.tool_name || '';
        if (['Write','Edit','NotebookEdit'].indexOf(t2) >= 0 && d.tool_input && d.tool_input.file_path) {
          S.filesChanged[d.tool_input.file_path] = true;
          addComm(metTime, 'SYS', 'sys', 'Payload update: ' + trunc(d.tool_input.file_path, 45), 'priority-ok');
        }
        break;
      case 'SubagentStart':
        var aid = d.agent_id || d.session_id || ('sub-' + Object.keys(S.subagents).length);
        var atype = d.agent_type || d.subagent_type || d.description || 'recon';
        S.subagents[aid] = { id: aid, type: atype, status: 'ACTIVE', started: ts };
        addComm(metTime, getCallsign(aid), 'fleet', 'Deployed \u2014 mission: ' + trunc(atype, 30), '');
        break;
      case 'SubagentStop':
        var sid = d.agent_id || d.session_id || '';
        if (S.subagents[sid]) {
          S.subagents[sid].status = 'RETURNED';
          addComm(metTime, getCallsign(sid), 'fleet', 'Mission complete \u2014 returned to base', 'priority-ok');
        }
        break;
      case 'Stop':
        S.mainAgent.status = 'IDLE';
        S.mainAgent.tool = null;
        addComm(metTime, 'SYS', 'cmd', 'Agent cycle complete \u2014 awaiting orders', '');
        break;
      case 'SessionStart':
        S.metStart = new Date(ts);
        addComm(metTime, 'SYS', 'sys', 'Session initiated \u2014 all systems nominal', 'priority-ok');
        break;
      case 'SessionEnd':
        S.mainAgent.status = 'OFFLINE';
        S.mainAgent.tool = null;
        addComm(metTime, 'SYS', 'sys', 'Session terminated \u2014 signal lost', 'priority-high');
        break;
      default:
        if (hook) addComm(metTime, 'SYS', 'sys', hook, '');
    }
  }

  function addComm(time, source, srcClass, text, priority) {
    S.commsEntries.unshift({ time: time, source: source, srcClass: srcClass, text: text, priority: priority });
    if (S.commsEntries.length > S.maxComms) S.commsEntries.pop();
  }

  // ===== UI UPDATES =====
  function updateUI() {
    updateConn();
    updateMET();
    updateTelemetry();
    updateCraft();
    updateFleet();
    updateToolStats();
    updateComms();
    updateRadar();
    document.getElementById('footer-events').textContent = S.lastLine + ' events';
  }

  function updateConn() {
    var dot = document.getElementById('conn-dot');
    var txt = document.getElementById('conn-text');
    if (S.connected) {
      dot.className = 'conn-dot';
      txt.textContent = 'UPLINK ACTIVE';
    } else {
      dot.className = 'conn-dot offline';
      txt.textContent = 'LINK LOST';
    }
  }

  function updateMET() {
    if (!S.metStart) return;
    var sec = Math.max(0, Math.floor((Date.now() - S.metStart.getTime()) / 1000));
    var h = pad(Math.floor(sec / 3600));
    var m = pad(Math.floor((sec % 3600) / 60));
    var s = pad(sec % 60);
    document.getElementById('met').textContent = h + ':' + m + ':' + s;
    document.getElementById('tel-met').textContent = m + ':' + s;
    document.getElementById('craft-dur').textContent = m + ':' + s;
  }
  setInterval(function() { if (S.metStart) updateMET(); }, 1000);

  function updateTelemetry() {
    document.getElementById('tel-ops').textContent = S.totalOps;
    var activeFleet = 1;
    var agents = Object.values(S.subagents);
    for (var i = 0; i < agents.length; i++) {
      if (agents[i].status === 'ACTIVE') activeFleet++;
    }
    var totalFleet = 1 + agents.length;
    document.getElementById('tel-fleet').textContent = activeFleet + '/' + totalFleet;
    document.getElementById('tel-fleet-sub').textContent = activeFleet === 1 && agents.length === 0 ? 'standby' : 'units active';
    document.getElementById('tel-files').textContent = Object.keys(S.filesChanged).length;
    document.getElementById('craft-ops').textContent = S.totalOps;
  }

  function updateCraft() {
    var st = S.mainAgent.status;
    var el = document.getElementById('craft-status');
    el.textContent = st;
    el.className = 'craft-status status-' + st.toLowerCase();
    var toolEl = document.getElementById('craft-tool');
    toolEl.textContent = S.mainAgent.tool || '\u2014';
    if (S.mainAgent.tool) toolEl.className = 'highlight'; else toolEl.className = '';
    document.getElementById('craft-file').textContent = S.mainAgent.file ? trunc(S.mainAgent.file, 45) : '\u2014';
  }

  function updateFleet() {
    var agents = Object.values(S.subagents);
    var section = document.getElementById('fleet-section');
    var grid = document.getElementById('fleet-grid');
    var label = document.getElementById('fleet-count-label');

    if (agents.length === 0) {
      section.style.display = 'none';
      label.textContent = '1 UNIT TRACKED';
      return;
    }
    section.style.display = '';
    label.textContent = (1 + agents.length) + ' UNITS TRACKED';

    grid.innerHTML = agents.map(function(a) {
      var cs = getCallsign(a.id);
      var stCls = a.status === 'ACTIVE' ? 'status-active' : 'status-returned';
      return '<div class="fleet-unit">' +
        '<div class="fleet-unit-header">' +
          '<span class="fleet-unit-name">' + cs + '</span>' +
          '<span class="fleet-unit-status ' + stCls + '">' + a.status + '</span>' +
        '</div>' +
        '<div class="fleet-unit-task">' + esc(trunc(a.type, 30)) + '</div>' +
      '</div>';
    }).join('');
  }

  function updateToolStats() {
    var entries = Object.entries(S.toolCounts).sort(function(a, b) { return b[1] - a[1]; });
    var container = document.getElementById('tool-stats');
    if (entries.length === 0) {
      container.innerHTML = '<div style="color:var(--muted);font-size:10px">Awaiting telemetry...</div>';
      return;
    }
    var max = entries[0][1];
    container.innerHTML = entries.slice(0, 8).map(function(e) {
      var pct = Math.round((e[1] / max) * 100);
      return '<div class="tool-row">' +
        '<span class="tool-name">' + esc(e[0]) + '</span>' +
        '<div class="tool-bar-bg"><div class="tool-bar-fill" style="width:' + pct + '%"></div></div>' +
        '<span class="tool-count">' + e[1] + '</span>' +
      '</div>';
    }).join('');
  }

  function updateComms() {
    var log = document.getElementById('comms-log');
    var countEl = document.getElementById('comms-count');
    // Rebuild comms (newest first)
    var html = '';
    var len = Math.min(S.commsEntries.length, 50);
    for (var i = 0; i < len; i++) {
      var c = S.commsEntries[i];
      html += '<div class="comms-entry">' +
        '<div class="comms-time">' + c.time + '</div>' +
        '<span class="comms-source src-' + c.srcClass + '">[' + esc(c.source) + ']</span>' +
        '<span class="comms-text ' + c.priority + '">' + esc(c.text) + '</span>' +
      '</div>';
    }
    log.innerHTML = html;
    countEl.textContent = S.commsEntries.length + ' ENTRIES';
  }

  function updateRadar() {
    var blips = document.getElementById('radar-blips');
    var agents = Object.values(S.subagents);
    var html = '';
    for (var i = 0; i < agents.length; i++) {
      var angle = (i / Math.max(agents.length, 1)) * 2 * Math.PI - Math.PI / 2;
      var radius = 20 + (i % 3) * 10;
      var x = 50 + radius * Math.cos(angle);
      var y = 50 + radius * Math.sin(angle);
      var cls = agents[i].status === 'ACTIVE' ? '' : ' returned';
      html += '<div class="radar-blip' + cls + '" style="left:' + x + '%;top:' + y + '%"></div>';
    }
    blips.innerHTML = html;
  }

  // ===== CLEAR =====
  window.clearEvents = function() {
    if (!confirm('Clear all events? This cannot be undone.')) return;
    fetch(API + '/clear', { method: 'POST' })
      .then(function() {
        S.lastLine = 0; S.totalOps = 0; S.metStart = null;
        S.mainAgent = { status: 'STANDBY', tool: null, file: null };
        S.subagents = {}; S.toolCounts = {}; S.filesChanged = {};
        S.commsEntries = []; callsignMap = {}; callsignIdx = 0;
        addComm('T+00:00:00', 'SYS', 'sys', 'Event log cleared \u2014 standing by', 'priority-ok');
        updateUI();
      });
  };

  // ===== HELPERS =====
  function formatMET(isoStr) {
    if (!S.metStart) return 'T+00:00:00';
    var sec = Math.max(0, Math.floor((new Date(isoStr).getTime() - S.metStart.getTime()) / 1000));
    return 'T+' + pad(Math.floor(sec / 3600)) + ':' + pad(Math.floor((sec % 3600) / 60)) + ':' + pad(sec % 60);
  }
  function pad(n) { return n < 10 ? '0' + n : '' + n; }
  function trunc(s, max) { if (!s) return ''; s = String(s); return s.length > max ? s.slice(0, max - 1) + '\u2026' : s; }
  function esc(s) { var d = document.createElement('div'); d.textContent = s; return d.innerHTML; }
})();
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------

class ReusableTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    allow_reuse_port = True
    daemon_threads = True


def main():
    projects = load_projects()
    aion_count = sum(1 for p in projects if p["has_aion"])

    print(f"\033[1;35mAionCode Dashboard\033[0m")
    print(f"  URL:      http://localhost:{PORT}")
    print(f"  Projects: {len(projects)} registered ({aion_count} with .aion/)")
    print(f"  Data:     {PROJECTS_FILE}")
    print()

    with ReusableTCPServer(("", PORT), DashboardHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down.")
            httpd.shutdown()


if __name__ == "__main__":
    main()
