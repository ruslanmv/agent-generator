"""FastAPI application factory.

``create_app`` wires settings, logging, CORS, and routers. Uvicorn /
the prod ASGI server import ``app.main:app`` (a module-level instance
constructed via ``create_app``).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api import (
    audit,
    auth,
    builds,
    compatibility,
    health,
    marketplace,
    ollabridge,
    projects,
    runs,
    secrets,
)
from app.db.session import init_models
from app.logging import configure_logging
from app.middleware.audit import AuditMiddleware
from app.settings import get_settings
from app.telemetry import setup_telemetry

_DEFAULT_JWT_SECRET = "change-me-or-the-app-will-yell-at-you"  # noqa: S105


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(level=settings.log_level, json=settings.env == "prod")
    log = structlog.get_logger("app")

    if settings.env != "dev" and settings.jwt_secret == _DEFAULT_JWT_SECRET:
        log.warning("security.default_jwt_secret_in_use", env=settings.env)

    if settings.env == "dev":
        # Create tables on first boot so a fresh checkout works without
        # running Alembic. Prod uses migrations.
        await init_models()

    log.info(
        "service.start",
        service=settings.service_name,
        version=__version__,
        env=settings.env,
        github_oauth=bool(settings.github_client_id),
    )
    yield
    log.info("service.stop", service=settings.service_name)


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.service_name,
        version=__version__,
        summary=(
            "FastAPI service that powers the Agent Generator wizard, "
            "Marketplace, Runs, and Docker builds across the web, "
            "desktop (Tauri) and mobile (Capacitor) shells."
        ),
        lifespan=lifespan,
    )

    app.add_middleware(AuditMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    setup_telemetry(app, settings)

    app.include_router(health.router)
    app.include_router(compatibility.router)
    app.include_router(auth.router)
    app.include_router(projects.router)
    app.include_router(runs.router)
    app.include_router(marketplace.router)
    app.include_router(builds.router)
    app.include_router(builds.ws_router)
    app.include_router(secrets.router)
    app.include_router(ollabridge.router)
    app.include_router(audit.router)

    return app


app = create_app()
