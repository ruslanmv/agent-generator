"""Batch 4 — controlled blueprints built from flagship templates."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from agent_generator.contracts import IdeaRequest, QualityLevel
from agent_generator.engine import AgentGenerator

FIXED_NOW = datetime(2026, 6, 12, 14, 0, 0, tzinfo=timezone.utc)


@pytest.fixture()
def engine() -> AgentGenerator:
    return AgentGenerator(fixed_now=FIXED_NOW)


def test_github_blueprint_uses_template_plan(engine: AgentGenerator) -> None:
    idea = IdeaRequest(idea="An AI agent that analyzes GitHub repositories for risks")
    blueprint = engine.generate_controlled_blueprint(idea)
    assert blueprint.name == "GitHub Repo Intelligence Agent"
    assert blueprint.slug == "github-repo-intelligence-agent"
    assert "/analyze" in blueprint.pages
    routes = {(r.method, r.path) for r in blueprint.api_routes}
    assert ("POST", "/api/v1/repos/analyze") in routes
    titles = [t.title for t in blueprint.tasks]
    assert any("repos/analyze" in t for t in titles)
    assert all(t.task_id.startswith("TASK-") for t in blueprint.tasks)


def test_document_qa_blueprint_uses_template_plan(engine: AgentGenerator) -> None:
    idea = IdeaRequest(idea="A document Q&A assistant that answers questions from PDFs")
    blueprint = engine.generate_controlled_blueprint(idea)
    assert blueprint.slug == "document-qa-agent"
    routes = {(r.method, r.path) for r in blueprint.api_routes}
    assert ("POST", "/api/v1/questions") in routes


def test_generic_blueprint_still_uses_planner_tasks(engine: AgentGenerator) -> None:
    idea = IdeaRequest(idea="A recipe planner for weekly family meals")
    blueprint = engine.generate_controlled_blueprint(idea)
    assert blueprint.tasks, "generic path should derive tasks from the planner"
    assert "recipe" in blueprint.slug


def test_auth_detected_from_idea_text(engine: AgentGenerator) -> None:
    idea = IdeaRequest(idea="A recipe planner with user login and accounts")
    blueprint = engine.generate_controlled_blueprint(idea)
    assert blueprint.stack.auth == "session"


def test_starter_level_selects_sqlite(engine: AgentGenerator) -> None:
    idea = IdeaRequest(
        idea="An AI agent that analyzes GitHub repositories for risks",
        quality_level=QualityLevel.STARTER,
    )
    candidates = engine.generate_blueprint_candidates(idea)
    starter = next(c for c in candidates if c.quality_level == QualityLevel.STARTER)
    blueprint = engine.generate_controlled_blueprint(idea, candidate_id=starter.candidate_id)
    assert blueprint.stack.database == "sqlite"


def test_template_blueprint_validates_against_definitions_schema(engine: AgentGenerator) -> None:
    jsonschema = pytest.importorskip("jsonschema")
    import json
    from pathlib import Path

    schema_path = (
        Path(__file__).resolve().parents[1]
        / "contracts"
        / "schemas"
        / "matrix-blueprint.schema.json"
    )
    schema = json.loads(schema_path.read_text())
    idea = IdeaRequest(idea="An AI agent that analyzes GitHub repositories for risks")
    blueprint = engine.generate_controlled_blueprint(idea)
    jsonschema.validate(instance=blueprint.to_definitions_dict(), schema=schema)
