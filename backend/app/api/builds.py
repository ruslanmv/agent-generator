"""Docker build trigger.

The frontend's Docker wizard (Configure → Env/Secrets → Build → Publish
→ Published) calls ``POST /api/builds/docker`` with a project id and
build options; the backend renders the Dockerfile + .dockerignore from
the project's files, then invokes ``docker buildx`` on the host daemon
(when ``AG_DOCKER_BUILD=local``) or returns a stub build record.

For prod we hand the build off to a Kaniko / BuildKit pod or to the
hosted ``backend-image.yml`` workflow on the GitHub side; the
endpoint stays the same so the SPA doesn't need to know which backend
runs the build.
"""

from __future__ import annotations

import asyncio
import os
from typing import Annotated, Literal

import structlog
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.project import Project
from app.db.models.user import User
from app.db.session import get_session
from app.db.models.user import User as UserOrm
from app.db.session import get_sessionmaker
from app.runs.bus import hub
from app.security.deps import get_current_user
from app.security.jwt import TokenError, decode_token

router = APIRouter(prefix="/api/builds", tags=["builds"])
ws_router = APIRouter(tags=["builds"])
log = structlog.get_logger("builds")

BuildMode = Literal["local", "remote", "stub"]


class DockerBuildIn(BaseModel):
    project_id: str
    image: str = Field(..., min_length=1, max_length=256)
    push: bool = False
    platforms: list[str] = Field(default_factory=lambda: ["linux/amd64"])


class DockerBuildOut(BaseModel):
    build_id: str
    mode: BuildMode
    image: str
    status: str
    stream_url: str


def _mode() -> BuildMode:
    raw = os.getenv("AG_DOCKER_BUILD", "stub").lower()
    if raw in ("local", "remote", "stub"):
        return raw  # type: ignore[return-value]
    return "stub"


async def _emit(build_id: str, kind: str, payload: dict) -> None:
    from datetime import datetime, timezone

    event = {
        "seq": payload.pop("seq", 0),
        "kind": kind,
        "payload": payload,
        "created_at": datetime.now(tz=timezone.utc).isoformat(),
    }
    await hub.publish(f"build:{build_id}", event)


async def _stub_build(build_id: str, image: str) -> None:
    seq = 0
    for line in (
        f"[stub] building {image}",
        "[stub] copying project files",
        "[stub] uv sync",
        "[stub] uv build",
        "[stub] image cached",
    ):
        await asyncio.sleep(0.05)
        await _emit(build_id, "log", {"seq": seq, "line": line})
        seq += 1
    await _emit(build_id, "status", {"seq": seq, "status": "succeeded"})


async def _local_build(build_id: str, image: str, project: Project, push: bool) -> None:
    """Invoke `docker buildx` on the host daemon.

    Streams stdout lines onto the bus as `log` events; emits a final
    `status` event with the exit code. Only used in dev; prod uses the
    GitHub workflow and the ``remote`` mode.
    """
    import json
    import shutil
    import tempfile
    from pathlib import Path

    docker = shutil.which("docker")
    if docker is None:
        await _emit(
            build_id,
            "error",
            {"seq": 0, "message": "docker CLI not on PATH"},
        )
        return

    with tempfile.TemporaryDirectory(prefix="ag-build-") as tmp:
        ctx = Path(tmp)
        # Render the project's files into the build context.
        for f in project.files:
            target = ctx / f.path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(f.content)
        # Drop a project descriptor so generated Dockerfiles can read
        # framework / hyperscaler / pattern at build time.
        (ctx / ".agent-generator.json").write_text(
            json.dumps(
                {
                    "framework": project.framework,
                    "hyperscaler": project.hyperscaler,
                    "pattern": project.pattern,
                    "model": project.model,
                },
                indent=2,
            )
        )
        cmd = [
            docker, "buildx", "build",
            "--tag", image,
            "--progress", "plain",
            *(["--push"] if push else ["--load"]),
            str(ctx),
        ]
        log.info("build.local.start", cmd=cmd, build_id=build_id)
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        seq = 0
        assert proc.stdout is not None
        async for raw in proc.stdout:
            await _emit(
                build_id,
                "log",
                {"seq": seq, "line": raw.decode(errors="replace").rstrip()},
            )
            seq += 1
        rc = await proc.wait()
        await _emit(
            build_id,
            "status",
            {"seq": seq, "status": "succeeded" if rc == 0 else "failed", "exit_code": rc},
        )


@router.post(
    "/docker", response_model=DockerBuildOut, status_code=status.HTTP_201_CREATED
)
async def start_docker_build(
    body: DockerBuildIn,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> DockerBuildOut:
    project = await session.get(Project, body.project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="project not found"
        )
    if project.owner_id != user.id and user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="forbidden"
        )

    from uuid import uuid4

    build_id = str(uuid4())
    mode = _mode()
    if mode == "local":
        asyncio.create_task(
            _local_build(build_id, body.image, project, body.push),
            name=f"build:{build_id}",
        )
    elif mode == "remote":
        # Real implementation enqueues a job on the BuildKit pod / fires
        # a `workflow_dispatch` against backend-image.yml. Stubbed here
        # to keep this batch self-contained.
        asyncio.create_task(
            _stub_build(build_id, body.image), name=f"build:{build_id}"
        )
    else:
        asyncio.create_task(
            _stub_build(build_id, body.image), name=f"build:{build_id}"
        )
    return DockerBuildOut(
        build_id=build_id,
        mode=mode,
        image=body.image,
        status="started",
        stream_url=f"/ws/builds/{build_id}",
    )


async def _ws_authorize_build(ws: WebSocket) -> UserOrm | None:
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
        user = await session.get(UserOrm, payload["sub"])
        if user is None:
            await ws.close(code=4401)
            return None
        return user


@ws_router.websocket("/ws/builds/{build_id}")
async def stream_build(ws: WebSocket, build_id: str) -> None:
    """Live build log feed.

    We don't persist build events to the DB today (builds are short-
    lived and the runner emits one event per docker stdout line); the
    WS just forwards the in-process bus. The Docker wizard subscribes
    immediately after POST /api/builds/docker returns, so missed
    events at the start are minimised.
    """
    await ws.accept()
    user = await _ws_authorize_build(ws)
    if user is None:
        return
    async with hub.subscribe(f"build:{build_id}") as queue:
        try:
            while True:
                recv_task = asyncio.create_task(ws.receive_text())
                pop_task = asyncio.create_task(queue.get())
                done, pending = await asyncio.wait(
                    {recv_task, pop_task},
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for t in pending:
                    t.cancel()
                if recv_task in done:
                    try:
                        recv_task.result()
                    except WebSocketDisconnect:
                        return
                else:
                    await ws.send_json(pop_task.result())
        except WebSocketDisconnect:
            return
