"""Auth flow tests.

GitHub's HTTP endpoints are stubbed with ``respx`` (via ``httpx``'s
transport mocking) so the OAuth callback runs end-to-end against
predictable fixtures.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest

from app.security import oauth
from app.security.jwt import decode_token, issue_token


@pytest.mark.asyncio
async def test_me_requires_auth(client: Any) -> None:
    r = await client.get("/api/auth/me")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_login_without_github_config_returns_503(client: Any) -> None:
    # GH client id is unset in conftest — login should bail out cleanly.
    r = await client.get("/api/auth/github/login", follow_redirects=False)
    assert r.status_code == 503


@pytest.mark.asyncio
async def test_login_with_github_config_redirects(
    client: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AG_GITHUB_CLIENT_ID", "test_id")
    monkeypatch.setenv("AG_GITHUB_CLIENT_SECRET", "test_secret")
    from app.settings import get_settings

    get_settings.cache_clear()

    r = await client.get(
        "/api/auth/github/login?next=/wizard",
        follow_redirects=False,
    )
    assert r.status_code == 302
    assert r.headers["location"].startswith("https://github.com/login/oauth/authorize")
    assert "state=" in r.headers["location"]


@pytest.mark.asyncio
async def test_state_signing_roundtrip() -> None:
    token = oauth.sign_state({"next": "/x"})
    assert oauth.verify_state(token) == {"next": "/x"}


@pytest.mark.asyncio
async def test_state_tampering_rejected() -> None:
    token = oauth.sign_state({"next": "/x"})
    with pytest.raises(oauth.OAuthError):
        oauth.verify_state(token + "tamper")


@pytest.mark.asyncio
async def test_callback_creates_admin_for_first_user(
    client: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AG_GITHUB_CLIENT_ID", "test_id")
    monkeypatch.setenv("AG_GITHUB_CLIENT_SECRET", "test_secret")
    from app.settings import get_settings

    get_settings.cache_clear()

    async def fake_exchange(code: str, *, redirect_uri: str) -> str:  # noqa: ARG001
        return "fake-access-token"

    async def fake_profile(token: str) -> oauth.GitHubProfile:  # noqa: ARG001
        return oauth.GitHubProfile(
            id="42",
            username="octocat",
            email="octo@example.com",
            avatar_url="https://avatars.githubusercontent.com/u/42",
        )

    with (
        patch("app.api.auth.oauth.exchange_code", side_effect=fake_exchange),
        patch("app.api.auth.oauth.fetch_profile", side_effect=fake_profile),
    ):
        state = oauth.sign_state({"next": "/wizard"})
        r = await client.get(
            f"/api/auth/github/callback?code=abc&state={state}",
            follow_redirects=False,
        )
    assert r.status_code == 302
    assert r.headers["location"].endswith("/wizard")
    cookie = r.cookies.get("ag_session")
    assert cookie
    payload = decode_token(cookie, expected_typ="access")
    assert payload["role"] == "admin"

    # Subsequent /me with the cookie returns the user.
    client.cookies.set("ag_session", cookie)
    r2 = await client.get("/api/auth/me")
    assert r2.status_code == 200
    body = r2.json()
    assert body["username"] == "octocat"
    assert body["role"] == "admin"


@pytest.mark.asyncio
async def test_refresh_issues_new_pair(client: Any) -> None:
    # Pre-seed a user via direct DB insert + manual token issuance.
    from sqlalchemy import select

    from app.db.models.user import User
    from app.db.session import get_sessionmaker

    Session = get_sessionmaker()
    async with Session() as session:
        user = User(
            provider="github",
            provider_user_id="99",
            username="alice",
            email="alice@example.com",
            avatar_url=None,
            role="user",
        )
        session.add(user)
        await session.commit()
        uid = (await session.execute(select(User.id).where(User.username == "alice"))).scalar_one()

    refresh_token = issue_token(subject=uid, role="user", typ="refresh")
    r = await client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert r.status_code == 200
    body = r.json()
    assert decode_token(body["access_token"], expected_typ="access")["sub"] == uid


@pytest.mark.asyncio
async def test_logout_clears_cookie(client: Any) -> None:
    r = await client.post("/api/auth/logout")
    assert r.status_code == 200
    assert "ag_session" in r.headers.get("set-cookie", "")
