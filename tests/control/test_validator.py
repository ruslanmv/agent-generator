"""Batch 8 — single validation authority: checks, drift, repair, input modes."""

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


# --- backward-compatible degraded path (no blueprint) ----------------------


def test_not_run_when_empty(engine: AgentGenerator) -> None:
    report = engine.validate_ai_coder_patch(bundle_id="b")
    assert report.status == ValidationStatus.NOT_RUN


def test_forbidden_change_rejected_without_contract(engine: AgentGenerator) -> None:
    req = ValidationRequest(changed_files=[ChangedFile(path="MATRIX_BLUEPRINT.yaml")])
    report = engine.validate_ai_coder_patch(bundle_id="b", request=req)
    assert report.status == ValidationStatus.REJECTED
    assert report.violations[0].rule_id == "RMD-002"
    assert "RMD-002" in report.repair_prompt


def test_allowed_change_approved_without_contract(engine: AgentGenerator) -> None:
    req = ValidationRequest(changed_files=[ChangedFile(path="backend/app/api/routes.py")])
    report = engine.validate_ai_coder_patch(bundle_id="b", request=req)
    assert report.status == ValidationStatus.APPROVED


# --- full contract enforcement (with blueprint) ----------------------------


def test_outside_allowlist_needs_repair(engine: AgentGenerator, blueprint) -> None:
    req = ValidationRequest(changed_files=[ChangedFile(path="totally/random/hack.py")])
    report = engine.validate_ai_coder_patch(bundle_id="b", request=req, blueprint=blueprint)
    assert report.status == ValidationStatus.NEEDS_REPAIR
    assert any(v.rule_id == "RMD-107" for v in report.violations)


def test_denied_dependency_rejected(engine: AgentGenerator, blueprint) -> None:
    req = ValidationRequest(
        dependency_changes=[DependencyChange(ecosystem="npm", name="shelljs", action="added")]
    )
    report = engine.validate_ai_coder_patch(bundle_id="b", request=req, blueprint=blueprint)
    assert report.status == ValidationStatus.REJECTED
    assert any(v.rule_id == "RMD-003" for v in report.violations)


def test_unapproved_dependency_needs_repair(engine: AgentGenerator, blueprint) -> None:
    req = ValidationRequest(
        dependency_changes=[DependencyChange(ecosystem="pypi", name="leftpad", action="added")]
    )
    report = engine.validate_ai_coder_patch(bundle_id="b", request=req, blueprint=blueprint)
    assert report.status == ValidationStatus.NEEDS_REPAIR
    assert any(v.rule_id == "RMD-116" for v in report.violations)


def test_baseline_dependency_is_allowed(engine: AgentGenerator, blueprint) -> None:
    req = ValidationRequest(
        dependency_changes=[DependencyChange(ecosystem="pypi", name="fastapi", action="added")]
    )
    report = engine.validate_ai_coder_patch(bundle_id="b", request=req, blueprint=blueprint)
    assert report.status == ValidationStatus.APPROVED


# --- repo / zip / patch input modes ----------------------------------------


def test_clean_exported_repo_is_approved(engine: AgentGenerator, blueprint, tmp_path) -> None:
    # Export the bundle, extract it, and validate it against its own blueprint: clean.
    zip_path = engine.export_zip(blueprint, tmp_path / "b.zip")
    repo = tmp_path / "repo"
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(repo)
    report = engine.validate_ai_coder_patch(bundle_id="b", repo_path=repo, blueprint=blueprint)
    assert report.status == ValidationStatus.APPROVED, [v.message for v in report.violations]


def test_repo_with_tampered_immutable_file_rejected(
    engine: AgentGenerator, blueprint, tmp_path
) -> None:
    zip_path = engine.export_zip(blueprint, tmp_path / "b.zip")
    repo = tmp_path / "repo"
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(repo)
    (repo / "MATRIX_BLUEPRINT.yaml").write_text("name: hacked\n")
    report = engine.validate_ai_coder_patch(bundle_id="b", repo_path=repo, blueprint=blueprint)
    assert report.status == ValidationStatus.REJECTED
    assert any(v.rule_id in {"RMD-001", "RMD-002"} for v in report.violations)


def test_zip_with_secret_rejected(engine: AgentGenerator, blueprint, tmp_path) -> None:
    zip_path = engine.export_zip(blueprint, tmp_path / "b.zip")
    repo = tmp_path / "repo"
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(repo)
    (repo / "backend" / "app").mkdir(parents=True, exist_ok=True)
    (repo / "backend" / "app" / "config.py").write_text('API_KEY = "8fJ2kLmN9pQr3sTuVwXyZ012"\n')
    out = tmp_path / "out.zip"
    import shutil

    shutil.make_archive(str(out.with_suffix("")), "zip", repo)
    report = engine.validate_ai_coder_patch(bundle_id="b", zip_path=out, blueprint=blueprint)
    assert any(v.rule_id == "SEC-001" for v in report.violations)
    assert report.status == ValidationStatus.REJECTED


def test_patch_with_forbidden_file_rejected(engine: AgentGenerator, blueprint) -> None:
    diff = (
        "diff --git a/MATRIX_STANDARDS.lock b/MATRIX_STANDARDS.lock\n"
        "--- a/MATRIX_STANDARDS.lock\n"
        "+++ b/MATRIX_STANDARDS.lock\n"
        "@@ -1 +1 @@\n"
        "+tampered: true\n"
    )
    report = engine.validate_ai_coder_patch(bundle_id="b", patch=diff, blueprint=blueprint)
    assert report.status == ValidationStatus.REJECTED
    assert any(v.rule_id == "RMD-002" for v in report.violations)


def test_patch_adding_secret_in_allowed_file_rejected(engine: AgentGenerator, blueprint) -> None:
    diff = (
        "diff --git a/backend/app/api/repos.py b/backend/app/api/repos.py\n"
        "--- a/backend/app/api/repos.py\n"
        "+++ b/backend/app/api/repos.py\n"
        "@@ -1 +1,2 @@\n"
        '+GITHUB_TOKEN = "ghp_abcdef1234567890ABCDEFabcdef1234567890"\n'
    )
    report = engine.validate_ai_coder_patch(bundle_id="b", patch=diff, blueprint=blueprint)
    assert any(v.rule_id == "SEC-001" for v in report.violations)


# --- report shape ----------------------------------------------------------


def test_report_has_checks_score_and_repair(engine: AgentGenerator, blueprint) -> None:
    req = ValidationRequest(changed_files=[ChangedFile(path="totally/random/hack.py")])
    report = engine.validate_ai_coder_patch(bundle_id="b", request=req, blueprint=blueprint)
    assert report.checks, "per-check summaries present"
    assert 0 <= report.score <= 100
    assert report.repair_prompt and "RMD-120" in report.repair_prompt
    assert report.matrixhub_publishable is False


def test_validation_is_deterministic(engine: AgentGenerator, blueprint) -> None:
    req = ValidationRequest(changed_files=[ChangedFile(path="totally/random/hack.py")])
    a = AgentGenerator(fixed_now=FIXED_NOW).validate_ai_coder_patch(
        bundle_id="b", request=req, blueprint=blueprint
    )
    b = AgentGenerator(fixed_now=FIXED_NOW).validate_ai_coder_patch(
        bundle_id="b", request=req, blueprint=blueprint
    )
    assert a.model_dump() == b.model_dump()
