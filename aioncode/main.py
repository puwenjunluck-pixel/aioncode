"""AionCode CLI — unified entry point."""

from __future__ import annotations

import argparse
import os
import sys


def _ensure_utf8() -> None:
    """Force UTF-8 encoding on all platforms."""
    os.environ.setdefault("PYTHONUTF8", "1")
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
            sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except (AttributeError, OSError):
            pass


def _build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser with subcommands."""
    from aioncode import __version__

    parser = argparse.ArgumentParser(
        prog="aioncode",
        description="AionCode — AI-powered development intelligence framework",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"aioncode {__version__}",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    sub = parser.add_subparsers(dest="command", metavar="<command>")

    # --- Admin commands ---
    sub.add_parser("install", help="Install aioncode to system PATH")
    sub.add_parser("upgrade", help="Upgrade to the latest version")
    sub.add_parser("uninstall", help="Remove aioncode from system")
    sub.add_parser("doctor", help="Run environment diagnostics")
    sub.add_parser("version", help="Show version and bootstrap status")

    # --- Project commands ---
    init_p = sub.add_parser("init", help="Initialize .aion/ in current directory")
    init_p.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Target project directory (default: current directory)",
    )

    dash_p = sub.add_parser("dashboard", help="Start the web UI")
    dash_p.add_argument("--port", type=int, default=19200, help="Server port (default: 19200)")
    dash_p.add_argument("--host", default="", help="Server host (default: 0.0.0.0)")
    dash_p.add_argument("--dev", action="store_true", help="Dev mode: load frontend from static files, enable API docs")

    clean_p = sub.add_parser("clean", help="Clean up temporary files in .aion/")
    clean_p.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be cleaned without deleting",
    )

    return parser


def main(argv: list[str] | None = None) -> None:
    """Main entry point."""
    _ensure_utf8()
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.no_color:
        os.environ["NO_COLOR"] = "1"

    if not args.command:
        parser.print_help()
        raise SystemExit(0)

    match args.command:
        case "init":
            from aioncode.commands.init import run_init

            run_init(args)
        case "install":
            from aioncode.commands.install import run_install

            run_install(args)
        case "uninstall":
            from aioncode.commands.uninstall import run_uninstall

            run_uninstall(args)
        case "upgrade":
            from aioncode.commands.upgrade import run_upgrade

            run_upgrade(args)
        case "dashboard":
            from aioncode.commands.dashboard import run_dashboard

            run_dashboard(args)
        case "doctor":
            from aioncode.commands.doctor import run_doctor

            run_doctor(args)
        case "version":
            from aioncode.commands.version import run_version

            run_version(args)
        case "clean":
            from aioncode.commands.clean import run_clean

            run_clean(args)
        case _:
            parser.print_help()
            raise SystemExit(1)
