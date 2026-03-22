"""API routes for file operations within .aion/."""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from aioncode.internal.dashboard.services.encoding import decode_project_path
from aioncode.internal.dashboard.services.file_ops import (
    create_file,
    delete_file,
    get_file_tree,
    read_file,
    write_file,
)

router = APIRouter(tags=["files"])


class FileWriteRequest(BaseModel):
    path: str
    content: str


@router.get("/api/projects/{encoded}/files")
async def file_tree(encoded: str) -> dict:
    """Get .aion/ file tree."""
    project_path = decode_project_path(encoded)
    return get_file_tree(project_path)


@router.get("/api/projects/{encoded}/file")
async def read_file_route(encoded: str, path: str = Query(...)) -> dict:
    """Read a file from .aion/."""
    project_path = decode_project_path(encoded)
    return read_file(project_path, path)


@router.put("/api/projects/{encoded}/file")
async def write_file_route(encoded: str, body: FileWriteRequest) -> dict:
    """Update a file in .aion/."""
    project_path = decode_project_path(encoded)
    return write_file(project_path, body.path, body.content)


@router.post("/api/projects/{encoded}/file")
async def create_file_route(encoded: str, body: FileWriteRequest) -> dict:
    """Create a new file in .aion/."""
    project_path = decode_project_path(encoded)
    return create_file(project_path, body.path, body.content)


@router.delete("/api/projects/{encoded}/file")
async def delete_file_route(encoded: str, path: str = Query(...)) -> dict:
    """Delete a file from .aion/."""
    project_path = decode_project_path(encoded)
    return delete_file(project_path, path)
