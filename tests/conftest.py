"""Shared fixtures for AionCode tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from aioncode import __version__


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Create a minimal project directory with .aion/ structure."""
    aion_dir = tmp_path / ".aion"
    aion_dir.mkdir()
    (aion_dir / "config.yml").write_text(f'version: "{__version__}"\n', encoding="utf-8")
    (tmp_path / ".git").mkdir()
    return tmp_path


@pytest.fixture
def mock_aion_env(tmp_path: Path) -> Path:
    """Create a complete isolated AionCode environment in /tmp.

    Simulates the full installation structure so tests don't pollute
    the real .aion/ directory during dogfooding development.
    """
    project_dir = tmp_path / "test-project"
    project_dir.mkdir()

    # .git
    (project_dir / ".git").mkdir()

    # .aion/ scaffolding
    aion_dir = project_dir / ".aion"
    aion_dir.mkdir()
    (aion_dir / "config.yml").write_text(f'version: "{__version__}"\n', encoding="utf-8")

    for subdir in [
        "rules", "refs", "specs", "plans", "reviews", "contracts",
        "prototypes", "monitor", "tests", "bugs", "checklists", "hooks",
    ]:
        (aion_dir / subdir).mkdir(parents=True, exist_ok=True)

    # Empty rule files
    for rule_file in ["pitfalls.md", "style.md", "perf.md"]:
        (aion_dir / "rules" / rule_file).write_text(
            f"---\ncategory: {rule_file.replace('.md', '')}\nrule_count: 0\n---\n",
            encoding="utf-8",
        )

    # .claude/
    claude_dir = project_dir / ".claude"
    claude_dir.mkdir()
    (claude_dir / "commands").mkdir()
    (claude_dir / "CLAUDE.md").write_text(
        "<!-- AIONCODE:START -->\ntest content\n<!-- AIONCODE:END -->\n",
        encoding="utf-8",
    )

    return project_dir
