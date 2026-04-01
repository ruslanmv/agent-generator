"""Tests for CrewAI code generator."""

from agent_generator.frameworks.crewai.generator import CrewAIGenerator


def test_crewai_generates_valid_python(dummy_workflow, test_settings):
    gen = CrewAIGenerator()
    code = gen.generate_code(dummy_workflow, test_settings)
    assert "CrewAgent" in code
    assert "CrewTask" in code
    assert "Crew(" in code
    assert "def main()" in code
    assert "researcher" in code
    assert "writer" in code


def test_crewai_with_mcp_wrapper(dummy_workflow, test_settings):
    gen = CrewAIGenerator()
    code = gen.generate_code(dummy_workflow, test_settings, mcp=True)
    assert "FastAPI" in code
    assert "/invoke" in code
    assert "uvicorn" in code


def test_crewai_single_task(single_task_workflow, test_settings):
    gen = CrewAIGenerator()
    code = gen.generate_code(single_task_workflow, test_settings)
    assert "def main()" in code
    assert "crew.kickoff()" in code
