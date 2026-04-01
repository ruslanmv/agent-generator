"""Tests for LangGraph code generator."""

from agent_generator.frameworks.langgraph.generator import LangGraphGenerator


def test_langgraph_generates_valid_python(dummy_workflow, test_settings):
    gen = LangGraphGenerator()
    code = gen.generate_code(dummy_workflow, test_settings)
    assert "StateGraph" in code
    assert "WorkflowState" in code
    assert "TypedDict" in code
    assert "def build_graph()" in code
    assert "def main()" in code
    assert "START" in code


def test_langgraph_has_node_functions(dummy_workflow, test_settings):
    gen = LangGraphGenerator()
    code = gen.generate_code(dummy_workflow, test_settings)
    assert "def research_task(state" in code
    assert "def write_task(state" in code


def test_langgraph_with_mcp_wrapper(dummy_workflow, test_settings):
    gen = LangGraphGenerator()
    code = gen.generate_code(dummy_workflow, test_settings, mcp=True)
    assert "FastAPI" in code
    assert "/invoke" in code
