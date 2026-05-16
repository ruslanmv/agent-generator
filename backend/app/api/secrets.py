"""Secrets API.

Project-scoped. Owners and admins can read/write secrets on their
projects; nobody else can. The value never round-trips through this
service except in ``PUT`` requests — ``GET /secrets`` only returns keys
and metadata, so a leaked SPA token doesn't dump the vault.

Routes:
- ``GET    /api/projects/{pid}/secrets``         → list keys (no values)
- ``PUT    /api/projects/{pid}/secrets/{key}``   → write value
- ``GET    /api/projects/{pid}/secrets/{key}``   → read value
- ``DELETE /api/projects/{pid}/secrets/{key}``   → drop the entry
"""

from __future__ import annotations

import re
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.project import Project
from app.db.models.user import User
from app.db.session import get_session
from app.secrets import get_secrets_backend
from app.secrets.base import SecretRecord
from app.security.deps import get_current_user

router = APIRouter(prefix="/api/projects/{project_id}/secrets", tags=["secrets"])

# Tight charset — keys flow into Vault paths + .env files + Helm values
# so we keep them shell-safe.
_KEY_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,127}$")


class SecretIn(BaseModel):
    value: str


class SecretOut(BaseModel):
    key: str
    version: int

    @classmethod
    def from_record(cls, r: SecretRecord) -> SecretOut:
        return cls(key=r.key, version=r.version)


class SecretValueOut(BaseModel):
    key: str
    value: str


async def _load_or_404_writable(
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


def _validate_key(key: str) -> None:
    if not _KEY_RE.match(key):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "key must match ^[A-Za-z][A-Za-z0-9_]{0,127}$ "
                "(letters, digits, underscore; starts with a letter)"
            ),
        )


@router.get("", response_model=list[SecretOut])
async def list_secrets(
    project_id: str,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[SecretOut]:
    await _load_or_404_writable(project_id, user, session)
    records = await get_secrets_backend().list(project_id)
    return [SecretOut.from_record(r) for r in records]


@router.put(
    "/{key}",
    response_model=SecretOut,
    status_code=status.HTTP_200_OK,
)
async def put_secret(
    project_id: str,
    key: Annotated[str, Path(min_length=1, max_length=128)],
    body: SecretIn,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SecretOut:
    _validate_key(key)
    await _load_or_404_writable(project_id, user, session)
    record = await get_secrets_backend().put(project_id, key, body.value)
    return SecretOut.from_record(record)


@router.get("/{key}", response_model=SecretValueOut)
async def get_secret(
    project_id: str,
    key: str,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SecretValueOut:
    _validate_key(key)
    await _load_or_404_writable(project_id, user, session)
    value = await get_secrets_backend().get(project_id, key)
    if value is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="secret not found"
        )
    return SecretValueOut(key=key, value=value)


@router.delete(
    "/{key}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_secret(
    project_id: str,
    key: str,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Response:
    _validate_key(key)
    await _load_or_404_writable(project_id, user, session)
    removed = await get_secrets_backend().delete(project_id, key)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="secret not found"
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
