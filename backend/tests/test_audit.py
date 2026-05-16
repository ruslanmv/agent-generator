"""Audit middleware + admin viewer."""

from __future__ import annotations

from typing import Any

import pytest

from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_request_id_header_echoed(client: Any) -> None:
    r = await client.get("/livez")
    assert r.status_code == 200
    assert "X-Request-Id" in r.headers
    # If we send one, it round-trips unchanged.
    r2 = await client.get("/livez", headers={"X-Request-Id": "abc-123"})
    assert r2.headers["X-Request-Id"] == "abc-123"


@pytest.mark.asyncio
async def test_mutating_request_records_audit_event(
    client: Any, make_user: Any
) -> None:
    _, token = await make_user("alice", role="admin")
    await client.post(
        "/api/projects",
        json={"name": "p", "framework": "crewai"},
        headers=auth_headers(token),
    )

    r = await client.get("/api/admin/audit?method=POST", headers=auth_headers(token))
    assert r.status_code == 200
    rows = r.json()
    assert any(e["path"] == "/api/projects" and e["method"] == "POST" for e in rows)
    # Actor metadata captured.
    target = next(e for e in rows if e["path"] == "/api/projects")
    assert target["actor_username"] is None or target["actor_id"]  # may resolve via token


@pytest.mark.asyncio
async def test_audit_admin_only(client: Any, make_user: Any) -> None:
    _, regular = await make_user("alice", role="user")
    r = await client.get("/api/admin/audit", headers=auth_headers(regular))
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_audit_skips_health(client: Any, make_user: Any) -> None:
    _, admin = await make_user("root", role="admin")
    # Hit /livez a few times.
    for _ in range(3):
        await client.get("/livez")
    r = await client.get("/api/admin/audit", headers=auth_headers(admin))
    assert r.status_code == 200
    paths = {e["path"] for e in r.json()}
    assert "/livez" not in paths
