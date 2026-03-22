"""FastAPI application factory for AionCode Dashboard."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from aioncode.internal.dashboard.config import DASHBOARD_VERSION


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan — load projects on startup."""
    from aioncode.internal.dashboard.services.project_registry import load_projects

    app.state.projects = load_projects()
    yield


def create_app(*, dev: bool = False) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        dev: If True, serve frontend from static files instead of embedded.
    """
    app = FastAPI(
        title="AionCode Dashboard",
        version=DASHBOARD_VERSION,
        docs_url="/api/docs" if dev else None,
        redoc_url=None,
        lifespan=_lifespan,
    )

    app.state.dev_mode = dev

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers (will be added in Plan Step 6)
    _register_routers(app)

    # Dev mode: serve static files from filesystem
    if dev:
        from pathlib import Path

        from starlette.staticfiles import StaticFiles

        static_dir = Path(__file__).parent / "frontend" / "static"
        if static_dir.is_dir():
            app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # Frontend routes
    @app.get("/", response_class=HTMLResponse)
    async def index() -> HTMLResponse:
        if app.state.dev_mode:
            from aioncode.internal.dashboard.frontend import load_static_html

            return HTMLResponse(load_static_html("index.html"))
        from aioncode.internal.dashboard.frontend.embedded import EMBEDDED_HTML

        return HTMLResponse(EMBEDDED_HTML)

    return app


def _register_routers(app: FastAPI) -> None:
    """Register all API routers."""
    from aioncode.internal.dashboard.routers import (
        browse,
        bugs,
        commands,
        files,
        logs,
        monitor,
        projects,
        team,
    )

    app.include_router(projects.router)
    app.include_router(files.router)
    app.include_router(monitor.router)
    app.include_router(bugs.router)
    app.include_router(team.router)
    app.include_router(commands.router)
    app.include_router(browse.router)
    app.include_router(logs.router)
