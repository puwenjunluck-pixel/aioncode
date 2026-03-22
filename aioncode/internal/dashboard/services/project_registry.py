"""Project registry — load, save, add, remove projects."""

from __future__ import annotations

import json
from pathlib import Path

from aioncode.internal.dashboard.config import resolve_projects_file

_PROJECTS_FILE: Path | None = None


def _get_projects_file() -> Path:
    global _PROJECTS_FILE
    if _PROJECTS_FILE is None:
        _PROJECTS_FILE = resolve_projects_file()
    return _PROJECTS_FILE


def load_projects() -> list[dict]:
    """Load project list from projects.json, skipping missing directories."""
    pf = _get_projects_file()
    if not pf.exists():
        return []
    try:
        data = json.loads(pf.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    valid = []
    for p in data:
        path = p.get("path", "")
        if Path(path).is_dir():
            p["has_aion"] = (Path(path) / ".aion").is_dir()
            valid.append(p)

    if len(valid) != len(data):
        save_projects(valid)

    return valid


def save_projects(projects: list[dict]) -> None:
    """Persist project list to projects.json."""
    pf = _get_projects_file()
    pf.parent.mkdir(parents=True, exist_ok=True)
    pf.write_text(json.dumps(projects, indent=2, ensure_ascii=False), encoding="utf-8")


def add_project(path: str) -> dict:
    """Add a project to the registry.

    Returns:
        dict with 'ok' and 'message' keys.
    """
    resolved = str(Path(path).resolve())
    if not Path(resolved).is_dir():
        return {"ok": False, "message": f"Directory not found: {resolved}"}

    projects = load_projects()
    for p in projects:
        if p.get("path") == resolved:
            return {"ok": False, "message": f"Already registered: {resolved}"}

    projects.append(
        {
            "path": resolved,
            "name": Path(resolved).name,
            "has_aion": (Path(resolved) / ".aion").is_dir(),
        }
    )
    save_projects(projects)
    return {"ok": True, "message": f"Added: {resolved}"}


def remove_project(path: str) -> dict:
    """Remove a project from the registry (does not delete files).

    Returns:
        dict with 'ok' and 'message' keys.
    """
    resolved = str(Path(path).resolve())
    projects = load_projects()
    new_list = [p for p in projects if p.get("path") != resolved]

    if len(new_list) == len(projects):
        return {"ok": False, "message": f"Not registered: {resolved}"}

    save_projects(new_list)
    return {"ok": True, "message": f"Removed: {resolved}"}
