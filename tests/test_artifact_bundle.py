"""Tests for ArtifactBundle and build pipeline."""

from agent_generator.application.build_service import build, build_dict
from agent_generator.application.planning_service import plan
from agent_generator.domain.artifact_bundle import ArtifactBundle, GeneratedFile


def test_build_returns_artifact_bundle():
    spec, _ = plan("Build a research assistant", framework="langgraph")
    artifact = build(spec)
    assert isinstance(artifact, ArtifactBundle)
    assert artifact.files
    assert artifact.manifest["framework"] == "langgraph"


def test_build_dict_backward_compatible():
    spec, _ = plan("Build a research team", framework="crewai")
    result = build_dict(spec)
    assert isinstance(result, dict)
    assert "files" in result
    assert "diagram" in result
    assert "framework" in result
    assert isinstance(result["files"], dict)


def test_artifact_bundle_valid_property():
    bundle = ArtifactBundle(files=[GeneratedFile(path="a.py", content="x=1")])
    assert bundle.valid is True


def test_all_frameworks_produce_bundles():
    for fw in ("crewai", "langgraph", "watsonx_orchestrate", "react", "crewai_flow"):
        spec, _ = plan(f"Hello world {fw} agent", framework=fw)
        artifact = build(spec)
        assert artifact.files, f"{fw} produced no files"
        assert artifact.manifest.get("generator_version") == "0.2.1"
        assert artifact.manifest.get("framework") == fw
