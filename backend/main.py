# backend/main.py

from __future__ import annotations
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .config import settings
from .logging_conf import setup_logging
from .agents import PlanRequest, PlanResponse, plan
from .agents.builder_manager import BuilderManager

# ────────────────────────────────────────────────────────────────────────────
# Configure logging
# ────────────────────────────────────────────────────────────────────────────
setup_logging()
logger = logging.getLogger("backend")

# ────────────────────────────────────────────────────────────────────────────
# FastAPI application setup
# ────────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="BeeAI Multi‑Agent Backend",
    version="1.0.0",
    description="Orchestrator and builder API for Agent Generator",
)

# Allow CORS if needed by local dev (adjust origins as appropriate)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

builder_mgr = BuilderManager()

# ────────────────────────────────────────────────────────────────────────────
# Planning endpoint
# ────────────────────────────────────────────────────────────────────────────
@app.post("/plan", response_model=PlanResponse, summary="Generate build plan")
async def api_plan(req: PlanRequest) -> PlanResponse:
    """
    1) Call the LLM planning agent to decide reuse vs scaffold.
    2) Return a PlanResponse with selected_framework, project_tree, build_tasks.
    """
    try:
        return await plan(req)
    except Exception as e:
        logger.exception("Planning failed")
        raise HTTPException(status_code=500, detail=str(e)) from e

# ────────────────────────────────────────────────────────────────────────────
# Build endpoint
# ────────────────────────────────────────────────────────────────────────────
@app.post("/build", summary="Execute build tasks")
async def api_build(req: PlanResponse) -> dict[str, Any]:
    """
    1) Fan out each build task to its builder.
    2) Merge the resulting files.
    3) Return status and final tree summary.
    """
    try:
        result = await builder_mgr.build(req.dict())
        return {"status": "ok", "summary": result}
    except Exception as e:
        logger.exception("Build failed")
        raise HTTPException(status_code=500, detail=str(e)) from e

# ────────────────────────────────────────────────────────────────────────────
# Run the app with Uvicorn
# ────────────────────────────────────────────────────────────────────────────
def run() -> None:
    """Entry point for `python -m backend.main`."""
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        log_level="info",
        access_log=False,
        reload=False,
    )


if __name__ == "__main__":
    run()
