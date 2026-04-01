"""Integration tests for the spec-first planning + build pipeline."""
import ast
from agent_generator.application.planning_service import plan
from agent_generator.application.build_service import build_dict as build


def test_plan_returns_valid_spec():
    spec, warnings = plan("Build a research team with a researcher and writer")
    assert spec.name
    assert len(spec.agents) >= 1
    assert len(spec.tasks) >= 1
    assert spec.framework.value in ("crewai", "langgraph", "watsonx_orchestrate", "crewai_flow", "react")


def test_build_from_spec():
    spec, _ = plan("Build a research team", framework="crewai")
    result = build(spec)
    assert "files" in result
    assert len(result["files"]) >= 1
    # Check at least one Python file has valid syntax
    for path, content in result["files"].items():
        if path.endswith(".py") and len(content) > 20:
            ast.parse(content)


def test_all_frameworks_plan_and_build():
    for fw in ("crewai", "langgraph", "watsonx_orchestrate", "react", "crewai_flow"):
        spec, _ = plan(f"Build a hello world {fw} agent", framework=fw)
        assert spec.framework.value == fw
        result = build(spec)
        assert result["files"], f"{fw} produced no files"


def test_plan_detects_tools():
    spec, _ = plan("Build an agent that searches the web and reads PDF documents")
    tool_ids = [t.id for t in spec.tools]
    assert "web_search" in tool_ids or "pdf_reader" in tool_ids


def _has_raw_eval_call(source: str) -> bool:
    """Check if Python source contains a direct eval() call (not _safe_eval)."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id == "eval":
                return True
    return False


def test_build_produces_no_eval():
    """Ensure no generated code contains a raw eval() call."""
    for fw in ("crewai", "langgraph", "watsonx_orchestrate", "react", "crewai_flow"):
        spec, _ = plan(f"Simple {fw} agent", framework=fw)
        result = build(spec)
        for path, content in result["files"].items():
            if path.endswith(".py"):
                assert not _has_raw_eval_call(content), f"{fw}/{path} contains raw eval() call"
