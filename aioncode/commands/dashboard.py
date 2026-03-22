"""aioncode dashboard — Start the AionCode web UI (copilot mode)."""

from __future__ import annotations

import argparse
import signal
import sys


def run_dashboard(args: argparse.Namespace) -> None:
    """CLI entry point for `aioncode dashboard`.

    Uses dual-process architecture:
    - Main process: stays responsive for CLI interaction (Ctrl+C)
    - Child process: runs uvicorn web server
    """
    import multiprocessing

    # Required for PyInstaller frozen executables on Windows
    if getattr(sys, "frozen", False):
        multiprocessing.freeze_support()

    port = getattr(args, "port", 19200)
    host = getattr(args, "host", "")
    dev = getattr(args, "dev", False)

    def _run_server() -> None:
        """Child process: run uvicorn."""
        import uvicorn

        from aioncode.internal.dashboard import create_app

        app = create_app(dev=dev)
        uvicorn.run(
            app,
            host=host or "0.0.0.0",
            port=port,
            workers=1,
            loop="asyncio",
            log_level="warning",
        )

    proc = multiprocessing.Process(target=_run_server, daemon=True)
    proc.start()

    # Main process: print info and wait
    url = f"http://{host if host else 'localhost'}:{port}"
    mode = "dev" if dev else "production"
    print(f"\n  AionCode Dashboard ({mode})")
    print("  ─────────────────────────")
    print(f"  URL:  {url}")
    if dev:
        print(f"  Docs: {url}/api/docs")
    print("\n  Press Ctrl+C to stop.\n")

    # Graceful shutdown on Ctrl+C
    def _shutdown(signum, frame):  # noqa: ARG001
        print("\n  Shutting down...")
        proc.terminate()
        proc.join(timeout=5)
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    try:
        proc.join()
    except KeyboardInterrupt:
        _shutdown(None, None)
