"""Marketplace proxy: fixture mode + cache + publish path."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_list_returns_fixture_without_hub(client: Any) -> None:
    r = await client.get("/api/marketplace/agents")
    assert r.status_code == 200
    ids = [a["id"] for a in r.json()]
    assert "research-assistant" in ids


@pytest.mark.asyncio
async def test_list_filters_by_framework(client: Any) -> None:
    r = await client.get("/api/marketplace/agents?framework=react")
    assert r.status_code == 200
    assert {a["framework"] for a in r.json()} == {"react"}


@pytest.mark.asyncio
async def test_list_search(client: Any) -> None:
    r = await client.get("/api/marketplace/agents?q=research")
    assert r.status_code == 200
    assert all("research" in a["name"].lower() or "research" in a["description"].lower()
               for a in r.json())


@pytest.mark.asyncio
async def test_get_agent_404(client: Any) -> None:
    r = await client.get("/api/marketplace/agents/missing")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_publish_requires_auth(client: Any) -> None:
    r = await client.post(
        "/api/marketplace/publish",
        json={"project_id": "x"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_publish_offline_returns_published_offline(
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
        "/api/marketplace/publish",
        json={"project_id": pid, "tags": ["demo"]},
        headers=auth_headers(token),
    )
    assert r.status_code == 201
    assert r.json()["status"] == "published-offline"


@pytest.mark.asyncio
async def test_publish_forbidden_for_other_user(
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
        "/api/marketplace/publish",
        json={"project_id": pid},
        headers=auth_headers(bob),
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_publish_against_hub(
    client: Any, make_user: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AG_MATRIX_HUB_URL", "https://hub.example.com")
    from app.settings import get_settings

    get_settings.cache_clear()

    _, token = await make_user()
    p = await client.post(
        "/api/projects",
        json={"name": "p", "framework": "crewai"},
        headers=auth_headers(token),
    )
    pid = p.json()["id"]

    class FakeResp:
        status_code = 201

        def json(self) -> dict:
            return {"id": "remote-id", "url": "https://hub.example.com/agents/remote-id"}

    fake_client = AsyncMock()
    fake_client.__aenter__.return_value = fake_client
    fake_client.__aexit__.return_value = None
    fake_client.post.return_value = FakeResp()

    with patch("app.api.marketplace.httpx.AsyncClient", return_value=fake_client):
        r = await client.post(
            "/api/marketplace/publish",
            json={"project_id": pid, "tags": ["demo"]},
            headers=auth_headers(token),
        )
    assert r.status_code == 201
    body = r.json()
    assert body["id"] == "remote-id"
    assert body["url"].endswith("/remote-id")
