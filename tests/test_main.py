"""Tests for aioncode CLI entry point."""

from __future__ import annotations

import pytest

from aioncode.main import _build_parser, main


class TestBuildParser:
    def test_returns_parser(self):
        parser = _build_parser()
        assert parser is not None
        assert parser.prog == "aioncode"

    def test_has_all_subcommands(self):
        parser = _build_parser()
        # Parse each subcommand to verify registration
        for cmd in ["install", "init", "upgrade", "uninstall", "doctor", "version", "dashboard", "clean"]:
            args = parser.parse_args([cmd])
            assert args.command == cmd

    def test_init_default_target(self):
        parser = _build_parser()
        args = parser.parse_args(["init"])
        assert args.target == "."

    def test_init_custom_target(self):
        parser = _build_parser()
        args = parser.parse_args(["init", "/tmp/my-project"])
        assert args.target == "/tmp/my-project"

    def test_dashboard_default_port(self):
        parser = _build_parser()
        args = parser.parse_args(["dashboard"])
        assert args.port == 19200

    def test_dashboard_custom_port(self):
        parser = _build_parser()
        args = parser.parse_args(["dashboard", "--port", "8080"])
        assert args.port == 8080

    def test_clean_dry_run(self):
        parser = _build_parser()
        args = parser.parse_args(["clean", "--dry-run"])
        assert args.dry_run is True


class TestMain:
    def test_no_args_shows_help(self):
        with pytest.raises(SystemExit) as exc_info:
            main([])
        assert exc_info.value.code == 0

    def test_help_flag(self):
        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        assert exc_info.value.code == 0

    def test_version_flag(self, capsys):
        from aioncode import __version__

        with pytest.raises(SystemExit) as exc_info:
            main(["--version"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "aioncode" in captured.out
        assert __version__ in captured.out
