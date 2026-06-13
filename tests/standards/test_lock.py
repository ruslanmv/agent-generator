"""Batch 3 — deterministic MATRIX_STANDARDS.lock construction + schema validity."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent_generator.contracts import QualityLevel
from agent_generator.standards import (
    build_standards_lock,
    load_pack,
    load_profile,
    render_lock_yaml,
)

jsonschema = pytest.importorskip("jsonschema")

_LOCK_SCHEMA = (
    Path(__file__).resolve().parents[1]
    / "contracts"
    / "schemas"
    / "matrix-standards-lock.schema.json"
)
_GENERATED_AT = "2026-06-12T14:00:00Z"


def _build(level: str = "standard"):
    pack = load_pack()
    profile = load_profile(None, level)
    return build_standards_lock(
        pack,
        quality_level=QualityLevel(level),
        profile=profile,
        generated_at=_GENERATED_AT,
    )


def test_lock_validates_against_matrix_definitions_schema() -> None:
    lock = _build()
    schema = json.loads(_LOCK_SCHEMA.read_text())
    jsonschema.validate(instance=lock.to_definitions_dict(), schema=schema)


def test_lock_is_deterministic() -> None:
    assert render_lock_yaml(_build()) == render_lock_yaml(_build())


def test_lock_pins_pack_and_sorts_rules() -> None:
    lock = _build("standard")
    assert lock.definitions_pack.pack_id == "matrix-definitions-current"
    assert lock.definitions_pack.version == "2026.06.0"
    assert lock.definitions_pack.checksum.startswith("sha256:")
    assert lock.rules == sorted(lock.rules)
    assert lock.quality_level == QualityLevel.STANDARD
    # Every pinned checksum is a sha256 reference to a pack input.
    assert lock.checksums
    assert all(v.startswith("sha256:") for v in lock.checksums.values())


def test_quality_levels_produce_different_rule_sets() -> None:
    starter = set(_build("starter").rules)
    enterprise = set(_build("enterprise").rules)
    assert starter != enterprise
    assert starter, "starter profile should still apply some rules"
