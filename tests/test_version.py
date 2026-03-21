"""Tests for version consistency — the release integrity iron rule."""

from __future__ import annotations

import re
from pathlib import Path

from aioncode import __version__


class TestVersionFormat:
    def test_is_valid_semver(self):
        """Version must be valid semver format."""
        pattern = r"^\d+\.\d+\.\d+$"
        assert re.match(pattern, __version__), f"Invalid version format: {__version__}"

    def test_not_empty(self):
        assert __version__
        assert len(__version__) > 0


class TestVersionConsistency:
    def test_matches_pyproject(self):
        """__init__.py version must match pyproject.toml version."""
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        content = pyproject_path.read_text(encoding="utf-8")
        match = re.search(r'^version\s*=\s*"(.+?)"', content, re.MULTILINE)
        assert match, "Could not find version in pyproject.toml"
        pyproject_version = match.group(1)
        assert __version__ == pyproject_version, (
            f"Version mismatch: __init__.py={__version__}, pyproject.toml={pyproject_version}"
        )
