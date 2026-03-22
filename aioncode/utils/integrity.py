"""File integrity utilities: MD5, fingerprints, CLAUDE.md marker merge."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

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
# CLAUDE.md strict marker merge
# ---------------------------------------------------------------------------

# Regex: match <!-- AIONCODE:START -->...<!-- AIONCODE:END --> blocks (greedy per block)
_MARKER_BLOCK_RE = re.compile(
    r"\s*<!-- AIONCODE:START -->.*?<!-- AIONCODE:END -->\s*",
    re.DOTALL,
)
# Regex: match legacy <!-- AIONCODE:LEARNED --> sections (to next marker or EOF)
_LEARNED_BLOCK_RE = re.compile(
    r"\s*<!-- AIONCODE:LEARNED -->.*?(?=<!-- AIONCODE:|$)",
    re.DOTALL,
)

CLAUDE_MD_MAX_LINES = 100


class MergeResult:
    """Result of a CLAUDE.md merge operation."""

    __slots__ = ("action", "content", "warnings")

    def __init__(
        self, action: str, content: str, warnings: list[str] | None = None
    ) -> None:
        self.action = action  # "created" | "merged" | "appended"
        self.content = content
        self.warnings = warnings or []


def _extract_user_content(text: str) -> str:
    """Strip all AionCode-managed sections, return only user content."""
    cleaned = _MARKER_BLOCK_RE.sub("", text)
    cleaned = _LEARNED_BLOCK_RE.sub("", cleaned)
    return cleaned.strip()


def _check_size(content: str, warnings: list[str]) -> None:
    """Append a warning if content exceeds CLAUDE_MD_MAX_LINES."""
    line_count = content.count("\n") + 1
    if line_count > CLAUDE_MD_MAX_LINES:
        warnings.append(
            f"CLAUDE.md has {line_count} lines (limit: {CLAUDE_MD_MAX_LINES}). "
            "Consider moving content to .aion/ files."
        )


def merge_claude_md(existing: str | None, template: str) -> MergeResult:
    """Merge template into CLAUDE.md with strict alignment.

    Guarantees exactly one START/END marker pair. Strips any legacy
    LEARNED sections or duplicate marker blocks. Preserves user content
    (everything outside AionCode markers).

    Args:
        existing: Current CLAUDE.md content, or None if file doesn't exist.
        template: New template content to insert between markers.

    Returns:
        MergeResult with action, final content, and any warnings.
    """
    wrapped = f"{MARKER_START}\n{template}\n{MARKER_END}"
    warnings: list[str] = []

    if existing is None:
        content = wrapped + "\n"
        _check_size(content, warnings)
        return MergeResult("created", content, warnings)

    if MARKER_START not in existing:
        content = f"{wrapped}\n\n{existing}"
        _check_size(content, warnings)
        return MergeResult("appended", content, warnings)

    # Has markers → strip ALL managed sections, rebuild with one clean pair
    user_content = _extract_user_content(existing)
    content = f"{wrapped}\n\n{user_content}\n" if user_content else wrapped + "\n"

    _check_size(content, warnings)
    return MergeResult("merged", content, warnings)


def strip_claude_md_markers(content: str) -> tuple[str, str]:
    """Remove all AionCode sections from CLAUDE.md content.

    Used by uninstall. Returns (cleaned_content, action).
    Action is one of: "stripped", "removed_entirely", "no_markers".
    """
    if MARKER_START not in content:
        return content, "no_markers"

    cleaned = _extract_user_content(content)
    if not cleaned:
        return "", "removed_entirely"

    return cleaned + "\n", "stripped"
