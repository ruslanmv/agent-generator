"""JWT issuance + verification.

Tokens are HS256 by default — the symmetric key lives in
``AG_JWT_SECRET``. RS256 support is wired into the algorithm field so
fleets that want asymmetric signing can drop a PEM into env.

We deliberately keep claims minimal: ``sub`` (user id), ``role``,
``typ`` (``access`` / ``refresh``), and the standard ``iat`` / ``exp``.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import jwt
from jwt.exceptions import InvalidTokenError

from app.settings import get_settings

TokenType = Literal["access", "refresh"]


class TokenError(Exception):
    """Raised when a token is missing, malformed, or expired."""


def _now() -> datetime:
    return datetime.now(tz=UTC)


def issue_token(
    *,
    subject: str,
    role: str,
    typ: TokenType,
    extra: dict[str, Any] | None = None,
) -> str:
    settings = get_settings()
    ttl = (
        settings.jwt_access_ttl_seconds
        if typ == "access"
        else settings.jwt_refresh_ttl_seconds
    )
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "typ": typ,
        "iat": _now(),
        "exp": _now() + timedelta(seconds=ttl),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str, *, expected_typ: TokenType | None = None) -> dict[str, Any]:
    settings = get_settings()
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except InvalidTokenError as exc:
        raise TokenError(str(exc)) from exc
    if expected_typ is not None and payload.get("typ") != expected_typ:
        raise TokenError(f"expected typ={expected_typ}, got {payload.get('typ')!r}")
    return payload
