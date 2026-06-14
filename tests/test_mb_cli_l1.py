"""Track L1 — the local-first ``mb`` CLI works fully offline via the in-process SDK.

Drives the documented "realistic session" end to end against a throwaway working directory:
init -> next -> prompt -> check (approved -> commit) -> reject -> repair -> timeline, asserting
exit codes (0/1/2), the .mb/ layout, and determinism.
"""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

import agent_generator
from agent_generator.mb import app

runner = CliRunner()
IDEA = "A GitHub repo intelligence agent"


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_version_flag() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0, result.output
    assert agent_generator.__version__ in result.output


def test_init_scaffolds_mb(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", IDEA])
    assert result.exit_code == 0, result.output
    project = _read(tmp_path / ".mb" / "project.json")
    assert project["version_label"] == "v1.0.0"
    assert project["next_batch_ordinal"] == 1
    assert project["next_commit_no"] == 1
    assert (tmp_path / ".mb" / "blueprint.json").exists()
    # init refuses to clobber an existing project.
    assert runner.invoke(app, ["init", IDEA]).exit_code == 2


def test_realistic_session_offline(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    assert runner.invoke(app, ["init", IDEA]).exit_code == 0

    nxt = runner.invoke(app, ["next", "Add a /health endpoint with a test"])
    assert nxt.exit_code == 0, nxt.output
    assert "Batch 01" in nxt.output
    batch = _read(tmp_path / ".mb" / "batches" / "01" / "batch.json")
    assert batch["status"] == "draft"
    assert batch["change_type"] == "add-feature"

    pr = runner.invoke(app, ["prompt", "--coder", "claude", "--file", str(tmp_path / "p.md")])
    assert pr.exit_code == 0, pr.output
    assert (tmp_path / ".mb" / "batches" / "01" / "prompts" / "claude-code.md").exists()
    assert (tmp_path / "CLAUDE.md").exists()  # tool-native helper emitted to cwd
    assert _read(tmp_path / ".mb" / "batches" / "01" / "batch.json")["status"] == "ready"

    chk = runner.invoke(
        app, ["check", "--changed", "backend/app/api/health.py", "tests/test_health.py"]
    )
    assert chk.exit_code == 0, chk.output  # approved
    assert "MATRIX_STATUS: approved" in chk.output
    # A commit was recorded and the batch is committed.
    commit = _read(tmp_path / ".mb" / "commits" / "001" / "manifest.json")
    assert commit["validation_status"] == "approved"
    assert commit["batch_ref"] == batch["batch_id"]
    project = _read(tmp_path / ".mb" / "project.json")
    assert project["current_commit_ref"] == commit["commit_ref"]
    assert project["next_commit_no"] == 2

    tl = runner.invoke(app, ["timeline"])
    assert tl.exit_code == 0
    assert "Batch 01" in tl.output and "commit 001" in tl.output


def test_check_rejects_forbidden_change(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", IDEA])
    runner.invoke(app, ["next", "Tweak the lock"])
    result = runner.invoke(app, ["check", "MATRIX_STANDARDS.lock"])
    assert result.exit_code == 2, result.output  # rejected
    assert "rejected" in result.output
    assert _read(tmp_path / ".mb" / "project.json")["last_failing_batch"] == 1


def test_repair_creates_fix_issue_batch(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", IDEA])
    runner.invoke(app, ["next", "Tweak the lock"])
    runner.invoke(app, ["check", "MATRIX_STANDARDS.lock"])
    rep = runner.invoke(app, ["repair", "--file", str(tmp_path / "repair.md")])
    assert rep.exit_code == 0, rep.output
    batch2 = _read(tmp_path / ".mb" / "batches" / "02" / "batch.json")
    assert batch2["change_type"] == "fix-issue"
    assert batch2["is_repair"] is True
    assert (tmp_path / "repair.md").read_text(encoding="utf-8").strip()


def test_deterministic_ids(tmp_path, monkeypatch) -> None:
    ids = []
    for sub in ("a", "b"):
        d = tmp_path / sub
        d.mkdir()
        monkeypatch.chdir(d)
        runner.invoke(app, ["init", IDEA])
        runner.invoke(app, ["next", "Add a /health endpoint with a test"])
        ids.append(
            (
                _read(d / ".mb" / "project.json")["project_id"],
                _read(d / ".mb" / "batches" / "01" / "batch.json")["batch_id"],
            )
        )
    assert ids[0] == ids[1]  # same idea + goal -> identical content-addressed ids, offline
