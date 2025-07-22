"""
Unit tests for the core Pydantic models (Agent, Task, Workflow).
"""

from agent_generator.models.agent import Agent, LLMConfig, Tool
from agent_generator.models.task import Task
from agent_generator.models.workflow import Workflow, WorkflowEdge


def test_model_roundtrip():
    """Dumping → loading should preserve equality."""
    agent = Agent(
        id="agent_a",
        role="research assistant",
        tools=[Tool(name="search")],
        llm=LLMConfig(model="meta-llama-3-70b-instruct"),
    )

    tasks = [
        Task(id="t1", goal="Research the market", agent_id=agent.id),
        Task(id="t2", goal="Summarise findings", agent_id=agent.id),
    ]
    edges = [WorkflowEdge(source="t1", target="t2")]

    wf = Workflow(agents=[agent], tasks=tasks, edges=edges)
    dumped = wf.model_dump()
    wf2 = Workflow.model_validate(dumped)

    assert wf2 == wf
    assert wf2.predecessors("t2")[0].id == "t1"
    assert wf2.successors("t1")[0].id == "t2"


def test_edge_validation():
    """Unknown task IDs referenced in edges should raise."""
    agent = Agent(id="a", role="x")
    task = Task(id="t", goal="y", agent_id="a")

    try:
        Workflow(
            agents=[agent],
            tasks=[task],
            edges=[WorkflowEdge(source="t", target="does_not_exist")],
        )
    except ValueError as exc:
        assert "unknown task id" in str(exc).lower()
    else:  # pragma: no cover
        raise AssertionError("Edge validation did not fail")
