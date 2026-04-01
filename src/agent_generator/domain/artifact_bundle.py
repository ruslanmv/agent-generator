"""Typed output contract for generated projects."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class GeneratedFile(BaseModel):
    """A single generated file in the artifact bundle."""
    path: str = Field(..., description="Relative file path.")
    content: str = Field(..., description="File content.")
    language: str | None = Field(default=None, description="Language hint for syntax highlighting.")


class ValidationIssue(BaseModel):
    """A validation finding attached to a build."""
    level: Literal["info", "warning", "error"] = "warning"
    message: str = ""


class ArtifactBundle(BaseModel):
    """Complete typed output of a build operation."""
    files: list[GeneratedFile] = Field(default_factory=list)
    manifest: dict[str, Any] = Field(default_factory=dict)
    warnings: list[ValidationIssue] = Field(default_factory=list)
    errors: list[ValidationIssue] = Field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not any(e.level == "error" for e in self.errors)
