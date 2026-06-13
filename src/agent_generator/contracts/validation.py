"""Validation contracts — request, report, violations, and repair output."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from agent_generator.contracts.common import (
    API_TO_DEFINITIONS_STATUS,
    JsonDict,
    StrictModel,
    ValidationStatus,
)

Severity = Literal["info", "low", "medium", "high", "critical"]
CheckStatus = Literal["passed", "failed", "skipped"]
FileChangeStatus = Literal["added", "modified", "deleted", "renamed"]
DependencyChangeAction = Literal["added", "updated", "removed"]
ValidationMode = Literal["bundle", "patch", "repository", "dry-run"]


class ChangedFile(StrictModel):
    path: str = Field(min_length=1)
    status: FileChangeStatus = "modified"
    digest: str | None = None
    previous_path: str | None = None


class DependencyChange(StrictModel):
    ecosystem: str = Field(min_length=1)
    name: str = Field(min_length=1)
    action: DependencyChangeAction = "added"
    version: str | None = None
    approved: bool = False
    reason: str | None = None


class ValidationArtifact(StrictModel):
    kind: str = Field(min_length=1)
    path: str = Field(min_length=1)
    digest: str | None = None
    verified: bool = False


class ValidationRequest(StrictModel):
    schema_version: str = "matrix.builder.validation-request/v1"
    bundle_id: str | None = None
    mode: ValidationMode = "patch"
    changed_files: list[ChangedFile] = Field(default_factory=list)
    dependency_changes: list[DependencyChange] = Field(default_factory=list)
    artifacts: list[ValidationArtifact] = Field(default_factory=list)
    standards_lock_digest: str | None = None
    matrix_blueprint_digest: str | None = None
    repository_archive_ref: str | None = None
    patch_ref: str | None = None
    metadata: JsonDict = Field(default_factory=dict)


class ValidationViolation(StrictModel):
    rule_id: str
    severity: Severity
    message: str
    path: str | None = None
    remediation: str | None = None


class ValidationCheck(StrictModel):
    check_id: str
    status: CheckStatus
    message: str | None = None


class ValidationReport(StrictModel):
    report_id: str = "validation_not_run"
    bundle_id: str = "bundle_demo"
    status: ValidationStatus = ValidationStatus.NOT_RUN
    score: int = Field(default=0, ge=0, le=100)
    violations: list[ValidationViolation] = Field(default_factory=list)
    repair_prompt: str | None = None
    checks: list[ValidationCheck] = Field(default_factory=list)
    approved: bool = False
    matrixhub_publishable: bool = False
    summary: str | None = None
    created_at: datetime | None = None

    def to_definitions_dict(self) -> JsonDict:
        """Project onto matrix-definitions ``validation-report.schema.json``."""
        out: JsonDict = {
            "schema_version": "1.0",
            "status": API_TO_DEFINITIONS_STATUS[self.status.value],
            "checks": [
                {"id": c.check_id, "status": c.status, "message": c.message or ""}
                for c in self.checks
            ],
            "errors": [v.message for v in self.violations if v.severity in {"high", "critical"}],
            "warnings": [
                v.message for v in self.violations if v.severity in {"info", "low", "medium"}
            ],
        }
        if self.created_at is not None:
            out["created_at"] = self.created_at.strftime("%Y-%m-%dT%H:%M:%SZ")
        return out


__all__ = [
    "Severity",
    "CheckStatus",
    "FileChangeStatus",
    "DependencyChangeAction",
    "ValidationMode",
    "ChangedFile",
    "DependencyChange",
    "ValidationArtifact",
    "ValidationRequest",
    "ValidationViolation",
    "ValidationCheck",
    "ValidationReport",
]
