"""Idea contracts — input to the engine and the normalized intent it returns."""

from __future__ import annotations

from pydantic import Field

from agent_generator.contracts.common import (
    BuildType,
    CoderId,
    Goal,
    QualityLevel,
    StrictModel,
)


class IdeaConstraints(StrictModel):
    preferred_stack: list[str] = Field(default_factory=list)
    forbidden_stack: list[str] = Field(default_factory=list)
    deployment_target: str = "docker"
    requires_auth: bool = False
    data_sensitivity: str = "public"


class IdeaMetadata(StrictModel):
    source: str = "matrix-builder-web"
    locale: str = "en"
    request_id: str | None = None


class IdeaRequest(StrictModel):
    schema_version: str = "matrix.builder.idea/v1"
    idea: str = Field(min_length=5, max_length=4000)
    build_type: BuildType = BuildType.APP
    goal: Goal = Goal.STARTUP_MVP
    preferred_coder: CoderId = CoderId.GENERIC_AI_CODER
    quality_level: QualityLevel = QualityLevel.STANDARD
    constraints: IdeaConstraints = Field(default_factory=IdeaConstraints)
    metadata: IdeaMetadata = Field(default_factory=IdeaMetadata)


class IdeaIntent(StrictModel):
    normalized_idea: str
    build_type: BuildType
    goal: Goal
    preferred_coder: CoderId
    quality_level: QualityLevel = QualityLevel.STANDARD
    constraints: IdeaConstraints = Field(default_factory=IdeaConstraints)


__all__ = ["IdeaConstraints", "IdeaMetadata", "IdeaRequest", "IdeaIntent"]
