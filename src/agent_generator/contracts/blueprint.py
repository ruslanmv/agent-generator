"""Blueprint contracts — candidates and the controlled blueprint result.

``BlueprintCandidate`` and ``BlueprintResult`` mirror the Matrix Builder API shape. In
addition they each expose a ``to_definitions_dict()`` projection that produces the
canonical artifact validated by the matrix-definitions JSON schemas
(``blueprint-candidate.schema.json`` and ``matrix-blueprint.schema.json``). Keeping both
shapes in one place is what lets the cross-repo contract test prove the API shape and the
signed-standard shape stay in agreement.
"""

from __future__ import annotations

from pydantic import Field

from agent_generator.contracts.common import ApiRoute, JsonDict, QualityLevel, StrictModel
from agent_generator.contracts.idea import IdeaRequest

#: Schema version embedded in canonical matrix-definitions artifacts (``MAJOR.MINOR``).
DEFINITIONS_SCHEMA_VERSION = "1.0"


class BlueprintCandidate(StrictModel):
    candidate_id: str
    title: str
    slug: str
    summary: str
    quality_level: QualityLevel
    stack: list[str] = Field(default_factory=list)
    recommended: bool = False
    estimated_files: int = Field(default=1, ge=1)
    estimated_effort: str = "unknown"
    difficulty: str = "medium"
    standards_profile: str = "standard"
    rationale: str = ""
    generator_actions: list[str] = Field(default_factory=list)
    validation_checks: list[str] = Field(default_factory=list)

    def to_definitions_dict(self) -> JsonDict:
        """Project onto matrix-definitions ``blueprint-candidate.schema.json``."""
        return {
            "schema_version": DEFINITIONS_SCHEMA_VERSION,
            "candidate_id": self.candidate_id,
            "name": self.title,
            "summary": self.summary,
            "template": self.slug,
            "quality_level": self.quality_level.value,
            "score": _confidence_score(self.recommended, self.difficulty),
            "why": self.rationale or self.summary,
            "risks": list(self.validation_checks),
        }


class BlueprintCandidateResponse(StrictModel):
    candidates: list[BlueprintCandidate]


class BlueprintGenerationRequest(StrictModel):
    schema_version: str = "matrix.builder.blueprint-generation/v1"
    idea_request: IdeaRequest
    candidate_id: str | None = None


class BlueprintStack(StrictModel):
    frontend: str
    backend: str
    worker: str | None = None
    database: str | None = None
    auth: str = "none"
    deploy: str = "docker"


class BlueprintTask(StrictModel):
    task_id: str = Field(pattern=r"^TASK-[0-9]{3}$")
    title: str
    allowed_files: list[str] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(default_factory=list)


class BlueprintResult(StrictModel):
    blueprint_id: str
    candidate_id: str
    name: str
    slug: str
    idea: str
    quality_level: QualityLevel
    stack: BlueprintStack
    pages: list[str] = Field(default_factory=list)
    services: list[str] = Field(default_factory=list)
    api_routes: list[ApiRoute] = Field(default_factory=list)
    required_files: list[str] = Field(default_factory=list)
    allowed_change_roots: list[str] = Field(default_factory=list)
    forbidden_changes: list[str] = Field(default_factory=list)
    tasks: list[BlueprintTask] = Field(default_factory=list)
    acceptance_commands: list[str] = Field(default_factory=list)
    standards_lock_ref: str = "MATRIX_STANDARDS.lock"

    def to_definitions_dict(self, *, project_type: str = "fullstack") -> JsonDict:
        """Project onto matrix-definitions ``matrix-blueprint.schema.json``."""
        allowed_stack = {"backend": self.stack.backend, "frontend": self.stack.frontend}
        if self.stack.worker:
            allowed_stack["worker"] = self.stack.worker
        if self.stack.database:
            allowed_stack["database"] = self.stack.database
        allowed_stack["deploy"] = self.stack.deploy
        goal = self.idea if len(self.idea) >= 10 else f"Build: {self.idea}".ljust(10, ".")
        return {
            "schema_version": DEFINITIONS_SCHEMA_VERSION,
            "blueprint_id": self.blueprint_id,
            "name": self.name,
            "project_type": project_type,
            "goal": goal,
            "quality_level": self.quality_level.value,
            "allowed_stack": allowed_stack,
            "required_pages": list(self.pages),
            "required_api_routes": [{"method": r.method, "path": r.path} for r in self.api_routes],
            "required_files": list(self.required_files),
            "forbidden": list(self.forbidden_changes),
            "allowed_change_scopes": [
                {"task_id": task.task_id, "allowed_files": list(task.allowed_files)}
                for task in self.tasks
            ],
        }


def _confidence_score(recommended: bool, difficulty: str) -> float:
    """Deterministic 0..1 fit score used by the canonical candidate projection."""
    base = 0.82 if recommended else 0.6
    penalty = {"easy": 0.0, "medium": 0.05, "hard": 0.12}.get(difficulty, 0.05)
    return round(base - penalty, 3)


# Aliases matching the architecture-doc naming (``BlueprintSpec``/``TaskSpec``).
BlueprintSpec = BlueprintResult
TaskSpec = BlueprintTask

__all__ = [
    "DEFINITIONS_SCHEMA_VERSION",
    "BlueprintCandidate",
    "BlueprintCandidateResponse",
    "BlueprintGenerationRequest",
    "BlueprintStack",
    "BlueprintTask",
    "BlueprintResult",
    "BlueprintSpec",
    "TaskSpec",
]
