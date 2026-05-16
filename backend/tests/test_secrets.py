"""Secrets API + memory backend.

We exercise the in-memory backend through the HTTP surface so the test
covers both the access-control plumbing and the encryption round-trip.
"""

from __future__ import annotations

from typing import Any

import pytest

from tests.conftest import auth_headers


@pytest.fixture(autouse=True)
def _reset_secrets_backend() -> None:
    from app.secrets.factory import get_secrets_backend

    get_secrets_backend.cache_clear()


async def _make_project(client: Any, token: str) -> str:
    p = await client.post(
        "/api/projects",
        json={"name": "p", "framework": "crewai"},
        headers=auth_headers(token),
    )
    return p.json()["id"]


@pytest.mark.asyncio
async def test_put_then_get(client: Any, make_user: Any) -> None:
    _, token = await make_user()
    pid = await _make_project(client, token)

    r = await client.put(
        f"/api/projects/{pid}/secrets/OPENAI_API_KEY",
        json={"value": "sk-test-12345"},
        headers=auth_headers(token),
    )
    assert r.status_code == 200
    assert r.json()["key"] == "OPENAI_API_KEY"

    r2 = await client.get(
        f"/api/projects/{pid}/secrets/OPENAI_API_KEY",
        headers=auth_headers(token),
    )
    assert r2.status_code == 200
    assert r2.json()["value"] == "sk-test-12345"


@pytest.mark.asyncio
async def test_list_returns_keys_not_values(client: Any, make_user: Any) -> None:
    _, token = await make_user()
    pid = await _make_project(client, token)

    for k, v in [("ONE", "1"), ("TWO", "2")]:
        await client.put(
            f"/api/projects/{pid}/secrets/{k}",
            json={"value": v},
            headers=auth_headers(token),
        )

    r = await client.get(
        f"/api/projects/{pid}/secrets", headers=auth_headers(token)
    )
    assert r.status_code == 200
    keys = sorted(s["key"] for s in r.json())
    assert keys == ["ONE", "TWO"]
    # `value` is not part of the list response shape.
    assert all("value" not in s for s in r.json())


@pytest.mark.asyncio
async def test_delete_removes_secret(client: Any, make_user: Any) -> None:
    _, token = await make_user()
    pid = await _make_project(client, token)

    await client.put(
        f"/api/projects/{pid}/secrets/X",
        json={"value": "v"},
        headers=auth_headers(token),
    )
    r = await client.delete(
        f"/api/projects/{pid}/secrets/X", headers=auth_headers(token)
    )
    assert r.status_code == 204

    r2 = await client.get(
        f"/api/projects/{pid}/secrets/X", headers=auth_headers(token)
    )
    assert r2.status_code == 404


@pytest.mark.asyncio
async def test_validates_key_charset(client: Any, make_user: Any) -> None:
    _, token = await make_user()
    pid = await _make_project(client, token)

    r = await client.put(
        f"/api/projects/{pid}/secrets/bad-key",
        json={"value": "v"},
        headers=auth_headers(token),
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_forbidden_for_other_owner(client: Any, make_user: Any) -> None:
    _, alice = await make_user("alice")
    _, bob = await make_user("bob")
    pid = await _make_project(client, alice)

    r = await client.put(
        f"/api/projects/{pid}/secrets/K",
        json={"value": "v"},
        headers=auth_headers(bob),
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_secrets_scoped_per_project(client: Any, make_user: Any) -> None:
    _, token = await make_user()
    p1 = await _make_project(client, token)
    p2 = await _make_project(client, token)

    await client.put(
        f"/api/projects/{p1}/secrets/K",
        json={"value": "in-p1"},
        headers=auth_headers(token),
    )
    # Same key on p2 returns 404 — projects share no secret store.
    r = await client.get(
        f"/api/projects/{p2}/secrets/K", headers=auth_headers(token)
    )
    assert r.status_code == 404
