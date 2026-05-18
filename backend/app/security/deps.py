"""FastAPI dependencies for the current user.

Two flavours:

- ``get_current_user`` — required; raises 401 if the request has no
  valid access token. Use on every protected route.
- ``require_admin`` — required + role check; raises 403 for non-admins.

Tokens are read from the ``Authorization: Bearer ...`` header (native
shells + curl) or the ``ag_session`` HttpOnly cookie (web).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.db.session import get_session
from app.security.jwt import TokenError, decode_token

SESSION_COOKIE_NAME = "ag_session"


def _extract_token(request: Request) -> str | None:
    auth = request.headers.get("authorization")
    if auth and auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip()
    return request.cookies.get(SESSION_COOKIE_NAME)


async def get_current_user(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    token = _extract_token(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_token(token, expected_typ="access")
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"invalid token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = await session.get(User, payload["sub"])
    if user is None:
        # Token references a deleted user — treat as logged out.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="user no longer exists",
        )
    return user


async def require_admin(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="admin role required",
        )
    return user


async def get_or_create_user(
    *,
    session: AsyncSession,
    provider: str,
    provider_user_id: str,
    username: str,
    email: str | None,
    avatar_url: str | None,
    admin_email: str | None,
) -> User:
    """Upsert helper used by the OAuth callback."""
    stmt = select(User).where(
        User.provider == provider,
        User.provider_user_id == provider_user_id,
    )
    row = (await session.execute(stmt)).scalar_one_or_none()

    is_first_user = False
    if row is None:
        count_stmt = select(User.id).limit(1)
        is_first_user = (await session.execute(count_stmt)).first() is None

    role = (
        "admin"
        if is_first_user
        or (admin_email and (email == admin_email or username == admin_email))
        else "user"
    )

    if row is None:
        row = User(
            provider=provider,
            provider_user_id=provider_user_id,
            username=username,
            email=email,
            avatar_url=avatar_url,
            role=role,
        )
        session.add(row)
        await session.flush()
    else:
        row.username = username
        row.email = email
        row.avatar_url = avatar_url
        # Promote to admin if newly matched by admin_email; never demote.
        if role == "admin" and row.role != "admin":
            row.role = "admin"
    return row
