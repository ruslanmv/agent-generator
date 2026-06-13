"""Blueprint models (architecture-named re-export).

Canonical definitions live in ``agent_generator.contracts.blueprint``. This module exists
so code and docs can import from the architecture path ``agent_generator.blueprints.models``.
"""

from __future__ import annotations

from agent_generator.contracts.blueprint import (
    BlueprintCandidate,
    BlueprintCandidateResponse,
    BlueprintGenerationRequest,
    BlueprintResult,
    BlueprintSpec,
    BlueprintStack,
    BlueprintTask,
    TaskSpec,
)

__all__ = [
    "BlueprintCandidate",
    "BlueprintCandidateResponse",
    "BlueprintGenerationRequest",
    "BlueprintResult",
    "BlueprintSpec",
    "BlueprintStack",
    "BlueprintTask",
    "TaskSpec",
]
