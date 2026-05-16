"""Project + ProjectFile rows.

A *project* is the persisted form of a wizard run: the user's framework
/ hyperscaler / pattern / model picks, the generated code, plus
metadata for the Marketplace / Export surfaces.

We store the canonical wizard state as JSON (``state``) so the schema
evolves with the wizard without migrations. Files live in a child
table because we stream them out to the Run / Docker pipelines.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal
from uuid import uuid4

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.user import User

Visibility = Literal["private", "public"]


class Project(Base, TimestampMixin):
    __tablename__ = "projects"
    __table_args__ = (
        Index("ix_projects_owner_updated", "owner_id", "updated_at"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    owner_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    framework: Mapped[str] = mapped_column(String(32), nullable=False)
    hyperscaler: Mapped[str | None] = mapped_column(String(16), nullable=True)
    pattern: Mapped[str | None] = mapped_column(String(16), nullable=True)
    model: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # The full wizard state (Step 1-6 fields) serialised as JSON. Lets
    # the wizard surface a single project row in the dashboard and
    # restore the user mid-flow.
    state: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    visibility: Mapped[Visibility] = mapped_column(
        String(16), default="private", nullable=False
    )

    owner: Mapped[User] = relationship(lazy="joined")
    files: Mapped[list[ProjectFile]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ProjectFile(Base, TimestampMixin):
    __tablename__ = "project_files"
    __table_args__ = (
        Index("ix_project_files_project_path", "project_id", "path", unique=True),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    path: Mapped[str] = mapped_column(String(512), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    project: Mapped[Project] = relationship(back_populates="files")
