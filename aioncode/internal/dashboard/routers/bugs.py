"""API routes for bug tracking."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from aioncode.internal.dashboard.services.bugs import get_bug_stats, list_bugs
from aioncode.internal.dashboard.services.encoding import decode_project_path

router = APIRouter(tags=["bugs"])


@router.get("/api/projects/{encoded}/bugs/stats")
async def bug_stats(encoded: str) -> dict:
    """Get bug statistics. Must be before /bugs to avoid path collision."""
    project_path = decode_project_path(encoded)
    return get_bug_stats(project_path)


@router.get("/api/projects/{encoded}/bugs")
async def list_bugs_route(
    encoded: str,
    status: Optional[str] = Query(None),  # noqa: UP045 — FastAPI evaluates at runtime, needs Optional for 3.9 compat
    assignee: Optional[str] = Query(None),  # noqa: UP045
    severity: Optional[str] = Query(None),  # noqa: UP045
    category: Optional[str] = Query(None),  # noqa: UP045
) -> dict:
    """List bugs with optional filters."""
    project_path = decode_project_path(encoded)
    filters = {}
    if status:
        filters["status"] = status
    if assignee:
        filters["assignee"] = assignee
    if severity:
        filters["severity"] = severity
    if category:
        filters["category"] = category
    bugs = list_bugs(project_path, filters or None)
    return {"ok": True, "bugs": bugs}
