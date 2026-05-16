"""Async engine + session factory.

One engine per process, one session per request. The session is created
lazily so test suites that monkey-patch the URL after import still pick
up the right database.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.settings import get_settings


@lru_cache(maxsize=1)
def get_engine() -> AsyncEngine:
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        echo=settings.env == "dev" and settings.log_level == "DEBUG",
        future=True,
        pool_pre_ping=True,
    )


@lru_cache(maxsize=1)
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        get_engine(),
        expire_on_commit=False,
        class_=AsyncSession,
    )


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency that yields one session per request."""
    Session = get_sessionmaker()  # noqa: N806
    async with Session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_models() -> None:
    """Create tables on first boot (dev-only fast path).

    Production deployments run Alembic migrations instead; this helper
    is wired into the lifespan when ``AG_ENV=dev`` so a fresh checkout
    works without manual setup.
    """
    from app.db.base import Base
    from app.db import models  # noqa: F401 — register tables

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
