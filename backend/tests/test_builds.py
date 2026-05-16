"""Docker build trigger.

The CI workflow handles signed image builds (Batch 20). This endpoint
is the wizard's in-app trigger; tests run against the stub backend so
the suite stays hermetic.
"""

from __future__ import annotations

from typing import Any

import pytest

from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_docker_build_requires_auth(client: Any) -> None:
    r = await client.post(
        "/api/builds/docker",
        json={"project_id": "x", "image": "y"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_docker_build_404_when_project_missing(
    client: Any, make_user: Any
) -> None:
    _, token = await make_user()
    r = await client.post(
        "/api/builds/docker",
        json={"project_id": "missing", "image": "ghcr.io/x:dev"},
        headers=auth_headers(token),
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_docker_build_forbidden_for_other_user(
    client: Any, make_user: Any
) -> None:
    _, alice = await make_user("alice")
    _, bob = await make_user("bob")
    p = await client.post(
        "/api/projects",
        json={"name": "p", "framework": "crewai"},
        headers=auth_headers(alice),
    )
    pid = p.json()["id"]
    r = await client.post(
        "/api/builds/docker",
        json={"project_id": pid, "image": "ghcr.io/x:dev"},
        headers=auth_headers(bob),
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_docker_build_stub_returns_handle(
    client: Any, make_user: Any
) -> None:
    _, token = await make_user()
    p = await client.post(
        "/api/projects",
        json={"name": "p", "framework": "crewai"},
        headers=auth_headers(token),
    )
    pid = p.json()["id"]
    r = await client.post(
        "/api/builds/docker",
        json={"project_id": pid, "image": "ghcr.io/x:dev"},
        headers=auth_headers(token),
    )
    assert r.status_code == 201
    body = r.json()
    assert body["mode"] == "stub"
    assert body["image"] == "ghcr.io/x:dev"
    assert body["stream_url"].startswith("/ws/builds/")
