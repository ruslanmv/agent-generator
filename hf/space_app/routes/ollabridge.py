"""OllaBridge device-pairing for the demo Space.

The production backend (backend/app/api/ollabridge.py) persists the
pairing token in a project-scoped secret vault. The Space has no
database, no auth, and no multi-project model, so this module keeps
the paired token in a process-local store guarded by a re-entrant
lock.

The token survives until the Space restarts. Visitors who want a
durable pairing should self-host the production backend or use the
CLI's `OLLABRIDGE_TOKEN` env var directly.

Endpoints:

* POST /api/ollabridge/pair    exchange a pairing code for a token
* GET  /api/ollabridge/status  is the demo paired? against which URL?
* POST /api/ollabridge/unpair  forget the token
* GET  /api/ollabridge/models  list models the token can reach
"""

from __future__ import annotations

import threading
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..config import SpaceSettings, get_settings

router = APIRouter(prefix="/api/ollabridge", tags=["ollabridge"])


# ── Session store ───────────────────────────────────────────────────


class _PairingSession:
    """Process-local pairing state. Demo only — not multi-tenant."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._token: str | None = None
        self._server_url: str | None = None

    def set(self, *, token: str, server_url: str) -> None:
        with self._lock:
            self._token = token
            self._server_url = server_url.rstrip("/")

    def clear(self) -> None:
        with self._lock:
            self._token = None
            self._server_url = None

    @property
    def token(self) -> str | None:
        with self._lock:
            return self._token

    @property
    def server_url(self) -> str | None:
        with self._lock:
            return self._server_url

    @property
    def paired(self) -> bool:
        return self.token is not None


_session = _PairingSession()


def get_pairing_session() -> _PairingSession:
    """FastAPI dependency."""
    return _session


# ── Schemas ─────────────────────────────────────────────────────────


class PairIn(BaseModel):
    code: str = Field(..., min_length=4, max_length=16)
    server_url: str | None = None


class PairOut(BaseModel):
    paired: bool
    server_url: str


class StatusOut(BaseModel):
    paired: bool
    server_url: str | None = None


class ModelsOut(BaseModel):
    models: list[str]


# ── Helpers ─────────────────────────────────────────────────────────


def _resolve_server_url(settings: SpaceSettings, override: str | None) -> str:
    if override:
        return override.rstrip("/")
    if settings.ollabridge_url:
        return settings.ollabridge_url.rstrip("/")
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="OllaBridge server URL not configured.",
    )


# ── Routes ──────────────────────────────────────────────────────────


@router.post("/pair", response_model=PairOut)
async def pair(
    body: PairIn,
    settings: Annotated[SpaceSettings, Depends(get_settings)],
    session: Annotated[_PairingSession, Depends(get_pairing_session)],
) -> PairOut:
    base = _resolve_server_url(settings, body.server_url)

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            r = await client.post(f"{base}/device/pair-simple", json={"code": body.code})
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to reach OllaBridge: {exc}",
            ) from exc

    if r.status_code == 404 or (r.status_code == 400 and "expired" in r.text.lower()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pairing code expired or unknown — re-pair on the device.",
        )
    if r.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OllaBridge returned HTTP {r.status_code}",
        )

    payload = r.json()
    token = payload.get("token") or payload.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="OllaBridge response missing token.",
        )

    session.set(token=token, server_url=base)
    return PairOut(paired=True, server_url=base)


@router.get("/status", response_model=StatusOut)
async def pairing_status(
    session: Annotated[_PairingSession, Depends(get_pairing_session)],
) -> StatusOut:
    return StatusOut(paired=session.paired, server_url=session.server_url)


@router.post("/unpair", response_model=StatusOut)
async def unpair(
    session: Annotated[_PairingSession, Depends(get_pairing_session)],
) -> StatusOut:
    session.clear()
    return StatusOut(paired=False, server_url=None)


@router.get("/models", response_model=ModelsOut)
async def list_models(
    settings: Annotated[SpaceSettings, Depends(get_settings)],
    session: Annotated[_PairingSession, Depends(get_pairing_session)],
) -> ModelsOut:
    base = session.server_url or settings.ollabridge_url.rstrip("/")
    headers: dict[str, str] = {}
    token = session.token or settings.ollabridge_token
    if token:
        headers["Authorization"] = f"Bearer {token}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            r = await client.get(f"{base}/v1/models", headers=headers)
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to reach OllaBridge: {exc}",
            ) from exc
    if r.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OllaBridge /v1/models returned HTTP {r.status_code}",
        )
    return ModelsOut(models=[m.get("id", "") for m in r.json().get("data", []) if m.get("id")])
