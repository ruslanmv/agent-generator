"""Shared test fixtures for agent-generator."""

from __future__ import annotations

import os

import pytest

from agent_generator.models.agent import Agent, LLMConfig, Tool
from agent_generator.models.task import Task
from agent_generator.models.workflow import Workflow, WorkflowEdge


# Ensure tests don't require real credentials
@pytest.fixture(autouse=True)
def _mock_env(monkeypatch):
    """Set minimal env vars so Settings can be constructed in dry-run mode."""
    monkeypatch.setenv("WATSONX_API_KEY", "test-key")
    monkeypatch.setenv("WATSONX_PROJECT_ID", "test-project")
    monkeypatch.setenv("AGENTGEN_PROVIDER", "watsonx")
    # Clear the lru_cache so Settings picks up the monkeypatched env
    from agent_generator.config import get_settings
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def test_settings():
    """Create a Settings instance with test credentials."""
    from agent_generator.config import Settings
    return Settings(
        provider="watsonx",
        watsonx_api_key="test-key",
        watsonx_project_id="test-project",
    )


@pytest.fixture
def dummy_workflow() -> Workflow:
    """A minimal two-task sequential workflow for testing."""
    agent = Agent(
        id="researcher",
        role="Researcher",
        tools=[Tool(name="web_search", description="Search the web")],
        llm=LLMConfig(model="meta-llama/llama-3-3-70b-instruct"),
    )
    writer = Agent(
        id="writer",
        role="Writer",
        tools=[],
        llm=LLMConfig(model="meta-llama/llama-3-3-70b-instruct"),
    )
    task1 = Task(
        id="research_task",
        goal="Research the given topic thoroughly",
        inputs=[],
        outputs=["research_data"],
        agent_id="researcher",
    )
    task2 = Task(
        id="write_task",
        goal="Write a comprehensive report based on findings",
        inputs=["research_data"],
        outputs=["report"],
        agent_id="writer",
    )
    edge = WorkflowEdge(source="research_task", target="write_task")
    return Workflow(agents=[agent, writer], tasks=[task1, task2], edges=[edge])


@pytest.fixture
def single_task_workflow() -> Workflow:
    """A minimal single-task workflow for testing."""
    agent = Agent(
        id="assistant",
        role="Assistant",
        tools=[],
        llm=LLMConfig(model="meta-llama/llama-3-3-70b-instruct"),
    )
    task = Task(
        id="main_task",
        goal="Complete the assigned objective",
        agent_id="assistant",
    )
    return Workflow(agents=[agent], tasks=[task], edges=[])
