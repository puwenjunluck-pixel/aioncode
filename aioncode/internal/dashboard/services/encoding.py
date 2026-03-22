"""Path encoding utilities for URL-safe project identifiers."""

from __future__ import annotations

import base64


def encode_project_path(path: str) -> str:
    """Encode a project path as URL-safe base64."""
    return base64.urlsafe_b64encode(path.encode("utf-8")).decode("ascii")


def decode_project_path(encoded: str) -> str:
    """Decode a URL-safe base64 project path.

    Handles missing padding characters.
    """
    # Fix padding
    padding = 4 - len(encoded) % 4
    if padding != 4:
        encoded += "=" * padding
    return base64.urlsafe_b64decode(encoded.encode("ascii")).decode("utf-8")
