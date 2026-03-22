"""API routes for filesystem browsing."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Query

router = APIRouter(tags=["browse"])

# Directories to skip when browsing
_SKIP_DIRS = {
    "node_modules",
    "__pycache__",
    "venv",
    ".venv",
    "Library",
    "Applications",
    ".Trash",
    ".git",
}


@router.get("/api/browse")
async def browse_filesystem(
    path: str = Query(default="~"),
) -> dict:
    """Browse directories for project selection."""
    browse_path = Path(path).expanduser().resolve()
    if not browse_path.is_dir():
        return {"ok": False, "message": f"Not a directory: {path}"}

    items = []
    try:
        for entry in sorted(browse_path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
            # Skip hidden dirs (except .aion) and system dirs
            if entry.name.startswith(".") and entry.name != ".aion":
                continue
            if entry.name in _SKIP_DIRS:
                continue
            if not entry.is_dir():
                continue

            items.append(
                {
                    "name": entry.name,
                    "path": str(entry),
                    "has_aion": (entry / ".aion").is_dir(),
                    "has_git": (entry / ".git").is_dir(),
                }
            )
    except PermissionError:
        return {"ok": False, "message": f"Permission denied: {path}"}

    return {
        "ok": True,
        "current": str(browse_path),
        "parent": str(browse_path.parent),
        "items": items,
    }
