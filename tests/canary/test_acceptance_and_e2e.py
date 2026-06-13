"""Canary: the v1.0.0 acceptance script, the CLI flow, and matrix-builder e2e."""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from agent_generator.engine import AgentGenerator

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXED_NOW = datetime(2026, 6, 12, 14, 0, 0, tzinfo=timezone.utc)
IDEA_TEXT = "An AI agent that analyzes GitHub repositories for risks"


# --- Python acceptance script ----------------------------------------------


def test_python_acceptance_script_passes() -> None:
    from scripts.acceptance import run  # type: ignore

    assert run() == 0


def _add_scripts_to_path() -> None:
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))


_add_scripts_to_path()


# --- CLI acceptance flow ---------------------------------------------------


def _cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "agent_generator.cli", *args],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )


def test_cli_matrix_flow(tmp_path) -> None:
    # candidates
    out = _cli("matrix", "candidates", "--idea", IDEA_TEXT)
    assert out.returncode == 0
    assert "Standard Matrix Bundle" in out.stdout

    # generate -> directory
    repo = tmp_path / "gen"
    out = _cli("matrix", "generate", "--idea", IDEA_TEXT, "--out", str(repo))
    assert out.returncode == 0
    assert (repo / "MATRIX_BLUEPRINT.yaml").exists()

    # validate the generated dir -> approved (exit 0)
    out = _cli("matrix", "validate", "--idea", IDEA_TEXT, "--repo", str(repo))
    assert out.returncode == 0, out.stdout + out.stderr
    assert "approved" in out.stdout

    # tamper a forbidden file -> rejected (exit 2)
    (repo / "MATRIX_STANDARDS.lock").write_text("tampered: true\n")
    out = _cli("matrix", "validate", "--idea", IDEA_TEXT, "--repo", str(repo))
    assert out.returncode == 2
    assert "rejected" in out.stdout


# --- matrix-builder e2e: HTTP mode -----------------------------------------


def test_matrix_builder_http_mode_e2e() -> None:
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from agent_generator.http.app import create_app

    client = TestClient(create_app(AgentGenerator(fixed_now=FIXED_NOW)))
    idea = {"idea": IDEA_TEXT}
    bp = client.post("/api/v1/blueprints", json={"idea_request": idea}).json()
    bundle = client.post("/api/v1/bundles", json={"blueprint": bp}).json()
    assert bundle["file_count"] > 0
    val = client.post(
        "/api/v1/validations",
        json={"blueprint": bp, "request": {"changed_files": [{"path": "MATRIX_BLUEPRINT.yaml"}]}},
    ).json()
    assert val["status"] == "rejected"


# --- matrix-builder e2e: SDK mode (through the real adapter) ----------------


def _matrix_builder_api_dir() -> Path | None:
    env = os.environ.get("MATRIX_BUILDER_API_DIR")
    candidates = [Path(env)] if env else []
    candidates.append(REPO_ROOT.parent / "matrix-builder" / "services" / "api")
    for path in candidates:
        if (path / "app" / "integrations" / "agent_generator_adapter.py").exists():
            return path
    return None


def test_matrix_builder_sdk_mode_e2e() -> None:
    api_dir = _matrix_builder_api_dir()
    if api_dir is None:
        pytest.skip("matrix-builder source not available")
    if str(api_dir) not in sys.path:
        sys.path.insert(0, str(api_dir))

    from app.integrations.agent_generator_adapter import AgentGeneratorAdapter  # type: ignore
    from app.schemas.idea import IdeaRequest as MBIdea  # type: ignore

    adapter = AgentGeneratorAdapter(mode="sdk")
    assert adapter.status()["status"] == "connected"

    req = MBIdea(idea=IDEA_TEXT)
    intent = adapter.parse_idea(req)
    assert intent.normalized_idea
    candidates = adapter.generate_blueprint_candidates(req)
    assert len(candidates) == 3
    blueprint = adapter.generate_controlled_blueprint(req)
    bundle = adapter.generate_matrix_bundle(blueprint)
    assert bundle.file_count > 0
    prompt = adapter.generate_coder_prompt(bundle.bundle_id, "claude-code")
    assert "MATRIX_STATUS" in prompt.prompt
    report = adapter.validate_bundle(bundle.bundle_id)
    assert report.status is not None
