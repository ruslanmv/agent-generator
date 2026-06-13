"""Commit-snapshot contract (Batch E2).

A ``matrix_commit`` is an immutable technical checkpoint of a bundle's tree: its content hash,
the change set relative to its parent, the batch that produced it, and its validation status.
Versions are product milestones; commits are the system-visible checkpoints between them.
"""

from __future__ import annotations

from pydantic import Field

from agent_generator.contracts.common import StrictModel, ValidationStatus


class CommitManifest(StrictModel):
    schema_version: str = "matrix.builder.commit-manifest/v1"
    commit_no: int = Field(ge=1)
    parent_commit_ref: str | None = None
    batch_ref: str | None = None
    tree_hash: str
    validation_status: ValidationStatus = ValidationStatus.NOT_RUN
    summary: str = ""
    added: list[str] = Field(default_factory=list)
    changed: list[str] = Field(default_factory=list)
    deleted: list[str] = Field(default_factory=list)


__all__ = ["CommitManifest"]
