"""POST /api/plan — turn a prompt into a ProjectSpec.

Thin wrapper around `agent_generator.application.planning_service.plan`.
The Space defaults to keyword-only planning (no LLM call) so it works
with no secrets configured.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Annotated, Any, Iterator

from agent_generator.application.planning_service import plan as plan_spec
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..dependencies import SpaceSettings, get_settings
from .ollabridge import _PairingSession, get_pairing_session


@contextmanager
def _ollabridge_env(
    settings: SpaceSettings, session: _PairingSession
) -> Iterator[None]:
    """Make the OllaBridge URL / token visible to agent_generator's
    config so the published planning service picks them up. Restores
    the previous env on exit so concurrent requests don't leak."""
    server_url = session.server_url or settings.ollabridge_url
    token = session.token or settings.ollabridge_token
    saved = {
        key: os.environ.get(key)
        for key in ("OLLABRIDGE_URL", "OLLABRIDGE_MODEL", "OLLABRIDGE_TOKEN")
    }
    os.environ["OLLABRIDGE_URL"] = server_url
    os.environ["OLLABRIDGE_MODEL"] = settings.ollabridge_model
    if token:
        os.environ["OLLABRIDGE_TOKEN"] = token
    else:
        os.environ.pop("OLLABRIDGE_TOKEN", None)
    try:
        yield
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

router = APIRouter(prefix="/api", tags=["plan"])


class PlanRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000)
    framework: str | None = None
    artifact_mode: str | None = None
    provider: str | None = None
    mcp: bool = False
    use_llm: bool = False


class PlanResponse(BaseModel):
    spec: dict[str, Any]
    warnings: list[str]


@router.post("/plan", response_model=PlanResponse)
async def plan_endpoint(
    body: PlanRequest,
    settings: Annotated[SpaceSettings, Depends(get_settings)],
    session: Annotated[_PairingSession, Depends(get_pairing_session)],
) -> PlanResponse:
    # LLM planning runs by default on the OllaBridge free tier. Set
    # AG_DEMO_PROVIDER=keyword to disable; pick a different provider
    # to override per-call.
    provider = body.provider or (None if settings.provider == "keyword" else settings.provider)
    use_llm = body.use_llm if body.use_llm else (settings.provider != "keyword")

    try:
        with _ollabridge_env(settings, session):
            spec, warnings = plan_spec(
                prompt=body.prompt,
                framework=body.framework,
                artifact_mode=body.artifact_mode,
                provider=provider,
                mcp=body.mcp,
                use_llm=use_llm,
            )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return PlanResponse(spec=spec.model_dump(mode="json"), warnings=warnings)
