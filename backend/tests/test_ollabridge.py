"""OllaBridge pairing proxy."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

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


def _fake_resp(status_code: int, body: dict | str) -> Any:
    resp = AsyncMock()
    resp.status_code = status_code
    resp.json = lambda: body if isinstance(body, dict) else {}
    resp.text = body if isinstance(body, str) else ""
    return resp


def _fake_client(post_resp: Any) -> AsyncMock:
    client = AsyncMock()
    client.__aenter__.return_value = client
    client.__aexit__.return_value = None
    client.post.return_value = post_resp
    return client


@pytest.mark.asyncio
async def test_pair_persists_secrets(
    client: Any, make_user: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AG_OLLABRIDGE_URL", "https://ollabridge.example.com")
    from app.settings import get_settings

    get_settings.cache_clear()

    _, token = await make_user()
    pid = await _make_project(client, token)

    fake = _fake_client(_fake_resp(200, {"token": "abc-token"}))
    with patch("app.api.ollabridge.httpx.AsyncClient", return_value=fake):
        r = await client.post(
            "/api/ollabridge/pair",
            json={"project_id": pid, "code": "GKEV-8985"},
            headers=auth_headers(token),
        )
    assert r.status_code == 200
    assert r.json()["paired"] is True

    # The secrets backend now has the URL + token.
    status = await client.get(
        f"/api/ollabridge/status/{pid}", headers=auth_headers(token)
    )
    assert status.status_code == 200
    body = status.json()
    assert body["paired"] is True
    assert body["server_url"].startswith("https://ollabridge.example.com")


@pytest.mark.asyncio
async def test_pair_expired_code_returns_400(
    client: Any, make_user: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AG_OLLABRIDGE_URL", "https://ollabridge.example.com")
    from app.settings import get_settings

    get_settings.cache_clear()

    _, token = await make_user()
    pid = await _make_project(client, token)

    fake = _fake_client(_fake_resp(400, "Pairing code expired"))
    with patch("app.api.ollabridge.httpx.AsyncClient", return_value=fake):
        r = await client.post(
            "/api/ollabridge/pair",
            json={"project_id": pid, "code": "GKEV-8985"},
            headers=auth_headers(token),
        )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_pair_without_server_url_returns_503(
    client: Any, make_user: Any
) -> None:
    _, token = await make_user()
    pid = await _make_project(client, token)
    r = await client.post(
        "/api/ollabridge/pair",
        json={"project_id": pid, "code": "GKEV-8985"},
        headers=auth_headers(token),
    )
    assert r.status_code == 503


@pytest.mark.asyncio
async def test_unpair_removes_secrets(
    client: Any, make_user: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AG_OLLABRIDGE_URL", "https://ollabridge.example.com")
    from app.settings import get_settings

    get_settings.cache_clear()

    _, token = await make_user()
    pid = await _make_project(client, token)

    fake = _fake_client(_fake_resp(200, {"token": "abc-token"}))
    with patch("app.api.ollabridge.httpx.AsyncClient", return_value=fake):
        await client.post(
            "/api/ollabridge/pair",
            json={"project_id": pid, "code": "GKEV-8985"},
            headers=auth_headers(token),
        )

    r = await client.post(
        "/api/ollabridge/unpair",
        json={"project_id": pid},
        headers=auth_headers(token),
    )
    assert r.status_code == 204

    status = await client.get(
        f"/api/ollabridge/status/{pid}", headers=auth_headers(token)
    )
    assert status.json()["paired"] is False


@pytest.mark.asyncio
async def test_pair_forbidden_for_other_user(
    client: Any, make_user: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AG_OLLABRIDGE_URL", "https://ollabridge.example.com")
    from app.settings import get_settings

    get_settings.cache_clear()

    _, alice = await make_user("alice")
    _, bob = await make_user("bob")
    pid = await _make_project(client, alice)

    r = await client.post(
        "/api/ollabridge/pair",
        json={"project_id": pid, "code": "GKEV-8985"},
        headers=auth_headers(bob),
    )
    assert r.status_code == 403
