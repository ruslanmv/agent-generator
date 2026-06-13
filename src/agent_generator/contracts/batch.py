"""Batch contracts (Batch E1) — the unit of incremental, in-version change.

A *version* change ("Update requirements" → ``regenerate``) bumps the product contract and
creates a new ``bundle_version``. A *batch* ("Continue build") is the next small implementation
step **inside the current version**: it appends scoped tasks and emits a prompt pack, without
bumping the version or mutating the blueprint.

``change_type`` wire values are hyphenated, matching the engine convention (``ChangeType``).
Note ``fix-issue`` (a batch concern) replaces ``change-architecture`` (a version concern).
"""

from __future__ import annotations

from pydantic import Field

from agent_generator.contracts.blueprint import BlueprintTask
from agent_generator.contracts.common import CoderId, StrictModel, _StrEnum
from agent_generator.contracts.validation import ChangedFile, DependencyChange


class BatchChangeType(_StrEnum):
    SMALL_UPDATE = "small-update"
    ADD_FEATURE = "add-feature"
    FIX_ISSUE = "fix-issue"


class BatchPlan(StrictModel):
    """A planned incremental change: scoped tasks plus the contract context to implement them."""

    schema_version: str = "matrix.builder.batch-plan/v1"
    batch_id: str
    ordinal: int = Field(default=1, ge=1)
    title: str
    goal_md: str
    change_type: BatchChangeType
    blueprint_id: str | None = None  # the version this batch belongs to
    parent_commit_ref: str | None = None  # the commit this batch builds on, if any
    tasks: list[BlueprintTask] = Field(default_factory=list)  # the NEW tasks only
    allowed_files: list[str] = Field(default_factory=list)  # union of task allowlists
    acceptance_commands: list[str] = Field(default_factory=list)
    change_summary: list[str] = Field(default_factory=list)
    is_repair: bool = False


class BatchExecutionRequest(StrictModel):
    """Submitted after a coder implements a batch: what changed, for validation."""

    schema_version: str = "matrix.builder.batch-execution/v1"
    batch_id: str
    coder: CoderId = CoderId.GENERIC_AI_CODER
    changed_files: list[ChangedFile] = Field(default_factory=list)
    dependency_changes: list[DependencyChange] = Field(default_factory=list)
    patch: str | None = None
    repository_ref: str | None = None
    parent_commit_ref: str | None = None


__all__ = ["BatchChangeType", "BatchPlan", "BatchExecutionRequest"]
