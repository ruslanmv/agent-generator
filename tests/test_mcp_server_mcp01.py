"""MCP-01 — Matrix MCP server tools (local-first, deterministic, no secrets).

Covers tool registration, the GitPilot `.gitpilotrules` helper contract, and the
plan -> prompt -> check -> commit loop via the in-process tool handlers.
"""

from __future__ import annotations

import json

from agent_generator import mcp_server as mcp

GOAL = "A GitHub repo intelligence agent"
REQUIRED_TOOLS = {
    "matrix_plan_batch",
    "matrix_prompt",
    "matrix_check",
    "matrix_repair",
    "matrix_commit",
    "matrix_publish",
}


def _plan(project: str, goal: str = GOAL) -> dict:
    return mcp.tool_plan_batch(project_path=project, goal=goal, coder="gitpilot")


def test_tool_registration() -> None:
    names = {t["name"] for t in mcp.list_tools()}
    assert REQUIRED_TOOLS.issubset(names)
    # every tool advertises a JSON-schema input with project_path
    for t in mcp.list_tools():
        assert "project_path" in t["inputSchema"]["properties"]


def test_gitpilot_prompt_emits_gitpilotrules(tmp_path) -> None:
    proj = str(tmp_path)
    _plan(proj)
    res = mcp.tool_prompt(project_path=proj, coder="gitpilot")
    assert res["status"] == "ok" and res["coder"] == "gitpilot"
    assert res["rules_path"] == ".gitpilotrules"
    assert (tmp_path / ".gitpilotrules").exists()
    # GitPilot must NOT depend on MATRIX_INSTRUCTIONS.md
    assert not (tmp_path / "MATRIX_INSTRUCTIONS.md").exists()
    assert any(h["path"] == ".gitpilotrules" for h in res["helper_files"])


def test_mcp_prompt_tool_response_shape(tmp_path) -> None:
    proj = str(tmp_path)
    _plan(proj)
    res = mcp.call_tool("matrix_prompt", {"project_path": proj, "coder": "gitpilot"})
    assert res["coder"] == "gitpilot"
    assert res["rules_path"] == ".gitpilotrules"
    assert ".gitpilotrules" in res["note"]
    assert isinstance(res["prompt"], str) and len(res["prompt"]) > 50
    assert res["helper_files"] and res["next_tool"] == "matrix_check"


def test_mcp_check_is_structured(tmp_path) -> None:
    proj = str(tmp_path)
    _plan(proj)
    mcp.tool_prompt(project_path=proj, coder="gitpilot")
    res = mcp.call_tool(
        "matrix_check",
        {
            "project_path": proj,
            "changed_files": ["backend/app/api/routes.py", "backend/tests/test_routes.py"],
        },
    )
    assert res["status"] in {"passed", "needs_repair", "rejected"}
    assert res["exit_code"] in {0, 1, 2}
    assert isinstance(res["issues"], list)
    assert res["files_checked"] == ["backend/app/api/routes.py", "backend/tests/test_routes.py"]


def test_mcp_check_rejects_control_file(tmp_path) -> None:
    proj = str(tmp_path)
    _plan(proj)
    res = mcp.call_tool(
        "matrix_check", {"project_path": proj, "changed_files": ["MATRIX_STANDARDS.lock"]}
    )
    assert res["status"] == "rejected" and res["exit_code"] == 2
    assert res["next_tool"] == "matrix_repair"
    assert res["issues"]


def test_mcp_commit_writes_matrix_record(tmp_path) -> None:
    proj = str(tmp_path)
    _plan(proj)
    mcp.tool_prompt(project_path=proj, coder="gitpilot")
    check = mcp.tool_check(project_path=proj, changed_files=["backend/app/api/routes.py"])
    assert check["status"] == "passed", check
    res = mcp.tool_commit(
        project_path=proj,
        coder="gitpilot",
        provider="ollama",
        model="qwen2.5-coder:0.5b",
        files_changed=["backend/app/api/routes.py"],
    )
    assert res["status"] == "ok" and res["matrix_commit_id"]
    record_path = tmp_path / ".matrix" / "commits" / "001.json"
    assert record_path.exists()
    record = json.loads(record_path.read_text())
    assert record["coder"] == "gitpilot"
    assert record["batch"] and record["status"] == "approved"
    assert record["files_changed"] == ["backend/app/api/routes.py"]
    assert record["provider"] == "ollama" and record["model"] == "qwen2.5-coder:0.5b"


def test_mcp_repair_returns_bounded_prompt(tmp_path) -> None:
    proj = str(tmp_path)
    _plan(proj)
    mcp.tool_prompt(project_path=proj, coder="gitpilot")
    mcp.tool_check(project_path=proj, changed_files=["MATRIX_STANDARDS.lock"])  # fails
    res = mcp.call_tool("matrix_repair", {"project_path": proj, "coder": "gitpilot"})
    assert res["status"] == "ok" and res["coder"] == "gitpilot"
    assert isinstance(res["repair_prompt"], str) and res["repair_prompt"]
    assert res["next_tool"] == "matrix_check"
    assert any(h["path"] == ".gitpilotrules" for h in res["helper_files"])


def test_publish_defaults_to_dry_run(tmp_path) -> None:
    proj = str(tmp_path)
    _plan(proj)
    res = mcp.call_tool("matrix_publish", {"project_path": proj})
    assert res["dry_run"] is True and res["status"] == "ok"
    blocked = mcp.call_tool("matrix_publish", {"project_path": proj, "dry_run": False})
    assert blocked["status"] == "error" and blocked["dry_run"] is False


def test_no_production_secrets_required(tmp_path, monkeypatch) -> None:
    for var in (
        "DATABASE_URL",
        "MIGRATION_DATABASE_URL",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "WATSONX_API_KEY",
        "GITHUB_TOKEN",
        "MATRIXHUB_TOKEN",
        "MB_JWT_SECRET",
    ):
        monkeypatch.delenv(var, raising=False)
    proj = str(tmp_path)
    assert _plan(proj)["status"] == "ok"
    assert mcp.tool_prompt(project_path=proj, coder="gitpilot")["status"] == "ok"
    assert mcp.tool_check(project_path=proj, changed_files=["backend/app/x.py"])["status"] in {
        "passed",
        "needs_repair",
        "rejected",
    }
