"""Batch 1 — public engine API boundary tests.

Covers the six SDK methods Matrix Builder's adapter calls, the additive helpers, and the
determinism guarantee the engine must provide for snapshot/golden tests.
"""

from __future__ import annotations

import zipfile
from datetime import datetime, timezone

import pytest

from agent_generator import AgentGenerator as ExportedAgentGenerator
from agent_generator.contracts import (
    BlueprintCandidate,
    BlueprintResult,
    ChangedFile,
    CoderId,
    IdeaIntent,
    IdeaRequest,
    MatrixBundle,
    PromptPack,
    PromptResponse,
    QualityLevel,
    ValidationReport,
    ValidationRequest,
    ValidationStatus,
)
from agent_generator.engine import AgentGenerator
from agent_generator.errors import CandidateNotFoundError

FIXED_NOW = datetime(2026, 6, 12, 14, 0, 0, tzinfo=timezone.utc)


@pytest.fixture()
def engine() -> AgentGenerator:
    return AgentGenerator(fixed_now=FIXED_NOW)


@pytest.fixture()
def idea() -> IdeaRequest:
    return IdeaRequest(idea="Build an AI app that analyzes GitHub repositories")


def test_engine_importable_from_both_paths() -> None:
    assert ExportedAgentGenerator is AgentGenerator


def test_status_shape_matches_adapter() -> None:
    status = AgentGenerator().status()
    assert status["engine"] == "agent-generator"
    assert status["mode"] == "sdk"
    assert "boundary" in status


def test_parse_idea_returns_intent(engine: AgentGenerator, idea: IdeaRequest) -> None:
    intent = engine.parse_idea(idea)
    assert isinstance(intent, IdeaIntent)
    assert intent.normalized_idea == "Build an AI app that analyzes GitHub repositories"
    assert intent.quality_level == idea.quality_level


def test_parse_idea_accepts_dict(engine: AgentGenerator) -> None:
    intent = engine.parse_idea({"idea": "Summarize PDFs with an agent"})
    assert isinstance(intent, IdeaIntent)


def test_candidates_three_and_typed(engine: AgentGenerator, idea: IdeaRequest) -> None:
    candidates = engine.generate_blueprint_candidates(idea)
    assert len(candidates) == 3
    assert all(isinstance(c, BlueprintCandidate) for c in candidates)
    levels = {c.quality_level for c in candidates}
    assert levels == {QualityLevel.STARTER, QualityLevel.STANDARD, QualityLevel.PRODUCTION}


def test_candidates_are_deterministic(idea: IdeaRequest) -> None:
    a = AgentGenerator(fixed_now=FIXED_NOW).generate_blueprint_candidates(idea)
    b = AgentGenerator(fixed_now=FIXED_NOW).generate_blueprint_candidates(idea)
    assert [c.candidate_id for c in a] == [c.candidate_id for c in b]


def test_controlled_blueprint_is_wired_to_planner(
    engine: AgentGenerator, idea: IdeaRequest
) -> None:
    blueprint = engine.generate_controlled_blueprint(idea)
    assert isinstance(blueprint, BlueprintResult)
    assert blueprint.tasks, "tasks should be derived from the planned spec"
    assert "MATRIX_BLUEPRINT.yaml" in blueprint.forbidden_changes
    assert blueprint.standards_lock_ref == "MATRIX_STANDARDS.lock"


def test_controlled_blueprint_selects_candidate(engine: AgentGenerator, idea: IdeaRequest) -> None:
    candidates = engine.generate_blueprint_candidates(idea)
    starter = next(c for c in candidates if c.quality_level == QualityLevel.STARTER)
    blueprint = engine.generate_controlled_blueprint(idea, candidate_id=starter.candidate_id)
    assert blueprint.candidate_id == starter.candidate_id
    assert blueprint.quality_level == QualityLevel.STARTER


def test_controlled_blueprint_unknown_candidate_raises(
    engine: AgentGenerator, idea: IdeaRequest
) -> None:
    with pytest.raises(CandidateNotFoundError):
        engine.generate_controlled_blueprint(idea, candidate_id="cand-does-not-exist")


def test_generate_matrix_bundle(engine: AgentGenerator, idea: IdeaRequest) -> None:
    blueprint = engine.generate_controlled_blueprint(idea)
    bundle = engine.generate_matrix_bundle(blueprint, preferred_coder=CoderId.CLAUDE_CODE)
    assert isinstance(bundle, MatrixBundle)
    assert bundle.blueprint_id == blueprint.blueprint_id
    assert bundle.file_count and bundle.file_count > 0
    assert bundle.manifest_digest and bundle.manifest_digest.startswith("sha256:")


def test_generate_coder_prompt_pack_returns_prompt_response(
    engine: AgentGenerator, idea: IdeaRequest
) -> None:
    blueprint = engine.generate_controlled_blueprint(idea)
    bundle = engine.generate_matrix_bundle(blueprint)
    prompt = engine.generate_coder_prompt_pack(
        bundle.bundle_id, CoderId.CLAUDE_CODE, blueprint=blueprint
    )
    assert isinstance(prompt, PromptResponse)
    assert "MATRIX_BLUEPRINT.yaml" in prompt.contract_files
    assert "claude" in prompt.path
    assert len(prompt.prompt) > 100


def test_build_prompt_pack_has_all_coders(engine: AgentGenerator, idea: IdeaRequest) -> None:
    blueprint = engine.generate_controlled_blueprint(idea)
    pack = engine.build_prompt_pack(blueprint)
    assert isinstance(pack, PromptPack)
    assert {p.coder for p in pack.prompts} == set(CoderId)


def test_validate_not_run_without_changes(engine: AgentGenerator) -> None:
    report = engine.validate_ai_coder_patch(bundle_id="bundle-1")
    assert isinstance(report, ValidationReport)
    assert report.status == ValidationStatus.NOT_RUN


def test_validate_rejects_forbidden_change(engine: AgentGenerator) -> None:
    request = ValidationRequest(
        bundle_id="bundle-1",
        changed_files=[ChangedFile(path="MATRIX_BLUEPRINT.yaml", status="modified")],
    )
    report = engine.validate_ai_coder_patch(bundle_id="bundle-1", request=request)
    assert report.status == ValidationStatus.REJECTED
    assert report.violations and report.violations[0].rule_id == "RMD-002"
    assert report.repair_prompt and "RMD-002" in report.repair_prompt


def test_validate_approves_allowed_change(engine: AgentGenerator) -> None:
    request = ValidationRequest(
        bundle_id="bundle-1",
        changed_files=[ChangedFile(path="backend/app/api/routes.py", status="modified")],
    )
    report = engine.validate_ai_coder_patch(bundle_id="bundle-1", request=request)
    assert report.status == ValidationStatus.APPROVED
    assert report.approved is True
    assert report.repair_prompt is None


def test_export_zip_is_deterministic_and_complete(
    engine: AgentGenerator, idea: IdeaRequest, tmp_path
) -> None:
    blueprint = engine.generate_controlled_blueprint(idea)
    out1 = engine.export_zip(blueprint, tmp_path / "a.zip")
    out2 = engine.export_zip(blueprint, tmp_path / "b.zip")
    assert out1.read_bytes() == out2.read_bytes(), "export should be byte-for-byte deterministic"
    with zipfile.ZipFile(out1) as zf:
        names = set(zf.namelist())
    assert "MATRIX_BLUEPRINT.yaml" in names
    assert "MATRIX_STANDARDS.lock" in names
    assert "coder-prompts/claude-code.md" in names


def test_adapter_alias_methods_exist_and_match(engine: AgentGenerator, idea: IdeaRequest) -> None:
    # Matrix Builder's adapter exposes generate_coder_prompt / validate_bundle; both must be
    # callable on the engine and behave identically to the canonical method names.
    blueprint = engine.generate_controlled_blueprint(idea)
    bundle = engine.generate_matrix_bundle(blueprint)

    via_alias = engine.generate_coder_prompt(
        bundle.bundle_id, CoderId.CLAUDE_CODE, blueprint=blueprint
    )
    via_canonical = engine.generate_coder_prompt_pack(
        bundle.bundle_id, CoderId.CLAUDE_CODE, blueprint=blueprint
    )
    assert via_alias.model_dump() == via_canonical.model_dump()

    alias_report = engine.validate_bundle(bundle_id="bundle-1")
    canonical_report = engine.validate_ai_coder_patch(bundle_id="bundle-1")
    assert alias_report.status == canonical_report.status == ValidationStatus.NOT_RUN


def test_info_lists_capabilities_and_frameworks(engine: AgentGenerator) -> None:
    info = engine.info()
    assert info.engine == "agent-generator"
    assert "generate_controlled_blueprint" in info.capabilities
    assert "crewai" in info.frameworks
