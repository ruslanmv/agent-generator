"""Deterministic plan of which files to generate."""
from __future__ import annotations

from pydantic import BaseModel, Field


class ArtifactEntry(BaseModel):
    """A single file to be rendered from a Jinja2 template."""

    path: str = Field(..., description="Relative file path in the output project.")
    template: str = Field(..., description="Jinja2 template name to render.")
    language: str = Field(
        default="python", description="File language for syntax highlighting."
    )


class RenderPlan(BaseModel):
    """Complete manifest of artifacts, dependencies, and framework version."""

    artifacts: list[ArtifactEntry] = Field(default_factory=list)
    dependencies: list[str] = Field(
        default_factory=list, description="pip packages needed."
    )
    framework_version: str = Field(
        default="", description="Framework pip specifier."
    )
