"""Auth routes.

Endpoints:

- ``GET  /api/auth/github/login``    → 302 to GitHub authorize URL
- ``GET  /api/auth/github/callback`` ← GitHub returns ?code=...&state=...
                                       Issues JWT, sets cookie, bounces
                                       back to ``next``.
- ``POST /api/auth/refresh``         → swap a refresh token for a new
                                       access + refresh pair.
- ``POST /api/auth/logout``          → clear cookie.
- ``GET  /api/auth/me``              → current user profile.

The frontend triggers a login by linking to ``/api/auth/github/login``;
the backend handles every other step.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.db.session import get_session
from app.security import oauth
from app.security.deps import (
    SESSION_COOKIE_NAME,
    get_current_user,
    get_or_create_user,
)
from app.security.jwt import TokenError, decode_token, issue_token
from app.settings import Settings, get_settings

router = APIRouter(prefix="/api/auth", tags=["auth"])

DEFAULT_GITHUB_SCOPES = ["read:user", "user:email"]


class UserOut(BaseModel):
    id: str
    provider: str
    username: str
    email: str | None
    avatar_url: str | None
    role: str

    @classmethod
    def from_orm_user(cls, user: User) -> UserOut:
        return cls(
            id=user.id,
            provider=user.provider,
            username=user.username,
            email=user.email,
            avatar_url=user.avatar_url,
            role=user.role,
        )


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"  # noqa: S105 — OAuth2 token type identifier, not a secret


class RefreshIn(BaseModel):
    refresh_token: str


def _callback_url(settings: Settings) -> str:
    return f"{settings.public_url.rstrip('/')}/api/auth/github/callback"


def _set_session_cookie(response: Response, token: str, settings: Settings) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=settings.jwt_access_ttl_seconds,
        httponly=True,
        secure=settings.env == "prod",
        samesite="lax",
        path="/",
    )


@router.get("/github/login")
async def github_login(
    next: Annotated[str, Query(description="Post-login bounce URL.")] = "/",
    settings: Settings = Depends(get_settings),  # noqa: B008 — FastAPI DI pattern
) -> RedirectResponse:
    if not settings.github_client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub OAuth is not configured on this server.",
        )
    state = oauth.sign_state({"next": next})
    url = oauth.authorize_url(
        state=state,
        redirect_uri=_callback_url(settings),
        scopes=DEFAULT_GITHUB_SCOPES,
    )
    return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)


@router.get("/github/callback")
async def github_callback(
    code: Annotated[str, Query()],
    state: Annotated[str, Query()],
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> RedirectResponse:
    try:
        bounce = oauth.verify_state(state)
    except oauth.OAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    try:
        access = await oauth.exchange_code(code, redirect_uri=_callback_url(settings))
        profile = await oauth.fetch_profile(access)
    except oauth.OAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
        ) from exc

    user = await get_or_create_user(
        session=session,
        provider="github",
        provider_user_id=profile.id,
        username=profile.username,
        email=profile.email,
        avatar_url=profile.avatar_url,
        admin_email=settings.admin_email,
    )

    access_token = issue_token(subject=user.id, role=user.role, typ="access")

    target = bounce.get("next", "/") or "/"
    if not target.startswith("/"):
        # Only same-origin bounces to keep open-redirect off the table.
        target = "/"
    response = RedirectResponse(
        url=f"{settings.public_url.rstrip('/')}{target}",
        status_code=status.HTTP_302_FOUND,
    )
    _set_session_cookie(response, access_token, settings)
    return response


@router.post("/refresh", response_model=TokenPair)
async def refresh(
    body: RefreshIn,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TokenPair:
    try:
        payload = decode_token(body.refresh_token, expected_typ="refresh")
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc

    user = await session.get(User, payload["sub"])
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="user no longer exists"
        )
    access = issue_token(subject=user.id, role=user.role, typ="access")
    refresh_token = issue_token(subject=user.id, role=user.role, typ="refresh")
    return TokenPair(access_token=access, refresh_token=refresh_token)


@router.post("/logout")
async def logout(
    response: Response,
    request: Request,
) -> dict[str, str]:
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    return {"status": "ok"}


@router.get("/me", response_model=UserOut)
async def me(user: Annotated[User, Depends(get_current_user)]) -> UserOut:
    return UserOut.from_orm_user(user)
