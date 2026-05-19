"""POST /api/generate — plan + build in a single call, with download.

Also exposes:

    GET  /api/projects          list of recently generated demos
    GET  /api/projects/{id}     individual project metadata
    GET  /api/projects/{id}/zip ZIP of the generated artifact bundle
"""

from __future__ import annotations

import io
import zipfile
from typing import Annotated, Any

from agent_generator.application.build_service import build_dict
from agent_generator.application.planning_service import plan as plan_spec
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..dependencies import (
    ProjectStore,
    SpaceSettings,
    get_project_store,
    get_settings,
)
from .ollabridge import _PairingSession, get_pairing_session
from .plan import _ollabridge_env

router = APIRouter(prefix="/api", tags=["generate"])


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000)
    framework: str | None = None
    artifact_mode: str | None = None
    provider: str | None = None
    mcp: bool = False
    use_llm: bool = False


class GenerateResponse(BaseModel):
    id: str
    spec: dict[str, Any]
    artifacts: dict[str, Any]
    warnings: list[str]


class ProjectSummary(BaseModel):
    id: str
    prompt: str
    framework: str
    file_count: int


@router.post("/generate", response_model=GenerateResponse)
async def generate_endpoint(
    body: GenerateRequest,
    settings: Annotated[SpaceSettings, Depends(get_settings)],
    store: Annotated[ProjectStore, Depends(get_project_store)],
    session: Annotated[_PairingSession, Depends(get_pairing_session)],
) -> GenerateResponse:
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

    bundle = build_dict(spec, mcp=body.mcp)

    project_id = store.add(
        {
            "prompt": body.prompt,
            "spec": spec.model_dump(mode="json"),
            "artifacts": bundle,
            "warnings": warnings,
        }
    )

    return GenerateResponse(
        id=project_id,
        spec=spec.model_dump(mode="json"),
        artifacts=bundle,
        warnings=warnings,
    )


@router.get("/projects", response_model=list[ProjectSummary])
async def list_projects(
    store: Annotated[ProjectStore, Depends(get_project_store)],
) -> list[ProjectSummary]:
    out: list[ProjectSummary] = []
    for proj in store.list():
        spec = proj.get("spec", {})
        files = proj.get("artifacts", {}).get("files") or {}
        out.append(
            ProjectSummary(
                id=proj["id"],
                prompt=proj.get("prompt", ""),
                framework=spec.get("framework", "unknown"),
                file_count=len(files),
            )
        )
    return out


@router.get("/projects/{project_id}")
async def get_project(
    project_id: str,
    store: Annotated[ProjectStore, Depends(get_project_store)],
) -> dict[str, Any]:
    proj = store.get(project_id)
    if proj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="project not found (demo store is volatile)",
        )
    return proj


@router.get("/projects/{project_id}/zip")
async def download_project_zip(
    project_id: str,
    store: Annotated[ProjectStore, Depends(get_project_store)],
) -> StreamingResponse:
    proj = store.get(project_id)
    if proj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="project not found (demo store is volatile)",
        )
    files: dict[str, str] = proj.get("artifacts", {}).get("files") or {}
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path, contents in files.items():
            zf.writestr(path, contents)
    buf.seek(0)
    filename = f"agent-generator-{project_id[:8]}.zip"
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"content-disposition": f'attachment; filename="{filename}"'},
    )
