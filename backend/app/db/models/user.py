"""User row.

One user per OAuth identity (provider, provider_user_id). Email is
collected when the provider exposes it but is not the primary key —
users can revoke / change emails on GitHub without orphaning their
agent-generator projects.
"""

from __future__ import annotations

from typing import Literal
from uuid import uuid4

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin

Role = Literal["admin", "user"]
Provider = Literal["github"]


class User(Base, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("provider", "provider_user_id", name="provider_identity"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    provider: Mapped[Provider] = mapped_column(String(16), nullable=False)
    provider_user_id: Mapped[str] = mapped_column(String(64), nullable=False)
    username: Mapped[str] = mapped_column(String(128), nullable=False)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    role: Mapped[Role] = mapped_column(String(16), default="user", nullable=False)

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"<User {self.username!r} role={self.role}>"
