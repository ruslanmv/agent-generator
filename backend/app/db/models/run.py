"""Run + RunEvent rows.

A *run* is one invocation of a project's agent. Events stream into
RunEvent for replay (the WS connection only sees live events; clients
that reconnect catch up via the events endpoint).

Status transitions: pending → running → (succeeded | failed | cancelled).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal
from uuid import uuid4

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.project import Project
    from app.db.models.user import User

RunStatus = Literal["pending", "running", "succeeded", "failed", "cancelled"]
EventKind = Literal["log", "trace", "tool", "result", "error", "status"]


class Run(Base, TimestampMixin):
    __tablename__ = "runs"
    __table_args__ = (
        Index("ix_runs_project_created", "project_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    owner_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[RunStatus] = mapped_column(
        String(16), default="pending", nullable=False
    )
    prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    project: Mapped["Project"] = relationship(lazy="joined")
    owner: Mapped["User"] = relationship(lazy="joined")
    events: Mapped[list["RunEvent"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="RunEvent.seq",
        lazy="selectin",
    )


class RunEvent(Base):
    """One event in a run's stream.

    `seq` is a monotonic per-run counter so clients can reconcile after
    a reconnect: ``GET /api/runs/{id}/events?after=N``.
    """

    __tablename__ = "run_events"
    __table_args__ = (
        Index("ix_run_events_run_seq", "run_id", "seq", unique=True),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    run_id: Mapped[str] = mapped_column(
        ForeignKey("runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    seq: Mapped[int] = mapped_column(nullable=False)
    kind: Mapped[EventKind] = mapped_column(String(16), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[str] = mapped_column(
        # ISO-8601 string is enough for replay; no need for a TZ-aware
        # timestamp column here since the wizard renders the value
        # client-side.
        String(40), nullable=False
    )

    run: Mapped[Run] = relationship(back_populates="events")
