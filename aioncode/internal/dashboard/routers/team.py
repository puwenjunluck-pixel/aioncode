"""API routes for team configuration."""

from __future__ import annotations

from fastapi import APIRouter

from aioncode.internal.dashboard.services.encoding import decode_project_path
from aioncode.internal.dashboard.services.team import (
    is_admin,
    read_team_config,
    write_team_config,
)

router = APIRouter(tags=["team"])


@router.get("/api/projects/{encoded}/team")
async def read_team(encoded: str) -> dict:
    """Read team configuration."""
    project_path = decode_project_path(encoded)
    config = read_team_config(project_path)
    return {"ok": True, **config}


@router.post("/api/projects/{encoded}/team")
async def write_team(encoded: str, config: dict) -> dict:
    """Write team configuration (admin only)."""
    if not is_admin():
        return {"ok": False, "message": "Admin only"}
    project_path = decode_project_path(encoded)
    return write_team_config(project_path, config)
