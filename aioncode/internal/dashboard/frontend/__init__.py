"""Dashboard frontend — embedded HTML or static file serving."""

from __future__ import annotations

from pathlib import Path

_STATIC_DIR = Path(__file__).parent / "static"


def load_static_html(filename: str) -> str:
    """Load an HTML file from the static directory (dev mode)."""
    filepath = _STATIC_DIR / filename
    if not filepath.exists():
        return f"<html><body><h1>404: {filename} not found in static/</h1></body></html>"
    return filepath.read_text(encoding="utf-8")
