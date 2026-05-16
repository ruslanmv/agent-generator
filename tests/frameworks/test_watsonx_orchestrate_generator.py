"""Tests for WatsonX Orchestrate YAML generator."""

import yaml

from agent_generator.frameworks.watsonx_orchestrate.generator import WatsonXOrchestrateGenerator


def test_watsonx_generates_valid_yaml(dummy_workflow, test_settings):
    gen = WatsonXOrchestrateGenerator()
    code = gen.generate_code(dummy_workflow, test_settings)
    parsed = yaml.safe_load(code)
    assert parsed is not None
    assert "spec_version" in parsed
    assert "kind" in parsed
    assert "name" in parsed


def test_watsonx_no_mcp_wrapper(dummy_workflow, test_settings):
    gen = WatsonXOrchestrateGenerator()
    code = gen.generate_code(dummy_workflow, test_settings, mcp=True)
    # YAML generators should not get MCP wrapper
    assert "FastAPI" not in code
