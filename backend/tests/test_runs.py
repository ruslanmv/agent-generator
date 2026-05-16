"""Run start / events / WebSocket streaming."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from tests.conftest import auth_headers


async def _wait_for_terminal(client: Any, run_id: str, token: str) -> str:
    """Poll until the run is no longer pending/running. Test-only."""
    for _ in range(40):
        r = await client.get(f"/api/runs/{run_id}", headers=auth_headers(token))
        status = r.json()["status"]
        if status not in ("pending", "running"):
            return status
        await asyncio.sleep(0.05)
    raise AssertionError(f"run {run_id} did not terminate")


@pytest.mark.asyncio
async def test_start_run_emits_events(client: Any, make_user: Any) -> None:
    _, token = await make_user()
    p = await client.post(
        "/api/projects",
        json={"name": "x", "framework": "crewai"},
        headers=auth_headers(token),
    )
    pid = p.json()["id"]

    r = await client.post(
        f"/api/projects/{pid}/runs",
        json={"prompt": "hello"},
        headers=auth_headers(token),
    )
    assert r.status_code == 201
    run_id = r.json()["id"]

    final = await _wait_for_terminal(client, run_id, token)
    assert final == "succeeded"

    events = await client.get(
        f"/api/runs/{run_id}/events", headers=auth_headers(token)
    )
    assert events.status_code == 200
    kinds = [e["kind"] for e in events.json()]
    assert "status" in kinds
    assert "result" in kinds
    # Replay by `after` filter works.
    after = await client.get(
        f"/api/runs/{run_id}/events?after=1", headers=auth_headers(token)
    )
    assert all(e["seq"] > 1 for e in after.json())


@pytest.mark.asyncio
async def test_start_run_forbidden_for_other_user(
    client: Any, make_user: Any
) -> None:
    _, alice = await make_user("alice")
    _, bob = await make_user("bob")
    p = await client.post(
        "/api/projects",
        json={"name": "x", "framework": "crewai"},
        headers=auth_headers(alice),
    )
    pid = p.json()["id"]

    r = await client.post(
        f"/api/projects/{pid}/runs",
        json={},
        headers=auth_headers(bob),
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_get_run_404(client: Any, make_user: Any) -> None:
    _, token = await make_user()
    r = await client.get("/api/runs/missing", headers=auth_headers(token))
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_ws_streaming_with_token() -> None:
    """Use Starlette's TestClient for the WS handshake."""
    from fastapi.testclient import TestClient

    from app.db.models.user import User
    from app.db.session import get_sessionmaker, init_models
    from app.main import app
    from app.security.jwt import issue_token

    await init_models()
    Session = get_sessionmaker()
    async with Session() as session:
        user = User(
            provider="github",
            provider_user_id="ws",
            username="ws",
            email=None,
            avatar_url=None,
            role="user",
        )
        session.add(user)
        await session.commit()
        uid = user.id
    token = issue_token(subject=uid, role="user", typ="access")

    with TestClient(app) as tc:
        h = {"Authorization": f"Bearer {token}"}
        project = tc.post(
            "/api/projects",
            json={"name": "ws", "framework": "crewai"},
            headers=h,
        ).json()
        run = tc.post(
            f"/api/projects/{project['id']}/runs",
            json={"prompt": "ws-test"},
            headers=h,
        ).json()

        # Wait until the run terminates so the WS just replays from
        # the DB without needing live events. Keeps the test
        # deterministic.
        for _ in range(40):
            status = tc.get(f"/api/runs/{run['id']}", headers=h).json()["status"]
            if status in ("succeeded", "failed", "cancelled"):
                break
            await asyncio.sleep(0.05)

        with tc.websocket_connect(f"/ws/runs/{run['id']}?token={token}") as ws:
            kinds: list[str] = []
            while True:
                event = ws.receive_json()
                kinds.append(event["kind"])
                if event["kind"] == "status" and event["payload"].get("status") == "succeeded":
                    break
        assert "result" in kinds


@pytest.mark.asyncio
async def test_ws_rejects_missing_token() -> None:
    from fastapi.testclient import TestClient
    from starlette.websockets import WebSocketDisconnect

    from app.db.session import init_models
    from app.main import app

    await init_models()
    with TestClient(app) as tc:
        with pytest.raises(WebSocketDisconnect) as excinfo:
            with tc.websocket_connect("/ws/runs/nope") as ws:
                ws.receive_json()
        assert excinfo.value.code == 4401
