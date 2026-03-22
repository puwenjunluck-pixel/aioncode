"""API routes for project management."""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

from aioncode.internal.dashboard.services.encoding import decode_project_path
from aioncode.internal.dashboard.services.project_registry import (
    add_project,
    load_projects,
    remove_project,
)
from aioncode.internal.dashboard.services.stats import get_project_stats

router = APIRouter(tags=["projects"])


class PathRequest(BaseModel):
    path: str


@router.get("/api/projects")
async def list_projects(request: Request) -> list[dict]:
    """List all registered projects."""
    return load_projects()


@router.post("/api/projects/add")
async def add_project_route(body: PathRequest) -> dict:
    """Add a project by path."""
    return add_project(body.path)


@router.post("/api/projects/remove")
async def remove_project_route(body: PathRequest) -> dict:
    """Remove a project from registry."""
    return remove_project(body.path)


@router.post("/api/projects/init")
async def init_project_route(body: PathRequest) -> dict:
    """Initialize .aion/ in a project using core init logic."""
    from pathlib import Path

    from aioncode.core.project import init_project

    target = Path(body.path).resolve()
    upgrade = (target / ".aion").is_dir()
    result = init_project(target, upgrade=upgrade, update_gitignore=True)

    return {
        "ok": result.ok,
        "message": result.message,
        "created": result.created,
        "updated": result.updated,
        "skipped": result.skipped,
    }


@router.get("/api/projects/{encoded}/stats")
async def project_stats(encoded: str) -> dict:
    """Get project statistics."""
    project_path = decode_project_path(encoded)
    return get_project_stats(project_path)


@router.post("/api/projects/{encoded}/upgrade")
async def upgrade_project(encoded: str) -> dict:
    """Run upgrade on a project."""
    import subprocess

    from aioncode.internal.dashboard.services.team import is_admin

    if not is_admin():
        return {"ok": False, "message": "Admin only"}

    project_path = decode_project_path(encoded)
    try:
        result = subprocess.run(
            ["aioncode", "init", project_path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return {
            "ok": result.returncode == 0,
            "message": result.stdout or result.stderr,
        }
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return {"ok": False, "message": str(e)}
