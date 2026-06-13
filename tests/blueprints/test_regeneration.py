"""Batch 5 — versioned regeneration (the "Update requirements" engine capability)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from agent_generator.blueprints.regeneration import bump_version
from agent_generator.contracts import ChangeType, IdeaRequest, RegenerationResult
from agent_generator.engine import AgentGenerator

FIXED_NOW = datetime(2026, 6, 12, 14, 0, 0, tzinfo=timezone.utc)


@pytest.fixture()
def engine() -> AgentGenerator:
    return AgentGenerator(fixed_now=FIXED_NOW)


@pytest.fixture()
def base(engine: AgentGenerator):
    idea = IdeaRequest(idea="An AI agent that analyzes GitHub repositories for risks")
    return engine.generate_controlled_blueprint(idea)


@pytest.mark.parametrize(
    ("change_type", "expected"),
    [
        (ChangeType.SMALL_UPDATE, "1.0.1"),
        (ChangeType.ADD_FEATURE, "1.1.0"),
        (ChangeType.CHANGE_ARCHITECTURE, "2.0.0"),
    ],
)
def test_version_bump(change_type: ChangeType, expected: str) -> None:
    assert bump_version("1.0.0", change_type) == expected


def test_bump_tolerates_v_prefix() -> None:
    assert bump_version("v1.2.3", ChangeType.ADD_FEATURE) == "1.3.0"


def test_add_feature_produces_new_version_without_mutating_base(
    engine: AgentGenerator, base
) -> None:
    base_task_count = len(base.tasks)
    base_id = base.blueprint_id

    result = engine.regenerate(
        base,
        "Add authentication, a user dashboard, and protected API routes. Keep FastAPI.",
        ChangeType.ADD_FEATURE,
        current_version="1.0.0",
    )
    assert isinstance(result, RegenerationResult)
    assert result.version == "1.1.0"
    assert result.previous_version == "1.0.0"

    # Base is untouched (pure function).
    assert base.blueprint_id == base_id
    assert len(base.tasks) == base_task_count

    new = result.blueprint
    assert new.blueprint_id != base.blueprint_id
    assert new.slug == base.slug  # same project
    assert len(new.tasks) > base_task_count
    assert new.stack.auth == "session"
    assert "/dashboard" in new.pages
    assert "Add authentication" in result.change_summary
    assert "Update prompt pack" in result.change_summary


def test_add_feature_appends_auth_task_and_routes(engine: AgentGenerator, base) -> None:
    result = engine.regenerate(base, "Add user login", ChangeType.ADD_FEATURE)
    titles = [t.title for t in result.blueprint.tasks]
    assert any("authentication" in t.lower() for t in titles)
    routes = {(r.method, r.path) for r in result.blueprint.api_routes}
    assert ("POST", "/api/v1/auth/login") in routes


def test_small_update_bumps_patch(engine: AgentGenerator, base) -> None:
    result = engine.regenerate(base, "Tweak the report wording", ChangeType.SMALL_UPDATE)
    assert result.version == "1.0.1"
    assert len(result.blueprint.tasks) == len(base.tasks) + 1


def test_change_architecture_swaps_database(engine: AgentGenerator, base) -> None:
    result = engine.regenerate(
        base,
        "Switch the database to MongoDB for flexible documents",
        ChangeType.CHANGE_ARCHITECTURE,
    )
    assert result.version == "2.0.0"
    assert result.blueprint.stack.database == "mongodb"
    assert "Switch database to mongodb" in result.change_summary


def test_regenerate_accepts_string_change_type(engine: AgentGenerator, base) -> None:
    result = engine.regenerate(base, "Add tests", "add-feature")
    assert result.version == "1.1.0"


def test_regeneration_is_deterministic(base) -> None:
    a = AgentGenerator(fixed_now=FIXED_NOW).regenerate(base, "Add login", ChangeType.ADD_FEATURE)
    b = AgentGenerator(fixed_now=FIXED_NOW).regenerate(base, "Add login", ChangeType.ADD_FEATURE)
    assert a.blueprint.model_dump() == b.blueprint.model_dump()
