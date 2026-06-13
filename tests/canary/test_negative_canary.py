"""Canary (negative): drift, forbidden edits, and secrets must be caught."""

from __future__ import annotations

import zipfile
from datetime import datetime, timezone

import pytest

from agent_generator.contracts import (
    ChangedFile,
    DependencyChange,
    IdeaRequest,
    ValidationRequest,
    ValidationStatus,
)
from agent_generator.engine import AgentGenerator

FIXED_NOW = datetime(2026, 6, 12, 14, 0, 0, tzinfo=timezone.utc)
IDEA = IdeaRequest(idea="An AI agent that analyzes GitHub repositories for risks")


@pytest.fixture()
def engine() -> AgentGenerator:
    return AgentGenerator(fixed_now=FIXED_NOW)


@pytest.fixture()
def blueprint(engine: AgentGenerator):
    return engine.generate_controlled_blueprint(IDEA)


def test_forbidden_file_injection_is_caught(engine: AgentGenerator, blueprint) -> None:
    req = ValidationRequest(changed_files=[ChangedFile(path="MATRIX_STANDARDS.lock")])
    report = engine.validate_ai_coder_patch("b", request=req, blueprint=blueprint)
    assert report.status == ValidationStatus.REJECTED
    assert any(v.rule_id == "RMD-002" for v in report.violations)


def test_dependency_drift_is_caught(engine: AgentGenerator, blueprint) -> None:
    req = ValidationRequest(
        dependency_changes=[DependencyChange(ecosystem="pypi", name="leftpad", action="added")]
    )
    report = engine.validate_ai_coder_patch("b", request=req, blueprint=blueprint)
    assert report.status == ValidationStatus.NEEDS_REPAIR
    assert any(v.rule_id == "RMD-116" for v in report.violations)


def test_denied_dependency_is_rejected(engine: AgentGenerator, blueprint) -> None:
    req = ValidationRequest(
        dependency_changes=[DependencyChange(ecosystem="npm", name="shelljs", action="added")]
    )
    report = engine.validate_ai_coder_patch("b", request=req, blueprint=blueprint)
    assert report.status == ValidationStatus.REJECTED


def test_secret_injection_is_caught(engine: AgentGenerator, blueprint, tmp_path) -> None:
    zip_path = engine.export_zip(blueprint, tmp_path / "b.zip")
    repo = tmp_path / "repo"
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(repo)
    (repo / "backend" / "app").mkdir(parents=True, exist_ok=True)
    (repo / "backend" / "app" / "cfg.py").write_text('SECRET_KEY = "9aF3kLpQ2mNvX7yR8tWzB1cD"\n')
    report = engine.validate_ai_coder_patch("b", repo_path=repo, blueprint=blueprint)
    assert report.status == ValidationStatus.REJECTED
    assert any(v.rule_id == "SEC-001" for v in report.violations)


def test_architecture_route_drift_is_caught(engine: AgentGenerator, blueprint, tmp_path) -> None:
    zip_path = engine.export_zip(blueprint, tmp_path / "b.zip")
    repo = tmp_path / "repo"
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(repo)
    # Rewrite the blueprint with a different route set: drift (and an immutable edit).
    bp = (repo / "MATRIX_BLUEPRINT.yaml").read_text()
    bp = bp.replace("/api/v1/repos/analyze", "/api/v1/repos/EXFILTRATE")
    (repo / "MATRIX_BLUEPRINT.yaml").write_text(bp)
    report = engine.validate_ai_coder_patch("b", repo_path=repo, blueprint=blueprint)
    assert report.status == ValidationStatus.REJECTED
    rules = {v.rule_id for v in report.violations}
    assert "RMD-115" in rules or "RMD-001" in rules
