"""Batch E2 — commit snapshots, diffs, and batch-delta validation scoping."""

from __future__ import annotations

import zipfile
from datetime import datetime, timezone

import pytest

from agent_generator.contracts import IdeaRequest, ValidationStatus
from agent_generator.control import diff_submissions, tree_hash
from agent_generator.control.submission import Submission, scan_repo
from agent_generator.engine import AgentGenerator

FIXED_NOW = datetime(2026, 6, 12, 14, 0, 0, tzinfo=timezone.utc)
IDEA = IdeaRequest(idea="An AI agent that analyzes GitHub repositories for risks")


@pytest.fixture()
def engine() -> AgentGenerator:
    return AgentGenerator(fixed_now=FIXED_NOW)


@pytest.fixture()
def blueprint(engine: AgentGenerator):
    return engine.generate_controlled_blueprint(IDEA)


def _export_repo(engine: AgentGenerator, blueprint, tmp_path, name: str):
    zip_path = engine.export_zip(blueprint, tmp_path / f"{name}.zip")
    repo = tmp_path / name
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(repo)
    return repo


# --- tree_hash -------------------------------------------------------------


def test_tree_hash_is_order_independent() -> None:
    a = Submission(files={"a.py": "x", "b.py": "y"})
    b = Submission(files={"b.py": "y", "a.py": "x"})
    assert tree_hash(a) == tree_hash(b)
    assert tree_hash(a).startswith("sha256:")


def test_tree_hash_normalizes_crlf() -> None:
    lf = Submission(files={"f.py": "line1\nline2\n"})
    crlf = Submission(files={"f.py": "line1\r\nline2\r\n"})
    assert tree_hash(lf) == tree_hash(crlf)


def test_tree_hash_changes_with_content() -> None:
    assert tree_hash(Submission(files={"f": "a"})) != tree_hash(Submission(files={"f": "b"}))


# --- diff_submissions ------------------------------------------------------


def test_diff_classifies_added_changed_deleted() -> None:
    base = Submission(files={"keep.py": "1", "edit.py": "old", "gone.py": "x"})
    head = Submission(files={"keep.py": "1", "edit.py": "new", "added.py": "y"})
    diff = diff_submissions(base, head)
    assert diff.added == ["added.py"]
    assert diff.changed == ["edit.py"]
    assert diff.deleted == ["gone.py"]
    assert not diff.is_empty
    assert "diff --git a/edit.py b/edit.py" in diff.patch
    assert "+new" in diff.patch and "-old" in diff.patch


def test_diff_is_empty_for_crlf_only_change() -> None:
    base = Submission(files={"f.py": "a\nb\n"})
    head = Submission(files={"f.py": "a\r\nb\r\n"})  # only line endings differ
    diff = diff_submissions(base, head)
    assert diff.is_empty
    assert diff.patch == ""


def test_diff_patch_is_byte_stable() -> None:
    base = Submission(files={"f.py": "a\nb\n"})
    head = Submission(files={"f.py": "a\nB\n", "n.py": "new\n"})
    assert diff_submissions(base, head).patch == diff_submissions(base, head).patch


# --- commit manifest (engine) ----------------------------------------------


def test_build_commit_manifest(engine: AgentGenerator, blueprint, tmp_path) -> None:
    repo = _export_repo(engine, blueprint, tmp_path, "v1")
    commit = engine.build_commit(commit_no=1, head_repo_path=repo, validation_status="approved")
    assert commit.commit_no == 1
    assert commit.tree_hash.startswith("sha256:")
    assert commit.validation_status == ValidationStatus.APPROVED
    assert commit.added  # first commit: everything is added


def test_commit_diff_against_parent(engine: AgentGenerator, blueprint, tmp_path) -> None:
    base = _export_repo(engine, blueprint, tmp_path, "base")
    head = _export_repo(engine, blueprint, tmp_path, "head")
    (head / "backend" / "app" / "feature.py").write_text("print('new feature')\n")
    commit = engine.build_commit(
        commit_no=2, head_repo_path=head, base_repo_path=base, parent_commit_ref="mc-1"
    )
    assert commit.parent_commit_ref == "mc-1"
    assert "backend/app/feature.py" in commit.added
    assert not commit.changed and not commit.deleted


def test_engine_diff_bundles(engine: AgentGenerator, blueprint, tmp_path) -> None:
    base = _export_repo(engine, blueprint, tmp_path, "b")
    head = _export_repo(engine, blueprint, tmp_path, "h")
    (head / "README.md").write_text((head / "README.md").read_text() + "\nMore.\n")
    diff = engine.diff_bundles(base_repo_path=base, head_repo_path=head)
    assert diff.changed == ["README.md"]


# --- validator base-delta scoping ------------------------------------------


def test_validation_scopes_to_batch_delta(engine: AgentGenerator, blueprint, tmp_path) -> None:
    # base has a pre-existing secret; the batch only edits an allowed file. With base-scoping,
    # the pre-existing secret is NOT re-flagged — only this batch's delta is validated.
    base = _export_repo(engine, blueprint, tmp_path, "base")
    (base / "backend" / "app").mkdir(parents=True, exist_ok=True)
    (base / "backend" / "app" / "legacy.py").write_text('SECRET_KEY = "9aF3kLpQ2mNvX7yR8tWzB1cD"\n')

    head = scan_repo(base).files  # copy base
    head_dir = tmp_path / "head"
    head_dir.mkdir()
    for path, content in head.items():
        target = head_dir / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
    # The batch adds one clean allowed file.
    (head_dir / "backend" / "app" / "api").mkdir(parents=True, exist_ok=True)
    (head_dir / "backend" / "app" / "api" / "repos.py").write_text("def analyze(): ...\n")

    # Without base: the pre-existing secret is flagged (whole-tree scan).
    whole = engine.validate_ai_coder_patch("b", repo_path=head_dir, blueprint=blueprint)
    assert any(v.rule_id == "SEC-001" for v in whole.violations)

    # With base: only the delta (the clean new file) is checked -> no secret finding.
    delta = engine.validate_ai_coder_patch(
        "b", repo_path=head_dir, base_repo_path=base, blueprint=blueprint
    )
    assert not any(v.rule_id == "SEC-001" for v in delta.violations)


def test_delta_validation_still_catches_new_violation(
    engine: AgentGenerator, blueprint, tmp_path
) -> None:
    base = _export_repo(engine, blueprint, tmp_path, "base")
    head = _export_repo(engine, blueprint, tmp_path, "head")
    # The batch introduces a NEW secret in the delta -> still caught with base-scoping.
    (head / "backend" / "app").mkdir(parents=True, exist_ok=True)
    (head / "backend" / "app" / "cfg.py").write_text('API_KEY = "9aF3kLpQ2mNvX7yR8tWzB1cD"\n')
    report = engine.validate_ai_coder_patch(
        "b", repo_path=head, base_repo_path=base, blueprint=blueprint
    )
    assert report.status == ValidationStatus.REJECTED
    assert any(v.rule_id == "SEC-001" for v in report.violations)
