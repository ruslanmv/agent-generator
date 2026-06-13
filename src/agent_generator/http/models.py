"""Request bodies for the Matrix engine HTTP facade (Batch 9).

Responses are the engine contracts themselves (``BlueprintResult``, ``MatrixBundle``, …); these
models only describe the composite request bodies the stateless endpoints accept.
"""

from __future__ import annotations

from pydantic import Field

from agent_generator.contracts.batch import BatchChangeType, BatchPlan
from agent_generator.contracts.blueprint import BlueprintResult
from agent_generator.contracts.common import CoderId, StrictModel
from agent_generator.contracts.idea import IdeaRequest
from agent_generator.contracts.validation import ValidationRequest
from agent_generator.contracts.versioning import ChangeType


class CandidateSelection(StrictModel):
    idea_request: IdeaRequest
    candidate_id: str | None = None


class BundleRequest(StrictModel):
    blueprint: BlueprintResult
    preferred_coder: CoderId = CoderId.GENERIC_AI_CODER


class PromptRequest(StrictModel):
    blueprint: BlueprintResult
    coder: CoderId = CoderId.GENERIC_AI_CODER
    bundle_id: str | None = None
    bundle_url: str | None = None


class RegenerationApiRequest(StrictModel):
    base_blueprint: BlueprintResult
    change_request: str
    change_type: ChangeType = ChangeType.ADD_FEATURE
    current_version: str = "1.0.0"


class ValidationApiRequest(StrictModel):
    blueprint: BlueprintResult | None = None
    request: ValidationRequest | None = None
    patch: str | None = None
    current_version: str = "1.0.0"
    bundle_id: str | None = None


class ExportRequest(StrictModel):
    blueprint: BlueprintResult
    version: str = "1.0.0"
    preferred_coder: CoderId = CoderId.GENERIC_AI_CODER


class BatchPlanApiRequest(StrictModel):
    blueprint: BlueprintResult
    goal_md: str
    change_type: BatchChangeType = BatchChangeType.ADD_FEATURE
    ordinal: int = Field(default=1, ge=1)
    parent_commit: str | None = None


class BatchPromptApiRequest(StrictModel):
    blueprint: BlueprintResult
    batch: BatchPlan | None = None
    coders: list[CoderId] | None = None  # default: all coders
    bundle_id: str | None = None
    bundle_url: str | None = None


class DiffApiRequest(StrictModel):
    base_files: dict[str, str] = Field(default_factory=dict)
    head_files: dict[str, str] = Field(default_factory=dict)


__all__ = [
    "CandidateSelection",
    "BundleRequest",
    "PromptRequest",
    "RegenerationApiRequest",
    "ValidationApiRequest",
    "ExportRequest",
    "BatchPlanApiRequest",
    "BatchPromptApiRequest",
    "DiffApiRequest",
]
