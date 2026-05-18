"""GitHub OAuth client.

Uses ``authlib`` to handle the dance:

1. ``GET  /api/auth/github/login``    → 302 to GitHub authorize URL
2. ``GET  /api/auth/github/callback`` ← GitHub redirects back with a code
3. Exchange code for access token, fetch the user's profile + email.

The state parameter is a signed token (``itsdangerous``) carrying the
post-login bounce target so the frontend can resume where it left off.

We don't store the GitHub access token: once we've identified the user
we issue our own JWT and drop the GitHub token on the floor.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx
from itsdangerous import BadSignature, URLSafeTimedSerializer

from app.settings import get_settings

GITHUB_AUTHORIZE = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"  # noqa: S105 — public URL, not a credential
GITHUB_USER_URL = "https://api.github.com/user"
GITHUB_EMAILS_URL = "https://api.github.com/user/emails"

STATE_SALT = "agent-generator:oauth:state"
STATE_MAX_AGE_SECONDS = 600  # 10 minutes


@dataclass(frozen=True)
class GitHubProfile:
    id: str
    username: str
    email: str | None
    avatar_url: str | None


class OAuthError(Exception):
    """OAuth flow failure (state mismatch, token exchange error, ...)."""


def _serializer() -> URLSafeTimedSerializer:
    settings = get_settings()
    secret = settings.cookie_secret or settings.jwt_secret
    return URLSafeTimedSerializer(secret_key=secret, salt=STATE_SALT)


def sign_state(payload: dict[str, Any]) -> str:
    return _serializer().dumps(payload)


def verify_state(token: str) -> dict[str, Any]:
    try:
        result: dict[str, Any] = _serializer().loads(token, max_age=STATE_MAX_AGE_SECONDS)
        return result
    except BadSignature as exc:
        raise OAuthError(f"invalid state: {exc}") from exc


def authorize_url(*, state: str, redirect_uri: str, scopes: list[str]) -> str:
    settings = get_settings()
    if not settings.github_client_id:
        raise OAuthError("AG_GITHUB_CLIENT_ID is not set")
    params = {
        "client_id": settings.github_client_id,
        "redirect_uri": redirect_uri,
        "scope": " ".join(scopes),
        "state": state,
        "allow_signup": "true",
    }
    qs = "&".join(f"{k}={httpx.QueryParams({k: v})[k]}" for k, v in params.items())
    return f"{GITHUB_AUTHORIZE}?{qs}"


async def exchange_code(code: str, *, redirect_uri: str) -> str:
    settings = get_settings()
    if not (settings.github_client_id and settings.github_client_secret):
        raise OAuthError("GitHub OAuth not configured")
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.post(
            GITHUB_TOKEN_URL,
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
                "redirect_uri": redirect_uri,
            },
        )
    if r.status_code != 200:
        raise OAuthError(f"token exchange failed: HTTP {r.status_code}")
    body = r.json()
    token = body.get("access_token")
    if not token:
        raise OAuthError(f"token exchange returned no access_token: {body!r}")
    return str(token)


async def fetch_profile(access_token: str) -> GitHubProfile:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
        r_user = await client.get(GITHUB_USER_URL)
        if r_user.status_code != 200:
            raise OAuthError(f"GET /user failed: HTTP {r_user.status_code}")
        user = r_user.json()

        email = user.get("email")
        if not email:
            # Fall back to /user/emails: pick the primary verified address.
            r_emails = await client.get(GITHUB_EMAILS_URL)
            if r_emails.status_code == 200:
                for entry in r_emails.json():
                    if entry.get("primary") and entry.get("verified"):
                        email = entry.get("email")
                        break

    return GitHubProfile(
        id=str(user["id"]),
        username=user.get("login") or f"user-{user['id']}",
        email=email,
        avatar_url=user.get("avatar_url"),
    )
