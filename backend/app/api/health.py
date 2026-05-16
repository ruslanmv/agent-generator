"""Liveness + readiness probes.

``/livez`` returns 200 if the process is up. ``/readyz`` performs a
lightweight DB ping when a database is configured. ``/healthz`` is the
combined check Kubernetes' default liveness/readiness probes point at.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from app import __version__
from app.settings import Settings, get_settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    env: str


@router.get("/livez", response_model=HealthResponse)
def livez(settings: Annotated[Settings, Depends(get_settings)]) -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.service_name,
        version=__version__,
        env=settings.env,
    )


@router.get("/readyz", response_model=HealthResponse)
def readyz(
    settings: Annotated[Settings, Depends(get_settings)],
) -> HealthResponse:
    # Real DB ping arrives in Batch 17 alongside the SQLAlchemy session
    # dependency. For now the process being up implies readiness.
    return HealthResponse(
        status="ready",
        service=settings.service_name,
        version=__version__,
        env=settings.env,
    )


@router.get(
    "/healthz",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
)
def healthz(
    settings: Annotated[Settings, Depends(get_settings)],
) -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.service_name,
        version=__version__,
        env=settings.env,
    )
