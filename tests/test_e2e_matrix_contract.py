"""Deterministic slice of the local E2E (no Ollama, no GitPilot, no secrets).

Proves the acceptance criterion that does NOT need a live model: agent-generator receives the idea
"Create a simple Hello World website" and produces a Matrix-compatible contract/bundle that
matrix-builder can consume, and the matrix-builder loop (MCP tools) validates a Hello-World change
and records Matrix Commit #001. The GitPilot+Ollama coding step is exercised separately by
scripts/e2e/local_ollama_gitpilot_hello.sh (manual/local).

Flow proven here:
  idea -> agent-generator (blueprint + Matrix bundle) -> matrix-builder (Batch 01, validate, commit)
"""

from __future__ import annotations

import json

from agent_generator import mcp_server as mcp
from agent_generator.contracts import IdeaRequest
from agent_generator.engine import AgentGenerator

IDEA = "Create a simple Hello World website"
# A Hello-World page inside the Matrix allowlist (frontend/), so the change validates as approved.
HELLO_FILE = "frontend/index.html"


def test_agent_generator_produces_matrix_bundle_from_idea() -> None:
    """agent-generator = creates the project blueprint / Matrix contract (the required first step)."""
    engine = AgentGenerator()
    blueprint = engine.generate_controlled_blueprint(IdeaRequest(idea=IDEA))
    bundle = engine.compile_bundle(blueprint)
    files = bundle.file_map()
    # A Matrix-compatible contract/bundle matrix-builder can consume:
    assert "MATRIX_BLUEPRINT.yaml" in files
    assert "MATRIX_TASKS.md" in files
    assert "MATRIX_STANDARDS.lock" in files
    assert "frontend/" in blueprint.allowed_change_roots


def test_full_matrix_half_idea_to_commit(tmp_path) -> None:
    """idea -> contract -> Batch 01 -> validate -> Matrix Commit #001 (matrix-builder side)."""
    proj = str(tmp_path)

    # agent-generator turns the idea into the Matrix contract + Batch 01 (matrix_plan_batch
    # scaffolds the blueprint from the idea, i.e. agent-generator is NOT bypassed).
    plan = mcp.tool_plan_batch(project_path=proj, goal=IDEA, coder="gitpilot")
    assert plan["status"] == "ok" and plan["batch_number"] == 1

    # matrix-builder emits the GitPilot-native contract file.
    prompt = mcp.tool_prompt(project_path=proj, coder="gitpilot")
    assert prompt["rules_path"] == ".gitpilotrules"
    assert (tmp_path / ".gitpilotrules").exists()

    # GitPilot/Ollama would produce this; here we stand in for the coding step deterministically.
    (tmp_path / "frontend").mkdir(parents=True, exist_ok=True)
    (tmp_path / HELLO_FILE).write_text(
        "<!doctype html>\n<title>Hello</title>\n<h1>Hello Matrix</h1>\n", encoding="utf-8"
    )

    # matrix-builder validates the change against the contract (single authority).
    check = mcp.tool_check(project_path=proj, changed_files=[HELLO_FILE])
    assert check["status"] == "passed" and check["exit_code"] == 0, check

    # matrix-builder records Matrix Commit #001.
    commit = mcp.tool_commit(
        project_path=proj, coder="gitpilot", provider="ollama", model="qwen2.5-coder:0.5b",
        files_changed=[HELLO_FILE],
    )
    assert commit["status"] == "ok"
    record = json.loads((tmp_path / ".matrix" / "commits" / "001.json").read_text())
    assert record["status"] == "approved"
    assert record["files_changed"] == [HELLO_FILE]
    assert record["coder"] == "gitpilot" and record["provider"] == "ollama"

    # The Hello World artifact exists and says "Hello Matrix".
    assert "Hello Matrix" in (tmp_path / HELLO_FILE).read_text()
