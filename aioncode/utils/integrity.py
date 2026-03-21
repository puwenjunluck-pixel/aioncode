"""File integrity utilities: MD5, fingerprints, CLAUDE.md marker merge."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from aioncode.utils.platform import open_utf8

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MARKER_START = "<!-- AIONCODE:START -->"
MARKER_END = "<!-- AIONCODE:END -->"
FINGERPRINT_PATTERN = re.compile(r"<!--\s*aion:fingerprint:([a-f0-9]{32})\s*-->")


# ---------------------------------------------------------------------------
# MD5 helpers
# ---------------------------------------------------------------------------

def md5_of_bytes(data: bytes) -> str:
    """Compute MD5 hex digest of raw bytes."""
    return hashlib.md5(data).hexdigest()


def md5_of_file(path: Path) -> str:
    """Compute MD5 hex digest of a file's content."""
    return md5_of_bytes(path.read_bytes())


def md5_of_text(text: str) -> str:
    """Compute MD5 hex digest of text (UTF-8 encoded)."""
    return md5_of_bytes(text.encode("utf-8"))


# ---------------------------------------------------------------------------
# Fingerprint operations (for Regenerable files)
# ---------------------------------------------------------------------------

def extract_fingerprint(path: Path) -> str | None:
    """Extract the aion fingerprint from a file, or None if not present."""
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    match = FINGERPRINT_PATTERN.search(content)
    return match.group(1) if match else None


def content_without_fingerprint(text: str) -> str:
    """Return text with the fingerprint comment line removed."""
    lines = text.splitlines(keepends=True)
    filtered = [line for line in lines if not FINGERPRINT_PATTERN.search(line)]
    return "".join(filtered).rstrip("\n") + "\n" if filtered else ""


def compute_fingerprint(text: str) -> str:
    """Compute the MD5 fingerprint of text, excluding any existing fingerprint line."""
    clean = content_without_fingerprint(text)
    return md5_of_text(clean)


def append_fingerprint(text: str) -> str:
    """Append (or update) a fingerprint comment to text."""
    clean = content_without_fingerprint(text)
    fp = md5_of_text(clean)
    return f"{clean}\n<!-- aion:fingerprint:{fp} -->\n"


# ---------------------------------------------------------------------------
# Template comparison (for init/upgrade anti-reverse-sync)
# ---------------------------------------------------------------------------

class TemplateComparison:
    """Result of comparing a template file with its installed counterpart."""

    __slots__ = ("template_path", "target_path", "status", "template_md5", "target_md5")

    def __init__(
        self,
        template_path: Path,
        target_path: Path,
        status: str,
        template_md5: str,
        target_md5: str | None,
    ) -> None:
        self.template_path = template_path
        self.target_path = target_path
        self.status = status  # "match" | "modified" | "missing" | "new"
        self.template_md5 = template_md5
        self.target_md5 = target_md5


def compare_template(template_path: Path, target_path: Path) -> TemplateComparison:
    """Compare a template file with its installed target.

    Returns a TemplateComparison with status:
    - "new": target doesn't exist, safe to create
    - "match": target matches template MD5, safe to overwrite
    - "modified": target was modified by user, needs confirmation
    """
    tmpl_md5 = md5_of_file(template_path)

    if not target_path.exists():
        return TemplateComparison(template_path, target_path, "new", tmpl_md5, None)

    target_md5 = md5_of_file(target_path)
    if tmpl_md5 == target_md5:
        return TemplateComparison(template_path, target_path, "match", tmpl_md5, target_md5)

    return TemplateComparison(template_path, target_path, "modified", tmpl_md5, target_md5)


# ---------------------------------------------------------------------------
# CLAUDE.md marker merge (ported from install.sh L346-384)
# ---------------------------------------------------------------------------

class MergeResult:
    """Result of a CLAUDE.md merge operation."""

    __slots__ = ("action", "content")

    def __init__(self, action: str, content: str) -> None:
        self.action = action  # "created" | "merged" | "appended"
        self.content = content


def merge_claude_md(existing: str | None, template: str) -> MergeResult:
    """Merge template content into CLAUDE.md, preserving user content.

    Three scenarios (matching install.sh behavior):
    1. File exists with markers → replace content between markers
    2. File exists without markers → append with markers
    3. File doesn't exist (existing is None) → create with markers

    Args:
        existing: Current CLAUDE.md content, or None if file doesn't exist.
        template: New template content to insert between markers.

    Returns:
        MergeResult with the action taken and the final content.
    """
    wrapped = f"{MARKER_START}\n{template}\n{MARKER_END}"

    if existing is None:
        return MergeResult("created", wrapped + "\n")

    if MARKER_START in existing:
        # Has markers → replace content between markers
        before_marker = existing.split(MARKER_START)[0]
        after_parts = existing.split(MARKER_END)
        after_marker = after_parts[-1] if len(after_parts) > 1 else ""

        content = f"{before_marker}{wrapped}{after_marker}"
        return MergeResult("merged", content)

    # No markers → append
    content = f"{existing}\n\n{wrapped}\n"
    return MergeResult("appended", content)


def strip_claude_md_markers(content: str) -> tuple[str, str]:
    """Remove AionCode marker section from CLAUDE.md content.

    Used by uninstall. Returns (cleaned_content, action).
    Action is one of: "stripped", "removed_entirely", "no_markers".
    """
    if MARKER_START not in content:
        return content, "no_markers"

    before = content.split(MARKER_START)[0]
    after_parts = content.split(MARKER_END)
    after = after_parts[-1] if len(after_parts) > 1 else ""

    cleaned = (before + after).strip()

    if not cleaned:
        return "", "removed_entirely"

    return cleaned + "\n", "stripped"
