"""aioncode dashboard — Start the AionCode web UI."""

from __future__ import annotations

import argparse


def run_dashboard(args: argparse.Namespace) -> None:
    """CLI entry point for `aioncode dashboard`."""
    from aioncode.internal.dashboard import main as dashboard_main

    port = getattr(args, "port", 19200)
    host = getattr(args, "host", "")
    dashboard_main(port=port, host=host)
