"""Batch E3 — tool-native helper files and batch-context prompts (6-coder canary)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from agent_generator.contracts import CoderHandoff, CoderId, IdeaRequest
from agent_generator.engine import AgentGenerator

FIXED_NOW = datetime(2026, 6, 12, 14, 0, 0, tzinfo=timezone.utc)

# The tool-native instruction file each coder emits.
HELPER_FILENAME = {
    CoderId.CLAUDE_CODE: "CLAUDE.md",
    CoderId.CODEX_CHATGPT: "AGENTS.md",
    CoderId.CURSOR: "MATRIX_INSTRUCTIONS.md",
    CoderId.GITPILOT: ".gitpilotrules",  # GitPilot reads workspace rules from .gitpilotrules
    CoderId.IBM_BOB: "MATRIX_INSTRUCTIONS.md",
    CoderId.GENERIC_AI_CODER: "MATRIX_INSTRUCTIONS.md",
}


@pytest.fixture()
def engine() -> AgentGenerator:
    return AgentGenerator(fixed_now=FIXED_NOW)


@pytest.fixture()
def blueprint(engine: AgentGenerator):
    return engine.generate_controlled_blueprint(
        IdeaRequest(idea="An AI agent that analyzes GitHub repositories for risks")
    )


@pytest.mark.parametrize("coder", list(CoderId))
def test_every_coder_emits_a_helper_file(engine: AgentGenerator, blueprint, coder: CoderId) -> None:
    handoff = engine.coder_handoff(blueprint, coder, bundle_id="b1")
    assert isinstance(handoff, CoderHandoff)
    assert handoff.coder == coder
    assert set(handoff.helper_files) == {HELPER_FILENAME[coder]}
    helper = handoff.helper_files[HELPER_FILENAME[coder]]
    # The helper is contract-derived and ends with the stop condition.
    assert "MATRIX_BLUEPRINT.yaml" in helper
    assert "MATRIX_STATUS" in helper
    assert "RMD-101" in helper
    assert "RMD-119" in helper  # validation commands mandatory


def test_claude_helper_is_claude_md(engine: AgentGenerator, blueprint) -> None:
    h = engine.coder_handoff(blueprint, CoderId.CLAUDE_CODE)
    assert "CLAUDE.md" in h.helper_files


def test_codex_helper_is_agents_md(engine: AgentGenerator, blueprint) -> None:
    h = engine.coder_handoff(blueprint, CoderId.CODEX_CHATGPT)
    assert "AGENTS.md" in h.helper_files


def test_handoff_prompt_has_no_batch_context_by_default(engine: AgentGenerator, blueprint) -> None:
    h = engine.coder_handoff(blueprint, CoderId.CLAUDE_CODE)
    assert "Batch" not in h.prompt.prompt.split("\n", 3)[0]  # no batch line in the header
    assert "Current batch" not in h.helper_files["CLAUDE.md"]


def test_batch_handoff_carries_batch_context(engine: AgentGenerator, blueprint) -> None:
    plan = engine.plan_batch(
        blueprint, "Add authentication", "add-feature", ordinal=3, parent_commit="mc-2"
    )
    handoff = engine.coder_handoff(blueprint, CoderId.CLAUDE_CODE, batch=plan, bundle_id="b1")
    assert handoff.batch_id == plan.batch_id
    # Batch context appears in both the prompt and the helper file.
    assert "Batch 03" in handoff.prompt.prompt
    assert "commit mc-2" in handoff.prompt.prompt
    assert "Current batch" in handoff.helper_files["CLAUDE.md"]
    # The prompt targets the batch's task.
    assert plan.tasks[0].task_id in handoff.prompt.prompt


def test_handoff_is_deterministic(blueprint) -> None:
    a = AgentGenerator(fixed_now=FIXED_NOW).coder_handoff(blueprint, CoderId.GITPILOT)
    b = AgentGenerator(fixed_now=FIXED_NOW).coder_handoff(blueprint, CoderId.GITPILOT)
    assert a.model_dump() == b.model_dump()
