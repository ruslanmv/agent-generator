"""POST /api/build — render files from a ProjectSpec."""

from __future__ import annotations

from typing import Any

from agent_generator.application.build_service import build_dict
from agent_generator.domain.project_spec import ProjectSpec
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, ValidationError

router = APIRouter(prefix="/api", tags=["build"])


class BuildRequest(BaseModel):
    spec: dict[str, Any] = Field(..., description="Validated ProjectSpec JSON.")
    mcp: bool = False


class BuildResponse(BaseModel):
    artifacts: dict[str, Any]


@router.post("/build", response_model=BuildResponse)
async def build_endpoint(body: BuildRequest) -> BuildResponse:
    try:
        spec = ProjectSpec.model_validate(body.spec)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.errors(),
        ) from exc

    bundle = build_dict(spec, mcp=body.mcp)
    return BuildResponse(artifacts=bundle)
