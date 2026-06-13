"""Batch 9 — Matrix engine HTTP facade (thin SDK wrappers)."""

from __future__ import annotations

import zipfile
from datetime import datetime, timezone

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

from agent_generator.engine import AgentGenerator  # noqa: E402
from agent_generator.http.app import create_app  # noqa: E402

FIXED_NOW = datetime(2026, 6, 12, 14, 0, 0, tzinfo=timezone.utc)
IDEA = {"idea": "An AI agent that analyzes GitHub repositories for risks"}


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app(AgentGenerator(fixed_now=FIXED_NOW)))


def test_health(client: TestClient) -> None:
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["engine"] == "agent-generator"


def test_standards_current(client: TestClient) -> None:
    body = client.get("/api/v1/standards/current").json()
    assert body["version"] == "2026.06.0"
    assert body["compatibility"]["ok"] is True


def test_parse_idea(client: TestClient) -> None:
    body = client.post("/api/v1/ideas/parse", json=IDEA).json()
    assert body["build_type"] == "agent"
    assert "GitHub" in body["normalized_idea"]


def test_candidates(client: TestClient) -> None:
    body = client.post("/api/v1/blueprints/candidates", json=IDEA).json()
    assert len(body["candidates"]) == 3


def test_blueprint_and_bundle(client: TestClient) -> None:
    bp = client.post("/api/v1/blueprints", json={"idea_request": IDEA}).json()
    assert bp["slug"] == "github-repo-intelligence-agent"
    bundle = client.post("/api/v1/bundles", json={"blueprint": bp}).json()
    assert bundle["file_count"] > 0
    assert bundle["manifest_digest"].startswith("sha256:")


def test_prompt_endpoint(client: TestClient) -> None:
    bp = client.post("/api/v1/blueprints", json={"idea_request": IDEA}).json()
    resp = client.post(
        "/api/v1/prompts", json={"blueprint": bp, "coder": "gitpilot", "bundle_id": "b1"}
    ).json()
    assert resp["coder"] == "gitpilot"
    assert resp["handoff_mode"] == "git"
    assert "MATRIX_STATUS" in resp["prompt"]


def test_regenerate_endpoint(client: TestClient) -> None:
    bp = client.post("/api/v1/blueprints", json={"idea_request": IDEA}).json()
    reg = client.post(
        "/api/v1/blueprints/regenerate",
        json={
            "base_blueprint": bp,
            "change_request": "Add authentication and a dashboard",
            "change_type": "add-feature",
            "current_version": "1.0.0",
        },
    ).json()
    assert reg["previous_version"] == "1.0.0"
    assert reg["version"] == "1.1.0"
    assert reg["blueprint"]["stack"]["auth"] == "session"


def test_validation_endpoint(client: TestClient) -> None:
    bp = client.post("/api/v1/blueprints", json={"idea_request": IDEA}).json()
    val = client.post(
        "/api/v1/validations",
        json={"blueprint": bp, "request": {"changed_files": [{"path": "MATRIX_BLUEPRINT.yaml"}]}},
    ).json()
    assert val["status"] == "rejected"
    assert any(v["rule_id"] == "RMD-002" for v in val["violations"])


def test_export_streams_deterministic_zip(client: TestClient) -> None:
    bp = client.post("/api/v1/blueprints", json={"idea_request": IDEA}).json()
    a = client.post("/api/v1/exports", json={"blueprint": bp, "version": "1.0.0"})
    b = client.post("/api/v1/exports", json={"blueprint": bp, "version": "1.0.0"})
    assert a.status_code == 200
    assert a.headers["content-type"] == "application/zip"
    assert a.content == b.content, "export must be byte-deterministic over HTTP too"
    assert a.headers["x-matrix-contract-hash"].startswith("sha256:")
    import io

    with zipfile.ZipFile(io.BytesIO(a.content)) as zf:
        assert "MATRIX_BLUEPRINT.yaml" in zf.namelist()


def test_batch_plan_endpoint(client: TestClient) -> None:
    bp = client.post("/api/v1/blueprints", json={"idea_request": IDEA}).json()
    plan = client.post(
        "/api/v1/batches/plan",
        json={
            "blueprint": bp,
            "goal_md": "Add authentication",
            "change_type": "add-feature",
            "ordinal": 3,
        },
    ).json()
    assert plan["ordinal"] == 3
    assert plan["batch_id"].startswith("bat-")
    assert plan["tasks"]


def test_batch_prompt_packs_endpoint(client: TestClient) -> None:
    bp = client.post("/api/v1/blueprints", json={"idea_request": IDEA}).json()
    plan = client.post(
        "/api/v1/batches/plan", json={"blueprint": bp, "goal_md": "Add login", "ordinal": 2}
    ).json()
    packs = client.post(
        "/api/v1/batches/prompt-packs",
        json={"blueprint": bp, "batch": plan, "coders": ["claude-code", "codex-chatgpt"]},
    ).json()
    handoffs = {h["coder"]: h for h in packs["handoffs"]}
    assert "CLAUDE.md" in handoffs["claude-code"]["helper_files"]
    assert "AGENTS.md" in handoffs["codex-chatgpt"]["helper_files"]
    assert "Batch 02" in handoffs["claude-code"]["prompt"]["prompt"]


def test_commits_diff_endpoint(client: TestClient) -> None:
    diff = client.post(
        "/api/v1/commits/diff",
        json={"base_files": {"a.py": "1\n"}, "head_files": {"a.py": "2\n", "b.py": "x\n"}},
    ).json()
    assert diff["added"] == ["b.py"]
    assert diff["changed"] == ["a.py"]
    assert "diff --git a/a.py b/a.py" in diff["patch"]


def test_openapi_is_served(client: TestClient) -> None:
    spec = client.get("/openapi.json").json()
    paths = set(spec["paths"])
    assert "/api/v1/ideas/parse" in paths
    assert "/api/v1/validations" in paths
    assert "/api/v1/batches/plan" in paths
    assert "/api/v1/commits/diff" in paths
