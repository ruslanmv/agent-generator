"""Batch 5 — controlled blueprint compiler."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from agent_generator.contracts import IdeaRequest
from agent_generator.control.contract import IMMUTABLE_FILES, compute_contract_hash
from agent_generator.engine import AgentGenerator
from agent_generator.template_compiler import MANIFEST_PATH

FIXED_NOW = datetime(2026, 6, 12, 14, 0, 0, tzinfo=timezone.utc)
IDEA = IdeaRequest(idea="An AI agent that analyzes GitHub repositories for risks")


@pytest.fixture()
def engine() -> AgentGenerator:
    return AgentGenerator(fixed_now=FIXED_NOW)


@pytest.fixture()
def compiled(engine: AgentGenerator):
    return engine.compile_bundle(engine.generate_controlled_blueprint(IDEA))


def test_all_control_files_present(compiled) -> None:
    paths = set(compiled.paths())
    for control in (
        "MATRIX_BLUEPRINT.yaml",
        "MATRIX_STANDARDS.lock",
        "MATRIX_TASKS.md",
        "MATRIX_ALLOWED_CHANGES.md",
        "MATRIX_ACCEPTANCE_CRITERIA.md",
        "MATRIX_VALIDATION.md",
    ):
        assert control in paths


def test_docs_readme_scaffold_and_prompts_present(compiled) -> None:
    paths = set(compiled.paths())
    assert {
        "README.md",
        "docs/architecture.md",
        "docs/security.md",
        "docs/standards-report.md",
    } <= paths
    assert ".env.example" in paths
    assert "backend/app/main.py" in paths and "backend/tests/test_health.py" in paths
    assert "frontend/app/page.tsx" in paths
    assert "coder-prompts/claude-code.md" in paths
    assert MANIFEST_PATH in paths


def test_only_blueprint_and_lock_are_immutable(compiled) -> None:
    immutable = {f.path for f in compiled.files if f.immutable}
    assert immutable == set(IMMUTABLE_FILES)
    assert set(compiled.immutable_files) == set(IMMUTABLE_FILES)


def test_contract_hash_matches_immutable_content(compiled) -> None:
    immutable_map = {p: compiled.get(p).content for p in compiled.immutable_files}
    assert compiled.contract_hash == compute_contract_hash(immutable_map)
    assert compiled.contract_hash.startswith("sha256:")


def test_manifest_lists_files_with_digests_and_contract_hash(compiled) -> None:
    from agent_generator.artifacts.checksums import CHECKSUMS_PATH
    from agent_generator.artifacts.sbom import SBOM_PATH

    manifest = json.loads(compiled.get(MANIFEST_PATH).content)
    assert manifest["contract_hash"] == compiled.contract_hash
    assert sorted(manifest["immutable_files"]) == sorted(IMMUTABLE_FILES)
    assert manifest["sbom_ref"] == SBOM_PATH
    listed = {entry["path"] for entry in manifest["files"]}
    # Manifest indexes everything except the two index files (itself and checksums.txt).
    assert listed == set(compiled.paths()) - {MANIFEST_PATH, CHECKSUMS_PATH}
    for entry in manifest["files"]:
        assert entry["digest"].startswith("sha256:")


def test_compilation_is_deterministic() -> None:
    a = AgentGenerator(fixed_now=FIXED_NOW)
    b = AgentGenerator(fixed_now=FIXED_NOW)
    ca = a.compile_bundle(a.generate_controlled_blueprint(IDEA))
    cb = b.compile_bundle(b.generate_controlled_blueprint(IDEA))
    assert ca.file_map() == cb.file_map()
    assert ca.contract_hash == cb.contract_hash


def test_standards_lock_is_real_in_compiled_bundle(compiled) -> None:
    lock_text = compiled.get("MATRIX_STANDARDS.lock").content
    assert "definitions_pack" in lock_text
    assert "2026.06.0" in lock_text
    assert "placeholder" not in lock_text.lower()
