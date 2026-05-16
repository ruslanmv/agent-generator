"""Shared pytest fixtures.

We use an in-memory aiosqlite database per test session and clear the
``get_settings`` / ``get_engine`` LRU caches so the override takes
effect before the app's lifespan opens any connection.
"""

from __future__ import annotations

import os
import tempfile
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import pytest

# Set test env BEFORE app modules import. Use a temp file rather than
# :memory: so the background run engine and the request handlers share
# the same SQLite database (each aiosqlite connection sees its own
# in-memory DB otherwise).
_TMP_DB = Path(tempfile.gettempdir()) / f"ag_test_{os.getpid()}.sqlite"
if _TMP_DB.exists():
    _TMP_DB.unlink()

os.environ.setdefault("AG_ENV", "test")
os.environ.setdefault("AG_DATABASE_URL", f"sqlite+aiosqlite:///{_TMP_DB}")
os.environ.setdefault(
    "AG_JWT_SECRET",
    "test-secret-not-for-prod-but-long-enough-to-clear-rfc-7518-32-byte-minimum",
)
os.environ.setdefault("AG_PUBLIC_URL", "http://testserver")


@pytest.fixture(autouse=True)
def _reset_settings_cache() -> None:
    from app.settings import get_settings

    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _reset_db_caches() -> None:
    from app.db.session import get_engine, get_sessionmaker

    get_engine.cache_clear()
    get_sessionmaker.cache_clear()
    # Wipe the shared sqlite file between tests so each starts clean.
    if _TMP_DB.exists():
        _TMP_DB.unlink()


@pytest.fixture
async def client() -> AsyncIterator[Any]:
    """ASGI client wired to a fresh in-memory DB."""
    from httpx import ASGITransport, AsyncClient

    from app.db.session import init_models
    from app.main import app

    await init_models()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as c:
        yield c


@pytest.fixture
async def make_user() -> Any:
    """Factory: create a User row and return (user_id, access_token)."""
    from app.db.models.user import User
    from app.db.session import get_sessionmaker
    from app.security.jwt import issue_token

    async def _make(
        username: str = "alice",
        role: str = "user",
        provider_user_id: str | None = None,
    ) -> tuple[str, str]:
        Session = get_sessionmaker()  # noqa: N806
        async with Session() as session:
            user = User(
                provider="github",
                provider_user_id=provider_user_id or f"id-{username}",
                username=username,
                email=f"{username}@example.com",
                avatar_url=None,
                role=role,  # type: ignore[arg-type]
            )
            session.add(user)
            await session.commit()
            uid = user.id
        token = issue_token(subject=uid, role=role, typ="access")
        return uid, token

    return _make


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
