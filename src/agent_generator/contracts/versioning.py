"""Versioning contracts (Batch 5).

The engine regenerates a new blueprint *version* from an existing one without mutating the
original — the capability behind Matrix Builder's "Update requirements" flow. The wire values
of ``ChangeType`` match the UI's three buttons (Small update / Add feature / Change
architecture).
"""

from __future__ import annotations

from agent_generator.contracts.blueprint import BlueprintResult
from agent_generator.contracts.common import StrictModel, _StrEnum


class ChangeType(_StrEnum):
    SMALL_UPDATE = "small-update"
    ADD_FEATURE = "add-feature"
    CHANGE_ARCHITECTURE = "change-architecture"


class RegenerationRequest(StrictModel):
    schema_version: str = "matrix.builder.regeneration/v1"
    change_request: str
    change_type: ChangeType = ChangeType.ADD_FEATURE
    current_version: str = "1.0.0"


class RegenerationResult(StrictModel):
    blueprint: BlueprintResult
    version: str
    previous_version: str
    change_type: ChangeType
    change_summary: list[str]


__all__ = ["ChangeType", "RegenerationRequest", "RegenerationResult"]
