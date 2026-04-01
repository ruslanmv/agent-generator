"""Tests for core data models."""

import pytest
from pydantic import ValidationError

from agent_generator.models.agent import Agent, LLMConfig, Tool
from agent_generator.models.task import Task
from agent_generator.models.workflow import Workflow, WorkflowEdge


class TestLLMConfig:
    def test_defaults(self):
        cfg = LLMConfig(model="test-model")
        assert cfg.provider == "watsonx"
        assert cfg.temperature == 0.7
        assert cfg.max_tokens == 4096

    def test_strips_model_whitespace(self):
        cfg = LLMConfig(model="  test-model  ")
        assert cfg.model == "test-model"

    def test_temperature_bounds(self):
        with pytest.raises(ValidationError):
            LLMConfig(model="m", temperature=3.0)


class TestTool:
    def test_basic_tool(self):
        t = Tool(name="search", description="Search web")
        assert t.name == "search"
        assert t.endpoint is None


class TestAgent:
    def test_agent_creation(self):
        a = Agent(id="a1", role="Researcher", llm=LLMConfig(model="m"))
        assert a.id == "a1"
        assert a.tools == []

    def test_agent_with_tools(self):
        a = Agent(
            id="a1",
            role="Researcher",
            tools=[Tool(name="search")],
            llm=LLMConfig(model="m"),
        )
        assert len(a.tools) == 1


class TestTask:
    def test_task_creation(self):
        t = Task(id="t1", goal="Do something")
        assert t.agent_id is None
        assert t.inputs == []

    def test_task_strips_whitespace(self):
        t = Task(id="  t1  ", goal="  goal  ")
        assert t.id == "t1"
        assert t.goal == "goal"


class TestWorkflow:
    def test_valid_workflow(self, dummy_workflow):
        assert len(dummy_workflow.agents) == 2
        assert len(dummy_workflow.tasks) == 2
        assert len(dummy_workflow.edges) == 1

    def test_get_task(self, dummy_workflow):
        t = dummy_workflow.get_task("research_task")
        assert t.goal == "Research the given topic thoroughly"

    def test_predecessors(self, dummy_workflow):
        preds = dummy_workflow.predecessors("write_task")
        assert len(preds) == 1
        assert preds[0].id == "research_task"

    def test_successors(self, dummy_workflow):
        succs = dummy_workflow.successors("research_task")
        assert len(succs) == 1
        assert succs[0].id == "write_task"

    def test_invalid_edge(self):
        agent = Agent(id="a1", role="R", llm=LLMConfig(model="m"))
        task = Task(id="t1", goal="G")
        with pytest.raises(ValidationError, match="unknown task"):
            Workflow(
                agents=[agent],
                tasks=[task],
                edges=[WorkflowEdge(source="t1", target="nonexistent")],
            )
