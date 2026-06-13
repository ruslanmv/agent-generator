"""Batch 7 — per-coder prompt adapters."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from agent_generator.coder_adapters import get_adapter
from agent_generator.contracts import CoderId, IdeaRequest
from agent_generator.engine import AgentGenerator

FIXED_NOW = datetime(2026, 6, 12, 14, 0, 0, tzinfo=timezone.utc)

# Each coder is governed by a specific matrix-definitions rule.
CODER_RULE = {
    CoderId.CLAUDE_CODE: "RMD-110",
    CoderId.CODEX_CHATGPT: "RMD-111",
    CoderId.CURSOR: "RMD-108",
    CoderId.GITPILOT: "RMD-113",
    CoderId.IBM_BOB: "RMD-112",
    CoderId.GENERIC_AI_CODER: "RMD-114",
}


@pytest.fixture()
def engine() -> AgentGenerator:
    return AgentGenerator(fixed_now=FIXED_NOW)


@pytest.fixture()
def blueprint(engine: AgentGenerator):
    return engine.generate_controlled_blueprint(
        IdeaRequest(idea="An AI agent that analyzes GitHub repositories for risks")
    )


def test_registry_covers_all_coders() -> None:
    for coder in CoderId:
        assert get_adapter(coder).coder == coder


def test_unknown_coder_falls_back_to_generic() -> None:
    assert get_adapter("totally-unknown-coder").coder == CoderId.GENERIC_AI_CODER


def test_every_prompt_has_status_stop_condition(engine: AgentGenerator, blueprint) -> None:
    pack = engine.build_prompt_pack(blueprint, bundle_id="bundle-x")
    assert {p.coder for p in pack.prompts} == set(CoderId)
    for prompt in pack.prompts:
        assert "MATRIX_STATUS: approved | needs_repair | rejected" in prompt.content
        assert "RMD-101" in prompt.content  # worker, not architect
        assert "MATRIX_BLUEPRINT.yaml" in prompt.contract_files


def test_each_prompt_cites_its_governing_rule(engine: AgentGenerator, blueprint) -> None:
    pack = engine.build_prompt_pack(blueprint, bundle_id="bundle-x")
    by_coder = {p.coder: p for p in pack.prompts}
    for coder, rule in CODER_RULE.items():
        assert rule in by_coder[coder].content, f"{coder} should cite {rule}"


def test_prompts_are_task_scoped_and_list_allowed_files(engine: AgentGenerator, blueprint) -> None:
    pack = engine.build_prompt_pack(blueprint, bundle_id="bundle-x")
    first_task = blueprint.tasks[0]
    for prompt in pack.prompts:
        assert first_task.task_id in prompt.content
        for f in first_task.allowed_files:
            assert f in prompt.content


def test_prompt_includes_bundle_fetch_url(engine: AgentGenerator, blueprint) -> None:
    pack = engine.build_prompt_pack(blueprint, bundle_id="bundle-x")
    for prompt in pack.prompts:
        assert "GET /api/v1/bundles/bundle-x/download" in prompt.content


def test_single_prompt_response_carries_handoff_mode(engine: AgentGenerator, blueprint) -> None:
    bundle = engine.generate_matrix_bundle(blueprint)
    resp = engine.generate_coder_prompt_pack(
        bundle.bundle_id, CoderId.GITPILOT, blueprint=blueprint
    )
    assert resp.handoff_mode == "git"
    assert resp.coder == CoderId.GITPILOT
    assert "RMD-113" in resp.prompt


def test_prompts_are_deterministic(blueprint) -> None:
    a = AgentGenerator(fixed_now=FIXED_NOW).build_prompt_pack(blueprint, bundle_id="b")
    b = AgentGenerator(fixed_now=FIXED_NOW).build_prompt_pack(blueprint, bundle_id="b")
    assert [p.content for p in a.prompts] == [p.content for p in b.prompts]


def test_prompts_cite_lock_rmd_rules(engine: AgentGenerator, blueprint) -> None:
    # The standard profile pins several RMD-1xx rules; the prompt cites them.
    pack = engine.build_prompt_pack(blueprint, bundle_id="b")
    claude = next(p for p in pack.prompts if p.coder == CoderId.CLAUDE_CODE)
    assert "Governing rules:" in claude.content
    assert "RMD-119" in claude.content  # validation commands mandatory
