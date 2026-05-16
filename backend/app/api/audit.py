"""Audit log viewer (admin-only)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.audit import AuditEvent
from app.db.models.user import User
from app.db.session import get_session
from app.security.deps import require_admin

router = APIRouter(prefix="/api/admin/audit", tags=["audit"])


class AuditOut(BaseModel):
    id: str
    actor_id: str | None
    actor_username: str | None
    method: str
    path: str
    status_code: int
    request_id: str | None
    ip: str | None
    user_agent: str | None
    created_at: str

    @classmethod
    def from_orm_event(cls, e: AuditEvent) -> AuditOut:
        return cls(
            id=e.id,
            actor_id=e.actor_id,
            actor_username=e.actor_username,
            method=e.method,
            path=e.path,
            status_code=e.status_code,
            request_id=e.request_id,
            ip=e.ip,
            user_agent=e.user_agent,
            created_at=e.created_at.isoformat(),
        )


@router.get("", response_model=list[AuditOut])
async def list_audit_events(
    _: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    method: Annotated[str | None, Query()] = None,
    path: Annotated[str | None, Query(description="Substring match on path.")] = None,
) -> list[AuditOut]:
    stmt = select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(limit)
    if method:
        stmt = stmt.where(AuditEvent.method == method.upper())
    if path:
        stmt = stmt.where(AuditEvent.path.contains(path))
    rows = (await session.execute(stmt)).scalars().all()
    return [AuditOut.from_orm_event(r) for r in rows]
