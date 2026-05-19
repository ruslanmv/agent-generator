"""Liveness probe.

Exposed at both `/health` (used by the Docker HEALTHCHECK in the image)
and `/api/health` (the SPA's probe).
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from .. import __version__

router = APIRouter(tags=["health"])


class Health(BaseModel):
    status: str
    version: str
    channel: str


@router.get("/health", response_model=Health)
@router.get("/api/health", response_model=Health)
async def health() -> Health:
    return Health(status="ok", version=__version__, channel="hf-space")
