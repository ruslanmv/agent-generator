"""OllaBridge device-pairing proxy.

The Providers settings screen shows a "Pairing Code" input; the user
types the code their phone shows in the OllaBridge app and the backend
calls the OllaBridge ``/device/pair-simple`` endpoint to exchange it
for a session token + server URL.

We do this server-side so the SPA never holds the OllaBridge admin
secret. The resulting (server_url, token) pair is stored in the
user's project-scoped secret store under the well-known keys
``OLLABRIDGE_URL`` and ``OLLABRIDGE_TOKEN``.

Endpoints:
- ``POST /api/ollabridge/pair``       → exchange code, persist secrets
- ``GET  /api/ollabridge/status``     → which providers are paired
- ``POST /api/ollabridge/unpair``     → drop the stored credentials
"""

from __future__ import annotations

from typing import Annotated

import httpx
import structlog
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.project import Project
from app.db.models.user import User
from app.db.session import get_session
from app.secrets import get_secrets_backend
from app.security.deps import get_current_user
from app.settings import Settings, get_settings

router = APIRouter(prefix="/api/ollabridge", tags=["ollabridge"])
log = structlog.get_logger("ollabridge")

SECRET_KEY_URL = "OLLABRIDGE_URL"
SECRET_KEY_TOKEN = "OLLABRIDGE_TOKEN"  # noqa: S105


class PairIn(BaseModel):
    project_id: str
    code: str = Field(..., min_length=4, max_length=16)
    server_url: str | None = Field(
        default=None,
        description="Override the default OllaBridge server URL.",
    )


class PairOut(BaseModel):
    project_id: str
    server_url: str
    paired: bool = True


class StatusOut(BaseModel):
    project_id: str
    paired: bool
    server_url: str | None


class UnpairIn(BaseModel):
    project_id: str


def _server_url(settings: Settings, override: str | None) -> str:
    if override:
        return override.rstrip("/")
    if settings.ollabridge_url:
        return str(settings.ollabridge_url).rstrip("/")
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="OllaBridge server URL not configured (set AG_OLLABRIDGE_URL).",
    )


async def _load_or_403(
    project_id: str, user: User, session: AsyncSession
) -> Project:
    project = await session.get(Project, project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="project not found"
        )
    if project.owner_id != user.id and user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="forbidden"
        )
    return project


@router.post("/pair", response_model=PairOut, status_code=status.HTTP_200_OK)
async def pair(
    body: PairIn,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> PairOut:
    await _load_or_403(body.project_id, user, session)
    base = _server_url(settings, body.server_url)

    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.post(
            f"{base}/device/pair-simple",
            json={"code": body.code},
        )
    if r.status_code == 404 or (r.status_code == 400 and "expired" in r.text.lower()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pairing code expired or unknown — re-pair on the device.",
        )
    if r.status_code >= 400:
        log.warning("ollabridge.pair_failed", status=r.status_code, body=r.text)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OllaBridge returned HTTP {r.status_code}",
        )

    payload = r.json()
    token = payload.get("token") or payload.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="OllaBridge response missing token",
        )

    backend = get_secrets_backend()
    await backend.put(body.project_id, SECRET_KEY_URL, base)
    await backend.put(body.project_id, SECRET_KEY_TOKEN, token)
    return PairOut(project_id=body.project_id, server_url=base)


@router.get("/status/{project_id}", response_model=StatusOut)
async def status_(
    project_id: str,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> StatusOut:
    await _load_or_403(project_id, user, session)
    backend = get_secrets_backend()
    url = await backend.get(project_id, SECRET_KEY_URL)
    return StatusOut(project_id=project_id, paired=bool(url), server_url=url)


@router.post(
    "/unpair",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def unpair(
    body: UnpairIn,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Response:
    await _load_or_403(body.project_id, user, session)
    backend = get_secrets_backend()
    await backend.delete(body.project_id, SECRET_KEY_URL)
    await backend.delete(body.project_id, SECRET_KEY_TOKEN)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
