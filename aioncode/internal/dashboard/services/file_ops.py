"""File tree and CRUD operations within .aion/ directory."""

from __future__ import annotations

from pathlib import Path


def _validate_aion_path(project_path: str, relative_path: str) -> Path | None:
    """Validate that a file path stays within .aion/.

    Returns resolved Path if valid, None if path traversal detected.
    """
    aion_dir = Path(project_path) / ".aion"
    target = (aion_dir / relative_path).resolve()
    try:
        target.relative_to(aion_dir.resolve())
    except ValueError:
        return None
    return target


def get_file_tree(project_path: str) -> dict:
    """Build a JSON file tree of the .aion/ directory."""
    aion_dir = Path(project_path) / ".aion"
    if not aion_dir.is_dir():
        return {"ok": False, "message": "No .aion/ directory"}

    def _build(dirpath: Path, prefix: str = "") -> list[dict]:
        items: list[dict] = []
        try:
            entries = sorted(dirpath.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except PermissionError:
            return items

        for entry in entries:
            if entry.name.startswith("."):
                continue
            rel = f"{prefix}{entry.name}" if not prefix else f"{prefix}/{entry.name}"
            if entry.is_dir():
                items.append(
                    {
                        "name": entry.name,
                        "path": rel,
                        "type": "dir",
                        "children": _build(entry, rel),
                    }
                )
            else:
                try:
                    stat = entry.stat()
                    items.append(
                        {
                            "name": entry.name,
                            "path": rel,
                            "type": "file",
                            "size": stat.st_size,
                            "mtime": stat.st_mtime,
                        }
                    )
                except OSError:
                    pass
        return items

    return {"ok": True, "tree": _build(aion_dir)}


def read_file(project_path: str, relative_path: str) -> dict:
    """Read a file from .aion/."""
    target = _validate_aion_path(project_path, relative_path)
    if target is None:
        return {"ok": False, "message": "Invalid path"}
    if not target.is_file():
        return {"ok": False, "message": "File not found"}
    try:
        content = target.read_text(encoding="utf-8")
        return {"ok": True, "content": content, "path": relative_path}
    except OSError as e:
        return {"ok": False, "message": str(e)}


def write_file(project_path: str, relative_path: str, content: str) -> dict:
    """Write/update a file in .aion/."""
    target = _validate_aion_path(project_path, relative_path)
    if target is None:
        return {"ok": False, "message": "Invalid path"}
    if not target.exists():
        return {"ok": False, "message": "File not found (use create_file for new files)"}
    try:
        target.write_text(content, encoding="utf-8")
        return {"ok": True, "message": f"Updated: {relative_path}"}
    except OSError as e:
        return {"ok": False, "message": str(e)}


def create_file(project_path: str, relative_path: str, content: str = "") -> dict:
    """Create a new file in .aion/."""
    target = _validate_aion_path(project_path, relative_path)
    if target is None:
        return {"ok": False, "message": "Invalid path"}
    if target.exists():
        return {"ok": False, "message": "File already exists"}
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return {"ok": True, "message": f"Created: {relative_path}"}
    except OSError as e:
        return {"ok": False, "message": str(e)}


def delete_file(project_path: str, relative_path: str) -> dict:
    """Delete a file from .aion/."""
    target = _validate_aion_path(project_path, relative_path)
    if target is None:
        return {"ok": False, "message": "Invalid path"}
    if not target.is_file():
        return {"ok": False, "message": "File not found"}
    try:
        target.unlink()
        return {"ok": True, "message": f"Deleted: {relative_path}"}
    except OSError as e:
        return {"ok": False, "message": str(e)}
