"""Runs API.

REST:
- ``POST /api/projects/{pid}/runs``       → create run, kick off engine
- ``GET  /api/runs/{run_id}``             → run header + status
- ``GET  /api/runs/{run_id}/events``      → replay events from seq=after

WebSocket:
- ``GET  /ws/runs/{run_id}``              → live event stream

The WS protocol is JSON-lines: each frame is
``{"seq": N, "kind": "...", "payload": {...}, "created_at": "..."}``.
On connect the server first replays missed events (driven by an
``?after=N`` query param) then keeps the connection open until the run
terminates or the client disconnects.
"""

from __future__ import annotations

import asyncio
from typing import Annotated, Any

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.project import Project
from app.db.models.run import Run, RunEvent
from app.db.models.user import User
from app.db.session import get_session, get_sessionmaker
from app.runs.bus import hub
from app.runs.engine import start_run
from app.security.deps import get_current_user
from app.security.jwt import TokenError, decode_token

router = APIRouter(tags=["runs"])


class RunStartIn(BaseModel):
    prompt: str | None = None


class RunOut(BaseModel):
    id: str
    project_id: str
    owner_id: str
    status: str
    prompt: str | None
    error: str | None
    created_at: str
    updated_at: str

    @classmethod
    def from_orm_run(cls, r: Run) -> "RunOut":
        return cls(
            id=r.id,
            project_id=r.project_id,
            owner_id=r.owner_id,
            status=r.status,
            prompt=r.prompt,
            error=r.error,
            created_at=r.created_at.isoformat(),
            updated_at=r.updated_at.isoformat(),
        )


class EventOut(BaseModel):
    seq: int
    kind: str
    payload: dict[str, Any]
    created_at: str


def _can_read_project(p: Project, user: User) -> bool:
    return p.owner_id == user.id or p.visibility == "public" or user.role == "admin"


def _can_run_project(p: Project, user: User) -> bool:
    return p.owner_id == user.id or user.role == "admin"


@router.post(
    "/api/projects/{project_id}/runs",
    response_model=RunOut,
    status_code=status.HTTP_201_CREATED,
)
async def start(
    project_id: str,
    body: RunStartIn,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> RunOut:
    p = await session.get(Project, project_id)
    if p is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="project not found")
    if not _can_run_project(p, user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")

    run = Run(
        project_id=project_id,
        owner_id=user.id,
        status="pending",
        prompt=body.prompt,
    )
    session.add(run)
    await session.flush()
    run_id = run.id

    # Commit before scheduling so the background task sees the row.
    await session.commit()

    start_run(run_id)

    out = await session.get(Run, run_id)
    assert out is not None
    return RunOut.from_orm_run(out)


@router.get("/api/runs/{run_id}", response_model=RunOut)
async def get_run(
    run_id: str,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> RunOut:
    r = await session.get(Run, run_id)
    if r is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="run not found")
    p = await session.get(Project, r.project_id)
    if p is None or not _can_read_project(p, user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    return RunOut.from_orm_run(r)


@router.get("/api/runs/{run_id}/events", response_model=list[EventOut])
async def list_events(
    run_id: str,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    after: Annotated[int, Query(ge=-1, description="Return events with seq > after.")] = -1,
    limit: Annotated[int, Query(ge=1, le=1000)] = 500,
) -> list[EventOut]:
    r = await session.get(Run, run_id)
    if r is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="run not found")
    p = await session.get(Project, r.project_id)
    if p is None or not _can_read_project(p, user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")

    stmt = (
        select(RunEvent)
        .where(RunEvent.run_id == run_id, RunEvent.seq > after)
        .order_by(RunEvent.seq)
        .limit(limit)
    )
    events = (await session.execute(stmt)).scalars().all()
    return [
        EventOut(seq=e.seq, kind=e.kind, payload=e.payload, created_at=e.created_at)
        for e in events
    ]


async def _ws_authorize(
    ws: WebSocket, run_id: str
) -> tuple[User, Project] | None:
    """Authorize the WebSocket using a Bearer token in the query string.

    Browsers can't set the Authorization header on a WS handshake, so
    we accept either ``?token=...`` (frontend pattern) or the
    ``ag_session`` cookie (same-origin web shell).
    """
    token = ws.query_params.get("token") or ws.cookies.get("ag_session")
    if not token:
        await ws.close(code=4401)
        return None
    try:
        payload = decode_token(token, expected_typ="access")
    except TokenError:
        await ws.close(code=4401)
        return None

    Session = get_sessionmaker()  # noqa: N806
    async with Session() as session:
        user = await session.get(User, payload["sub"])
        if user is None:
            await ws.close(code=4401)
            return None
        r = await session.get(Run, run_id)
        if r is None:
            await ws.close(code=4404)
            return None
        project = await session.get(Project, r.project_id)
        if project is None or not _can_read_project(project, user):
            await ws.close(code=4403)
            return None
        return user, project


@router.websocket("/ws/runs/{run_id}")
async def stream_run(ws: WebSocket, run_id: str) -> None:
    await ws.accept()
    auth = await _ws_authorize(ws, run_id)
    if auth is None:
        return
    after_str = ws.query_params.get("after")
    after = int(after_str) if after_str is not None else -1

    Session = get_sessionmaker()  # noqa: N806

    # Replay missed events before joining the live feed.
    async with Session() as session:
        stmt = (
            select(RunEvent)
            .where(RunEvent.run_id == run_id, RunEvent.seq > after)
            .order_by(RunEvent.seq)
        )
        for ev in (await session.execute(stmt)).scalars().all():
            await ws.send_json(
                {
                    "seq": ev.seq,
                    "kind": ev.kind,
                    "payload": ev.payload,
                    "created_at": ev.created_at,
                }
            )
            after = max(after, ev.seq)

    async with hub.subscribe(run_id) as queue:
        try:
            while True:
                # Either the next live event arrives, or the client
                # disconnects. We race the queue against a receive_text
                # so disconnects are noticed promptly.
                recv_task = asyncio.create_task(ws.receive_text())
                pop_task = asyncio.create_task(queue.get())
                done, pending = await asyncio.wait(
                    {recv_task, pop_task}, return_when=asyncio.FIRST_COMPLETED
                )
                for t in pending:
                    t.cancel()
                if recv_task in done:
                    # The frontend doesn't send anything back; if it does
                    # we just drop the message and keep streaming.
                    try:
                        recv_task.result()
                    except WebSocketDisconnect:
                        return
                else:
                    event = pop_task.result()
                    if event["seq"] <= after:
                        continue
                    await ws.send_json(event)
                    after = event["seq"]
        except WebSocketDisconnect:
            return
