from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from agent_generator.web.inference import get_inference_client

BASE_DIR = Path(__file__).resolve().parent


def create_app() -> FastAPI:
    app = FastAPI(title="Agent Generator", version="0.1.3")
    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

    from agent_generator.web.routes.api import router as api_router
    from agent_generator.web.routes.pages import router as pages_router

    app.include_router(pages_router)
    app.include_router(api_router, prefix="/api")

    @app.get("/health")
    def health():
        inference = get_inference_client()
        return {
            "status": "ok",
            "version": "0.1.3",
            "inference_available": inference.available,
        }

    return app
