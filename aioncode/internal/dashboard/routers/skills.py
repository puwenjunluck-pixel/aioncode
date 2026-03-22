"""API routes for skill management — global (not project-scoped)."""

from __future__ import annotations

from fastapi import APIRouter

from aioncode.internal.dashboard.services.skills import (
    delete_skill,
    install_plugin,
    list_marketplace_plugins,
    list_skills,
    read_skill,
)

router = APIRouter(tags=["skills"])


@router.get("/api/skills/marketplace")
async def marketplace_route() -> dict:
    """List available marketplace plugins.

    Must be registered BEFORE /api/skills/{name} to avoid path collision.
    """
    plugins = list_marketplace_plugins()
    return {"ok": True, "plugins": plugins}


@router.post("/api/skills/marketplace/install")
async def install_plugin_route(body: dict) -> dict:
    """Install a marketplace plugin via claude CLI."""
    name = body.get("name", "")
    if not name:
        return {"ok": False, "message": "Missing plugin name"}
    return install_plugin(name)


@router.get("/api/skills")
async def list_skills_route() -> dict:
    """List all installed skills."""
    skills = list_skills()
    return {"ok": True, "skills": skills}


@router.delete("/api/skills/{name}")
async def delete_skill_route(name: str) -> dict:
    """Delete an installed skill."""
    return delete_skill(name)


@router.get("/api/skills/{name}")
async def read_skill_route(name: str) -> dict:
    """Read a skill's full content."""
    return read_skill(name)
