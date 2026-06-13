"""Cross-repo contract test: engine canonical artifacts validate against matrix-definitions.

The engine produces objects in the Matrix Builder *API* shape, and each carries a
``to_definitions_dict()`` projection onto the canonical *signed-standard* shape owned by
matrix-definitions. This test loads the matrix-definitions JSON Schemas (vendored copy by
default, or a live checkout via ``MATRIX_DEFINITIONS_DIR``) and asserts the projections
validate. It is the guard that keeps agent-generator, matrix-builder, and matrix-definitions
in agreement.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from agent_generator.contracts import (
    DefinitionsPackRef,
    IdeaRequest,
    QualityLevel,
    StandardsLock,
    ValidationCheck,
    ValidationReport,
    ValidationStatus,
    ValidationViolation,
)
from agent_generator.engine import AgentGenerator

jsonschema = pytest.importorskip("jsonschema")

_VENDORED = Path(__file__).parent / "schemas"


def _schema(name: str) -> dict:
    live = os.environ.get("MATRIX_DEFINITIONS_DIR")
    base = Path(live) / "schemas" if live else _VENDORED
    return json.loads((base / f"{name}.schema.json").read_text())


def _validate(instance: dict, schema_name: str) -> None:
    jsonschema.validate(instance=instance, schema=_schema(schema_name))


@pytest.fixture()
def engine() -> AgentGenerator:
    return AgentGenerator()


def test_blueprint_candidate_projection_is_valid(engine: AgentGenerator) -> None:
    idea = IdeaRequest(idea="Analyze public GitHub repositories and report risks")
    for candidate in engine.generate_blueprint_candidates(idea):
        _validate(candidate.to_definitions_dict(), "blueprint-candidate")


def test_controlled_blueprint_projection_is_valid(engine: AgentGenerator) -> None:
    idea = IdeaRequest(idea="Analyze public GitHub repositories and report risks")
    blueprint = engine.generate_controlled_blueprint(idea)
    _validate(blueprint.to_definitions_dict(), "matrix-blueprint")


def test_validation_report_projection_is_valid() -> None:
    report = ValidationReport(
        report_id="val-1",
        bundle_id="bundle-1",
        status=ValidationStatus.NEEDS_REPAIR,
        score=70,
        violations=[
            ValidationViolation(rule_id="RMD-002", severity="critical", message="forbidden change")
        ],
        checks=[ValidationCheck(check_id="forbidden_changes_absent", status="failed")],
    )
    instance = report.to_definitions_dict()
    assert instance["status"] == "needs_repair"  # API hyphen -> canonical underscore
    _validate(instance, "validation-report")


def test_standards_lock_projection_is_valid() -> None:
    lock = StandardsLock(
        generated_at="2026-06-12T14:00:00Z",
        definitions_pack=DefinitionsPackRef(
            pack_id="matrix-definitions-current",
            version="2026.06.0",
            checksum="sha256:" + "a" * 64,
        ),
        quality_level=QualityLevel.STANDARD,
        rules=["RMD-001", "GHA-002"],
        control_files=["MATRIX_BLUEPRINT.yaml", "MATRIX_STANDARDS.lock"],
        checksums={"MATRIX_BLUEPRINT.yaml": "sha256:" + "b" * 64},
    )
    _validate(lock.to_definitions_dict(), "matrix-standards-lock")
