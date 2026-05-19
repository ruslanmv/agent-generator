"""FastAPI application for the Hugging Face Space.

Responsibilities:

* Mount the SPA bundle at `/` (everything else is `/api/*`).
* Wire up the demo-shaped backend routes.
* Apply enterprise-grade middleware: CORS, GZip, structured logging,
  and a "demo-mode" header that downstream caches and clients can use
  for cache differentiation.

The Space runs under uvicorn's default async loop. There is no
persistent storage; in-memory state is owned by the ProjectStore
created in `dependencies.py`.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import __version__
from .config import get_settings
from .routes import (
    build,
    compatibility,
    generate,
    health,
    huggingface,
    marketplace,
    ollabridge,
    plan,
    test_chat,
)

log = logging.getLogger("space_app")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    log.info(
        "space_app.start",
        extra={"version": __version__, "provider": settings.provider, "spa_dir": str(settings.spa_dir)},
    )
    yield
    log.info("space_app.stop")


app = FastAPI(
    title="Agent Generator · Live Demo",
    version=__version__,
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# ── Middleware ──────────────────────────────────────────────────────
# CORS is open because the Space serves the SPA from the same origin,
# but allowing requests from arbitrary origins lets the public API be
# explored from e.g. https://www.huggingface.co/spaces/... iframes
# without a CORS preflight failure.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    max_age=600,
)
app.add_middleware(GZipMiddleware, minimum_size=1024)


@app.middleware("http")
async def stamp_demo_header(request: Request, call_next):  # type: ignore[no-untyped-def]
    response = await call_next(request)
    response.headers["x-agent-generator-channel"] = "hf-space"
    response.headers["x-agent-generator-version"] = __version__
    return response


# ── Routes ──────────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(plan.router)
app.include_router(build.router)
app.include_router(generate.router)
app.include_router(compatibility.router)
app.include_router(marketplace.router)
app.include_router(ollabridge.router)
app.include_router(test_chat.router)
app.include_router(huggingface.router)


# ── SPA static mount ────────────────────────────────────────────────
SPA_DIR = get_settings().spa_dir
SPA_INDEX = SPA_DIR / "index.html"


if SPA_DIR.exists() and SPA_INDEX.exists():
    # Serve hashed assets directly so the browser can cache them
    # aggressively; the index.html and other routes fall through to
    # the SPA fallback below.
    app.mount(
        "/assets",
        StaticFiles(directory=str(SPA_DIR / "assets")),
        name="spa-assets",
    )

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str) -> FileResponse:
        """Serve `index.html` for any non-API route so the React Router
        client takes over (BrowserRouter)."""
        if full_path.startswith("api/"):
            # The /api router didn't match — let FastAPI's default 404 handler run.
            raise HTTPException(status_code=404, detail="not found")
        candidate = (SPA_DIR / full_path).resolve()
        # Reject path-traversal attempts; only serve real files inside the SPA dir.
        try:
            candidate.relative_to(SPA_DIR.resolve())
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="invalid path") from exc
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(SPA_INDEX)

else:
    log.warning(
        "space_app.spa_missing",
        extra={"spa_dir": str(SPA_DIR)},
    )

    @app.get("/", include_in_schema=False)
    async def spa_missing() -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content={
                "error": "spa-bundle-missing",
                "detail": (
                    "The SPA bundle was not present in the image. Build the "
                    "frontend with `AG_BUILD_CHANNEL=hf npm run build` and "
                    "copy the resulting `dist/` to /app/frontend_dist."
                ),
            },
        )


# Convenience CLI entrypoint: `python -m space_app.main`
if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run("space_app.main:app", host="0.0.0.0", port=7860)
