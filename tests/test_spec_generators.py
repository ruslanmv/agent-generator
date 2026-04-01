"""Test that generators work directly from ProjectSpec (no Workflow adapter)."""
from agent_generator.domain.project_spec import ProjectSpec, FrameworkChoice, ArtifactMode, AgentSpec, TaskSpec, LLMSpec
from agent_generator.config import get_settings_lenient
from agent_generator.frameworks import FRAMEWORKS


def _make_spec(framework: str) -> ProjectSpec:
    return ProjectSpec(
        name="test-project",
        description="A test project",
        framework=FrameworkChoice(framework),
        artifact_mode=ArtifactMode.CODE_ONLY,
        llm=LLMSpec(provider="watsonx"),
        agents=[
            AgentSpec(id="agent_1", role="Assistant", goal="Help users", backstory="Expert"),
        ],
        tasks=[
            TaskSpec(id="task_1", description="Greet the user", agent_id="agent_1", expected_output="A greeting"),
            TaskSpec(id="task_2", description="Answer questions", agent_id="agent_1", expected_output="An answer", depends_on=["task_1"]),
        ],
    )


def test_crewai_from_spec():
    import ast
    spec = _make_spec("crewai")
    gen = FRAMEWORKS["crewai"]()
    code = gen.generate_from_spec(spec, get_settings_lenient())
    assert "CrewAgent" in code or "Agent" in code
    ast.parse(code)


def test_langgraph_from_spec():
    spec = _make_spec("langgraph")
    gen = FRAMEWORKS["langgraph"]()
    code = gen.generate_from_spec(spec, get_settings_lenient())
    assert "StateGraph" in code
    assert len(code) > 100  # non-trivial output


def test_watsonx_from_spec():
    spec = _make_spec("watsonx_orchestrate")
    gen = FRAMEWORKS["watsonx_orchestrate"]()
    code = gen.generate_from_spec(spec, get_settings_lenient())
    assert "spec_version" in code or "kind" in code


def test_react_from_spec():
    spec = _make_spec("react")
    gen = FRAMEWORKS["react"]()
    code = gen.generate_from_spec(spec, get_settings_lenient())
    assert "react_loop" in code
    assert len(code) > 100  # non-trivial output


def test_crewai_flow_from_spec():
    spec = _make_spec("crewai_flow")
    gen = FRAMEWORKS["crewai_flow"]()
    code = gen.generate_from_spec(spec, get_settings_lenient())
    assert "Flow" in code
    assert len(code) > 100  # non-trivial output


def test_build_uses_spec_not_workflow():
    """Verify build_service no longer imports Workflow directly."""
    import inspect
    from agent_generator.application import build_service
    source = inspect.getsource(build_service)
    assert "_spec_to_workflow" not in source, "build_service still contains legacy _spec_to_workflow adapter"
