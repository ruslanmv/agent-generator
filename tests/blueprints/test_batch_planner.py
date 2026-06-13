"""Batch E1 — batch planner: scoped batches and repair batches."""

from __future__ import annotations

import re
from datetime import datetime, timezone

import pytest

from agent_generator.contracts import (
    BatchChangeType,
    BatchPlan,
    ChangedFile,
    IdeaRequest,
    ValidationRequest,
)
from agent_generator.engine import AgentGenerator

FIXED_NOW = datetime(2026, 6, 12, 14, 0, 0, tzinfo=timezone.utc)
_TASK_ID = re.compile(r"^TASK-[0-9]{3}$")


@pytest.fixture()
def engine() -> AgentGenerator:
    return AgentGenerator(fixed_now=FIXED_NOW)


@pytest.fixture()
def blueprint(engine: AgentGenerator):
    return engine.generate_controlled_blueprint(
        IdeaRequest(idea="An AI agent that analyzes GitHub repositories for risks")
    )


def test_plan_batch_appends_scoped_tasks(engine: AgentGenerator, blueprint) -> None:
    base_tasks = len(blueprint.tasks)
    plan = engine.plan_batch(blueprint, "Add authentication and a dashboard", "add-feature")
    assert isinstance(plan, BatchPlan)
    assert plan.batch_id.startswith("bat-")
    assert plan.change_type == BatchChangeType.ADD_FEATURE
    assert plan.tasks, "a batch produces at least one task"
    for task in plan.tasks:
        assert _TASK_ID.match(task.task_id)
    # Task numbering continues after the blueprint's existing tasks.
    first_no = int(plan.tasks[0].task_id.split("-")[1])
    assert first_no == base_tasks + 1
    assert plan.allowed_files
    assert "Add authentication" in plan.change_summary


def test_plan_batch_does_not_mutate_blueprint_or_bump_version(
    engine: AgentGenerator, blueprint
) -> None:
    before_id = blueprint.blueprint_id
    before_tasks = len(blueprint.tasks)
    plan = engine.plan_batch(blueprint, "Add tests", "small-update")
    # Blueprint is untouched; the plan only references it.
    assert blueprint.blueprint_id == before_id
    assert len(blueprint.tasks) == before_tasks
    assert plan.blueprint_id == before_id
    # No version field anywhere — a batch is in-version.
    assert not hasattr(plan, "version")


def test_plan_batch_title_summarizes_goal(engine: AgentGenerator, blueprint) -> None:
    plan = engine.plan_batch(blueprint, "Add GitHub repository upload and analysis", "add-feature")
    assert plan.title.startswith("Add GitHub repository upload")


def test_plan_batch_is_deterministic(blueprint) -> None:
    a = AgentGenerator(fixed_now=FIXED_NOW).plan_batch(blueprint, "Add login", "add-feature")
    b = AgentGenerator(fixed_now=FIXED_NOW).plan_batch(blueprint, "Add login", "add-feature")
    assert a.model_dump() == b.model_dump()


def test_plan_batch_ordinal_is_carried(engine: AgentGenerator, blueprint) -> None:
    plan = engine.plan_batch(blueprint, "Add a worker", "add-feature", ordinal=3)
    assert plan.ordinal == 3


def test_plan_repair_batch_scopes_to_violating_files(engine: AgentGenerator, blueprint) -> None:
    # Produce a real failing report: a forbidden-file edit.
    req = ValidationRequest(changed_files=[ChangedFile(path="MATRIX_BLUEPRINT.yaml")])
    report = engine.validate_ai_coder_patch("b", request=req, blueprint=blueprint)
    assert report.status.value == "rejected"

    plan = engine.plan_repair_batch(report, blueprint=blueprint)
    assert plan.change_type == BatchChangeType.FIX_ISSUE
    assert plan.is_repair is True
    assert len(plan.tasks) == 1
    # The repair task's allowlist is exactly the violating files.
    assert plan.tasks[0].allowed_files == ["MATRIX_BLUEPRINT.yaml"]
    assert plan.goal_md  # carries the repair instructions


def test_plan_repair_batch_without_blueprint(engine: AgentGenerator, blueprint) -> None:
    req = ValidationRequest(changed_files=[ChangedFile(path="MATRIX_STANDARDS.lock")])
    report = engine.validate_ai_coder_patch("b", request=req, blueprint=blueprint)
    plan = engine.plan_repair_batch(report)  # no blueprint context
    assert plan.is_repair and plan.tasks[0].allowed_files == ["MATRIX_STANDARDS.lock"]


def test_plan_repair_batch_is_deterministic(engine: AgentGenerator, blueprint) -> None:
    req = ValidationRequest(changed_files=[ChangedFile(path="MATRIX_BLUEPRINT.yaml")])
    report = engine.validate_ai_coder_patch("b", request=req, blueprint=blueprint)
    a = engine.plan_repair_batch(report, blueprint=blueprint)
    b = engine.plan_repair_batch(report, blueprint=blueprint)
    assert a.batch_id == b.batch_id
