"""Batch 0 baseline — freeze the pre-upgrade public surface.

These assertions are the compatibility promise for existing users: the engine upgrade is
*additive*. If one of these breaks, a change removed or altered behavior that downstream
users (and the existing CLI/web app) depend on. Update intentionally, never casually.
"""

from __future__ import annotations

import agent_generator

# The package version is frozen so an accidental bump is caught in review. Update this
# deliberately as part of a release. 0.2.0 = standards loader (Batch 3); 0.3.0 = strict
# Matrix Bundle exporter (Batch 6), completing milestone M2 (real generation).
EXPECTED_VERSION = "0.2.0"

# The five generation frameworks the README and users rely on.
EXPECTED_FRAMEWORKS = {
    "crewai",
    "crewai_flow",
    "langgraph",
    "react",
    "watsonx_orchestrate",
}


def test_version_is_frozen() -> None:
    assert agent_generator.__version__ == EXPECTED_VERSION


def test_legacy_public_exports_present() -> None:
    for name in ("Settings", "get_settings", "FRAMEWORKS", "PROVIDERS"):
        assert hasattr(agent_generator, name), f"missing legacy export: {name}"


def test_framework_registry_unchanged() -> None:
    assert EXPECTED_FRAMEWORKS.issubset(set(agent_generator.FRAMEWORKS.keys()))


def test_provider_registry_has_watsonx() -> None:
    # watsonx is the default provider; openai/ollabridge are optional extras.
    assert "watsonx" in agent_generator.PROVIDERS


def test_legacy_application_entrypoints_importable() -> None:
    from agent_generator.application.build_service import build_dict
    from agent_generator.application.planning_service import plan

    assert callable(plan)
    assert callable(build_dict)


def test_engine_facade_is_additive() -> None:
    # The new engine must be importable but must not have displaced anything above.
    from agent_generator import AgentGenerator
    from agent_generator.engine import AgentGenerator as EngineAgentGenerator

    assert AgentGenerator is EngineAgentGenerator
