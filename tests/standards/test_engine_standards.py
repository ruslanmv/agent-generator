"""Batch 3 — engine surface for standards and lock emission in exports."""

from __future__ import annotations

import zipfile
from datetime import datetime, timezone

import pytest

from agent_generator.contracts import IdeaRequest, QualityLevel, StandardsLock
from agent_generator.engine import AgentGenerator

FIXED_NOW = datetime(2026, 6, 12, 14, 0, 0, tzinfo=timezone.utc)


@pytest.fixture()
def engine() -> AgentGenerator:
    return AgentGenerator(fixed_now=FIXED_NOW)


def test_load_standards_pack(engine: AgentGenerator) -> None:
    pack = engine.load_standards_pack()
    assert pack.version == "2026.06.0"


def test_standards_metadata_reports_compatible(engine: AgentGenerator) -> None:
    meta = engine.standards_metadata()
    assert meta["compatibility"]["ok"] is True
    assert meta["checksums_ok"] is True
    assert meta["signature_mode"] == "placeholder"
    assert meta["version"] == "2026.06.0"


def test_generate_standards_lock(engine: AgentGenerator) -> None:
    lock = engine.generate_standards_lock(QualityLevel.STANDARD)
    assert isinstance(lock, StandardsLock)
    assert lock.generated_at == "2026-06-12T14:00:00Z"
    assert lock.rules


def test_export_embeds_real_lock(engine: AgentGenerator, tmp_path) -> None:
    idea = IdeaRequest(idea="Analyze GitHub repositories and report architecture risks")
    blueprint = engine.generate_controlled_blueprint(idea)
    out = engine.export_zip(blueprint, tmp_path / "bundle.zip")
    with zipfile.ZipFile(out) as zf:
        lock_text = zf.read("MATRIX_STANDARDS.lock").decode()
    # The export now carries the real signed-pack lock, not the Batch 1 placeholder text.
    assert "definitions_pack" in lock_text
    assert "2026.06.0" in lock_text
    assert "placeholder" not in lock_text.lower()
