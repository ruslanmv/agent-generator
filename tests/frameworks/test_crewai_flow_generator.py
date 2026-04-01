"""Tests for CrewAI Flow generator."""

from agent_generator.frameworks.crewai_flow.generator import CrewAIFlowGenerator


def test_crewai_flow_generates_flow(dummy_workflow, test_settings):
    gen = CrewAIFlowGenerator()
    code = gen.generate_code(dummy_workflow, test_settings)
    assert "Flow" in code
    assert "@start()" in code
    assert "FlowState" in code
    assert "def main()" in code


def test_crewai_flow_has_steps(dummy_workflow, test_settings):
    gen = CrewAIFlowGenerator()
    code = gen.generate_code(dummy_workflow, test_settings)
    assert "def begin(self)" in code
