"""Shared Matrix contract primitives.

These mirror the Matrix Builder API schemas field-for-field and enum-for-enum so the
``agent-generator`` engine can be consumed by Matrix Builder in SDK mode without any
translation layer. The string values of every enum are part of the cross-repo contract
and must not change without a coordinated update in:

* ``matrix-builder`` (``services/api/app/schemas``)
* ``matrix-definitions`` (``schemas/*.schema.json``)

Python 3.10 compatibility note: Matrix Builder uses ``enum.StrEnum`` (3.11+). This package
targets ``requires-python >= 3.10``, so we use ``str``-mixed ``Enum`` instead. The wire value
(``member.value`` and JSON serialization) is identical.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    """Base model matching Matrix Builder's ``StrictModel`` semantics."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class _StrEnum(str, Enum):
    """3.10-compatible stand-in for ``enum.StrEnum``."""

    def __str__(self) -> str:  # pragma: no cover - cosmetic parity with StrEnum
        return str(self.value)


class BuildType(_StrEnum):
    APP = "app"
    AGENT = "agent"
    API = "api"


class Goal(_StrEnum):
    PORTFOLIO = "portfolio"
    STARTUP_MVP = "startup-mvp"
    INTERNAL_TOOL = "internal-tool"
    LEARNING = "learning"
    OPEN_SOURCE = "open-source"
    ENTERPRISE = "enterprise"


class QualityLevel(_StrEnum):
    STARTER = "starter"
    STANDARD = "standard"
    PRODUCTION = "production"
    ENTERPRISE = "enterprise"


class CoderId(_StrEnum):
    CLAUDE_CODE = "claude-code"
    CODEX_CHATGPT = "codex-chatgpt"
    CURSOR = "cursor"
    GITPILOT = "gitpilot"
    IBM_BOB = "ibm-bob"
    GENERIC_AI_CODER = "generic-ai-coder"


class ValidationStatus(_StrEnum):
    """API-facing validation status (hyphenated wire values, per Matrix Builder)."""

    NOT_RUN = "not-run"
    APPROVED = "approved"
    NEEDS_REPAIR = "needs-repair"
    REJECTED = "rejected"


class BundleStatus(_StrEnum):
    DRAFT = "draft"
    READY = "ready"
    EXPIRED = "expired"
    ARCHIVED = "archived"
    SAVED = "saved"


class ApiRoute(StrictModel):
    method: str = Field(pattern="^(GET|POST|PUT|PATCH|DELETE)$")
    path: str = Field(pattern="^/")
    summary: str | None = None
    auth_required: bool = False


class BundleFile(StrictModel):
    path: str = Field(min_length=1)
    kind: str = "control"
    required: bool = True
    content_type: str = "text/plain"
    digest: str | None = None
    size_bytes: int | None = Field(default=None, ge=0)


class ContractFileRef(StrictModel):
    path: str
    required: bool = True
    reason: str | None = None


JsonDict = dict[str, Any]

# The canonical "definitions" status values use underscores (matrix-definitions
# validation-report.schema.json), whereas the API uses hyphens. This map projects
# the API status onto the signed-standard status when emitting canonical artifacts.
API_TO_DEFINITIONS_STATUS: dict[str, str] = {
    ValidationStatus.NOT_RUN.value: "draft",
    ValidationStatus.APPROVED.value: "approved",
    ValidationStatus.NEEDS_REPAIR.value: "needs_repair",
    ValidationStatus.REJECTED.value: "rejected",
}

__all__ = [
    "StrictModel",
    "BuildType",
    "Goal",
    "QualityLevel",
    "CoderId",
    "ValidationStatus",
    "BundleStatus",
    "ApiRoute",
    "BundleFile",
    "ContractFileRef",
    "JsonDict",
    "API_TO_DEFINITIONS_STATUS",
]
