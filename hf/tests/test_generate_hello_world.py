"""
Unit tests: generate a 'hello world' project for each framework.

Verifies that every framework produces valid, non-empty files
and that Python files pass AST parsing.
"""
import ast
import sys
from pathlib import Path

import yaml

# Add the hf/app directory to the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from generator import generate_project


FRAMEWORKS = ["crewai", "langgraph", "watsonx_orchestrate", "react", "crewai_flow"]

HELLO_PROMPT = "Build a simple hello-world agent that greets the user and responds to questions."


def _validate_python(code: str, filepath: str):
    """Assert the code is valid Python."""
    try:
        ast.parse(code, filename=filepath)
    except SyntaxError as exc:
        raise AssertionError(f"{filepath}: SyntaxError at line {exc.lineno}: {exc.msg}") from exc


def _validate_yaml(content: str, filepath: str):
    """Assert the content is valid YAML."""
    try:
        data = yaml.safe_load(content)
        assert data is not None, f"{filepath}: YAML parsed as None"
    except yaml.YAMLError as exc:
        raise AssertionError(f"{filepath}: YAML error: {exc}") from exc


# ── Per-framework tests ─────────────────────────────────────────


def test_crewai_hello_world():
    plan, files = generate_project(HELLO_PROMPT, "crewai", "code_and_yaml")
    assert plan["framework"] == "crewai"
    assert len(files) >= 4, f"Expected >=4 files, got {len(files)}: {list(files.keys())}"

    # Must have YAML configs
    yaml_files = [f for f in files if f.endswith((".yaml", ".yml"))]
    assert yaml_files, "CrewAI code_and_yaml should produce YAML files"

    # Validate all files
    for path, content in files.items():
        assert content.strip(), f"{path} is empty"
        if path.endswith(".py"):
            _validate_python(content, path)
        elif path.endswith((".yaml", ".yml")):
            _validate_yaml(content, path)


def test_langgraph_hello_world():
    plan, files = generate_project(HELLO_PROMPT, "langgraph", "code_only")
    assert plan["framework"] == "langgraph"
    assert len(files) >= 2

    py_files = [f for f in files if f.endswith(".py")]
    assert py_files, "LangGraph should produce Python files"

    for path, content in files.items():
        assert content.strip(), f"{path} is empty"
        if path.endswith(".py"):
            _validate_python(content, path)


def test_watsonx_hello_world():
    plan, files = generate_project(HELLO_PROMPT, "watsonx_orchestrate", "yaml_only")
    assert plan["framework"] == "watsonx_orchestrate"
    assert len(files) >= 1

    yaml_files = [f for f in files if f.endswith((".yaml", ".yml"))]
    assert yaml_files, "WatsonX should produce YAML files"

    for path, content in files.items():
        assert content.strip(), f"{path} is empty"
        if path.endswith((".yaml", ".yml")):
            _validate_yaml(content, path)


def test_react_hello_world():
    plan, files = generate_project(HELLO_PROMPT, "react", "code_only")
    assert plan["framework"] == "react"
    assert len(files) >= 2

    for path, content in files.items():
        assert content.strip(), f"{path} is empty"
        if path.endswith(".py"):
            _validate_python(content, path)


def test_crewai_flow_hello_world():
    plan, files = generate_project(HELLO_PROMPT, "crewai_flow", "code_only")
    assert plan["framework"] == "crewai_flow"
    assert len(files) >= 2

    for path, content in files.items():
        assert content.strip(), f"{path} is empty"
        if path.endswith(".py"):
            _validate_python(content, path)


# ── Cross-framework tests ───────────────────────────────────────


def test_all_frameworks_produce_readme():
    for fw in FRAMEWORKS:
        _, files = generate_project(HELLO_PROMPT, fw)
        readme = [f for f in files if f.lower() == "readme.md"]
        assert readme, f"{fw} should produce a README.md"


def test_all_frameworks_produce_nonempty():
    for fw in FRAMEWORKS:
        _, files = generate_project(HELLO_PROMPT, fw)
        assert len(files) >= 1, f"{fw} produced no files"
        for path, content in files.items():
            assert len(content) > 10, f"{fw}/{path} is too short ({len(content)} chars)"


def test_plan_detects_framework():
    """Verify framework detection from prompt keywords."""
    from generator import plan_project

    plan = plan_project("Build a LangGraph state machine pipeline")
    assert plan["framework"] == "langgraph"

    plan = plan_project("Create a WatsonX Orchestrate assistant")
    assert plan["framework"] == "watsonx_orchestrate"

    plan = plan_project("Build a CrewAI multi-agent research team")
    assert plan["framework"] == "crewai"
