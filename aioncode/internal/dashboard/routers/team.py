"""API routes for team configuration and model switching."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from aioncode.internal.dashboard.services.encoding import decode_project_path
from aioncode.internal.dashboard.services.team import (
    check_env_vars,
    get_current_model,
    is_admin,
    read_team_config,
    switch_model,
    write_team_config,
)

router = APIRouter(tags=["team"])


class EnvCheckRequest(BaseModel):
    """Request body for environment variable check."""

    names: list[str]


class SwitchModelRequest(BaseModel):
    """Request body for model switching."""

    provider_name: str
    model_name: str


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


@router.post("/api/projects/{encoded}/team/check-env")
async def check_env(encoded: str, req: EnvCheckRequest) -> dict:
    """Check which environment variables are set (without revealing values)."""
    decode_project_path(encoded)  # validate path
    return {"ok": True, "env_status": check_env_vars(req.names)}


@router.post("/api/projects/{encoded}/team/switch-model")
async def switch_model_endpoint(encoded: str, req: SwitchModelRequest) -> dict:
    """Switch active model by updating Claude Code settings."""
    if not is_admin():
        return {"ok": False, "message": "Admin only"}
    project_path = decode_project_path(encoded)
    return switch_model(project_path, req.provider_name, req.model_name)


@router.get("/api/projects/{encoded}/team/current-model")
async def current_model(encoded: str) -> dict:
    """Read current active model from Claude Code settings."""
    decode_project_path(encoded)  # validate path
    return {"ok": True, **get_current_model()}
