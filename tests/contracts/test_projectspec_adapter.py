"""Back-compat adapter tests: legacy ProjectSpec <-> Matrix contracts."""

from __future__ import annotations

import re

from agent_generator.contracts import IdeaRequest
from agent_generator.contracts.projectspec_adapter import (
    idea_to_project_spec,
    project_spec_to_stack,
    project_spec_to_tasks,
)
from agent_generator.domain.project_spec import ProjectSpec

_TASK_ID = re.compile(r"^TASK-[0-9]{3}$")


def test_idea_to_project_spec_returns_validated_spec() -> None:
    idea = IdeaRequest(idea="Build a research team that summarizes documents and answers questions")
    spec, warnings = idea_to_project_spec(idea)
    assert isinstance(spec, ProjectSpec)
    assert spec.name
    assert isinstance(warnings, list)


def test_project_spec_to_tasks_uses_contract_task_ids() -> None:
    idea = IdeaRequest(idea="Build a research team that summarizes documents and answers questions")
    spec, _ = idea_to_project_spec(idea)
    tasks = project_spec_to_tasks(spec)
    assert tasks, "expected at least one task"
    for task in tasks:
        assert _TASK_ID.match(task.task_id), task.task_id
        assert task.allowed_files


def test_project_spec_to_stack_maps_framework() -> None:
    idea = IdeaRequest(idea="Build a crewai social media team that drafts and schedules posts")
    spec, _ = idea_to_project_spec(idea)
    stack = project_spec_to_stack(spec, database="postgresql", auth="session")
    assert stack.database == "postgresql"
    assert stack.auth == "session"
    assert stack.backend
