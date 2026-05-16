"""Release build integration tests."""

from agent_generator.application.build_service import build
from agent_generator.application.planning_service import plan


def test_build_returns_valid_artifact_bundle():
    spec, _ = plan("build a research assistant", framework="langgraph")
    artifact = build(spec)
    assert artifact.files
    assert artifact.manifest["framework"] == "langgraph"
    assert artifact.manifest["generator_version"] == "0.2.1"
    assert artifact.manifest["template_tier"] == "production"


def test_all_frameworks_build_valid():
    for fw in ("crewai", "langgraph", "watsonx_orchestrate", "react", "crewai_flow"):
        spec, _ = plan(f"Build a {fw} hello world agent", framework=fw)
        artifact = build(spec)
        assert artifact.files, f"{fw} produced no files"
        assert artifact.manifest["generator_version"] == "0.2.1"
