"""Tests for ReAct generator."""

from agent_generator.frameworks.react.generator import ReActGenerator


def test_react_generates_loop(dummy_workflow, test_settings):
    gen = ReActGenerator()
    code = gen.generate_code(dummy_workflow, test_settings)
    assert "def think(" in code
    assert "def act(" in code
    assert "react_loop" in code
    assert "def main()" in code
    assert "MAX_ITERATIONS" in code


def test_react_has_task_runners(dummy_workflow, test_settings):
    gen = ReActGenerator()
    code = gen.generate_code(dummy_workflow, test_settings)
    assert "run_research_task" in code
    assert "run_write_task" in code
