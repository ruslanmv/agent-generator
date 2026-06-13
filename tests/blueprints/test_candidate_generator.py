"""Batch 4 — candidate generator: template-aware, scored, deterministic, schema-valid."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent_generator.blueprints import generate_candidates
from agent_generator.contracts import IdeaConstraints, IdeaRequest, QualityLevel
from agent_generator.runtime import EngineRuntime

jsonschema = pytest.importorskip("jsonschema")

_CANDIDATE_SCHEMA = (
    Path(__file__).resolve().parents[1]
    / "contracts"
    / "schemas"
    / "blueprint-candidate.schema.json"
)

RUNTIME = EngineRuntime()

GITHUB_IDEA = IdeaRequest(idea="An AI agent that analyzes GitHub repositories for risks")
GENERIC_IDEA = IdeaRequest(idea="A recipe planner for weekly family meals")


def test_three_quality_tiers() -> None:
    candidates = generate_candidates(GITHUB_IDEA, RUNTIME)
    assert [c.quality_level for c in candidates] == [
        QualityLevel.STARTER,
        QualityLevel.STANDARD,
        QualityLevel.PRODUCTION,
    ]


def test_flagship_idea_uses_template_slug() -> None:
    candidates = generate_candidates(GITHUB_IDEA, RUNTIME)
    slugs = {c.slug for c in candidates}
    assert slugs == {
        "github-repo-intelligence-agent-starter",
        "github-repo-intelligence-agent",
        "github-repo-intelligence-agent-production",
    }


def test_generic_idea_uses_idea_slug() -> None:
    candidates = generate_candidates(GENERIC_IDEA, RUNTIME)
    standard = next(c for c in candidates if c.quality_level == QualityLevel.STANDARD)
    assert "recipe" in standard.slug


def test_rationale_names_template_and_score() -> None:
    candidates = generate_candidates(GITHUB_IDEA, RUNTIME)
    standard = next(c for c in candidates if c.quality_level == QualityLevel.STANDARD)
    assert "GitHub Repo Intelligence Agent" in standard.rationale
    assert "fit score" in standard.rationale


def test_recommended_follows_requested_quality() -> None:
    starter_req = IdeaRequest(idea=GITHUB_IDEA.idea, quality_level=QualityLevel.STARTER)
    recommended = [c for c in generate_candidates(starter_req, RUNTIME) if c.recommended]
    assert len(recommended) == 1 and recommended[0].quality_level == QualityLevel.STARTER

    enterprise_req = IdeaRequest(idea=GITHUB_IDEA.idea, quality_level=QualityLevel.ENTERPRISE)
    recommended = [c for c in generate_candidates(enterprise_req, RUNTIME) if c.recommended]
    assert len(recommended) == 1 and recommended[0].quality_level == QualityLevel.PRODUCTION


def test_forbidden_stack_lowers_score_and_warns() -> None:
    constrained = IdeaRequest(
        idea=GITHUB_IDEA.idea,
        constraints=IdeaConstraints(forbidden_stack=["PostgreSQL"]),
    )
    candidates = generate_candidates(constrained, RUNTIME)
    standard = next(c for c in candidates if c.quality_level == QualityLevel.STANDARD)
    assert "forbidden stack" in standard.rationale.lower()


def test_candidates_are_deterministic() -> None:
    a = generate_candidates(GITHUB_IDEA, EngineRuntime())
    b = generate_candidates(GITHUB_IDEA, EngineRuntime())
    assert [c.model_dump() for c in a] == [c.model_dump() for c in b]


def test_template_candidates_validate_against_definitions_schema() -> None:
    schema = json.loads(_CANDIDATE_SCHEMA.read_text())
    for idea in (GITHUB_IDEA, GENERIC_IDEA):
        for candidate in generate_candidates(idea, RUNTIME):
            jsonschema.validate(instance=candidate.to_definitions_dict(), schema=schema)
