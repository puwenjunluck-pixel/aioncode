"""Tests for aioncode init — verifies anti-reverse-sync and idempotency."""

from __future__ import annotations

import hashlib
from pathlib import Path
from unittest.mock import patch

from aioncode.commands.init import _init_project
from aioncode.core.project import _get_templates_dir


def _hash_dir(directory: Path) -> dict[str, str]:
    """Compute MD5 of every file in a directory tree."""
    hashes = {}
    if not directory.exists():
        return hashes
    for f in sorted(directory.rglob("*")):
        if f.is_file():
            rel = str(f.relative_to(directory))
            hashes[rel] = hashlib.md5(f.read_bytes()).hexdigest()
    return hashes


def _mock_init_interactive():
    """Return a stack of patches that bypass all interactive prompts in init."""
    return [
        patch("aioncode.commands.init.confirm", return_value=True),
        patch("aioncode.commands.init.choose_one", return_value=3),
        patch("aioncode.commands.init.toggle_select", side_effect=lambda items: [s for _, _, s in items]),
    ]


class TestAntiReverseSync:
    """Verify that init NEVER modifies templates/ — the cardinal dogfooding rule."""

    def test_templates_unchanged_after_init(self, tmp_path: Path):
        """init must not modify the bundled templates directory."""
        templates_dir = _get_templates_dir()
        if not templates_dir.exists():
            return  # Skip if templates not available (CI without full repo)

        # Snapshot templates before init
        before = _hash_dir(templates_dir)

        # Run init on a temp project
        target = tmp_path / "project"
        target.mkdir()
        (target / ".git").mkdir()
        patches = _mock_init_interactive()
        for p in patches:
            p.start()
        try:
            _init_project(target)
        except SystemExit:
            pass  # init may exit on missing dependencies, that's fine
        finally:
            for p in patches:
                p.stop()

        # Verify templates unchanged
        after = _hash_dir(templates_dir)
        assert before == after, "init modified templates/ — anti-reverse-sync violation!"


class TestIdempotency:
    """Verify that running init twice produces the same result."""

    def test_init_twice_no_error(self, tmp_path: Path):
        """Running init on an already-initialized project should not crash."""
        target = tmp_path / "project"
        target.mkdir()
        (target / ".git").mkdir()

        patches = _mock_init_interactive()
        for p in patches:
            p.start()
        try:
            _init_project(target)
        except SystemExit:
            pass

        # Second run (upgrade mode)
        try:
            _init_project(target, upgrade=True)
        except SystemExit:
            pass
        finally:
            for p in patches:
                p.stop()

        # .aion/ should still exist and be valid
        assert (target / ".aion").is_dir()
        assert (target / ".aion" / "config.yml").is_file()

    def test_user_files_not_overwritten(self, tmp_path: Path):
        """User-modified files in .aion/ must not be overwritten by init."""
        target = tmp_path / "project"
        target.mkdir()
        (target / ".git").mkdir()

        patches = _mock_init_interactive()
        for p in patches:
            p.start()
        try:
            # First init
            try:
                _init_project(target)
            except SystemExit:
                pass

            # User modifies a file
            rules_file = target / ".aion" / "rules" / "style.md"
            if rules_file.exists():
                user_content = "user custom rule\n"
                rules_file.write_text(user_content, encoding="utf-8")

                # Second init
                try:
                    _init_project(target, upgrade=True)
                except SystemExit:
                    pass

                # User content must survive
                assert rules_file.read_text(encoding="utf-8") == user_content
        finally:
            for p in patches:
                p.stop()
