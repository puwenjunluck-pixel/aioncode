"""API routes for command file browsing."""

from __future__ import annotations

import re

from fastapi import APIRouter

from aioncode.internal.dashboard.config import COMMANDS_SRC

router = APIRouter(tags=["commands"])


@router.get("/api/commands")
async def list_commands() -> dict:
    """List available command files with title and description."""
    if not COMMANDS_SRC.is_dir():
        return {"ok": True, "commands": []}

    cmds = []
    for f in sorted(COMMANDS_SRC.glob("*.md")):
        content = f.read_text(encoding="utf-8")
        lines = content.splitlines()

        # Extract title from first # heading
        title = f.stem
        description = ""
        for line in lines[:10]:
            if line.startswith("# "):
                title = line[2:].strip()
                # Try to extract description from the line after title
                idx = lines.index(line)
                for next_line in lines[idx + 1 : idx + 5]:
                    stripped = next_line.strip()
                    if stripped and not stripped.startswith("#"):
                        description = stripped
                        break
                break

        cmds.append(
            {
                "name": f.stem,
                "title": title,
                "description": description,
                "file": f.name,
            }
        )

    return {"ok": True, "commands": cmds}


@router.get("/api/commands/{name}")
async def read_command(name: str) -> dict:
    """Read a command file's content."""
    # Sanitize: remove path separators and traversal
    safe_name = re.sub(r"[/\\.]", "", name)
    if not safe_name:
        return {"ok": False, "message": "Invalid command name"}

    # Try with and without .md extension
    for candidate in [safe_name, f"{safe_name}.md"]:
        filepath = COMMANDS_SRC / candidate
        if filepath.is_file():
            content = filepath.read_text(encoding="utf-8")
            return {"ok": True, "name": safe_name, "content": content}

    return {"ok": False, "message": f"Command not found: {name}"}
