"""Batch 10 — release evidence (provenance + signature) and dry-run publishing."""

from __future__ import annotations

import hashlib
import json
import zipfile
from datetime import datetime, timezone

import pytest

from agent_generator.artifacts.checksums import CHECKSUMS_PATH
from agent_generator.artifacts.provenance import PROVENANCE_PATH
from agent_generator.artifacts.signatures import COSIGN_PATH, verify_cosign_bundle
from agent_generator.contracts import IdeaRequest
from agent_generator.engine import AgentGenerator
from agent_generator.template_compiler.manifest import MANIFEST_PATH

FIXED_NOW = datetime(2026, 6, 12, 14, 0, 0, tzinfo=timezone.utc)
IDEA = IdeaRequest(idea="An AI agent that analyzes GitHub repositories for risks")


@pytest.fixture()
def engine() -> AgentGenerator:
    return AgentGenerator(fixed_now=FIXED_NOW)


@pytest.fixture()
def blueprint(engine: AgentGenerator):
    return engine.generate_controlled_blueprint(IDEA)


# --- release evidence ------------------------------------------------------


def test_release_bundle_adds_provenance_and_signature(engine: AgentGenerator, blueprint) -> None:
    rel = engine.build_release_evidence(blueprint, version="1.0.0")
    paths = set(rel.paths())
    assert PROVENANCE_PATH in paths
    assert COSIGN_PATH in paths
    assert MANIFEST_PATH in paths and CHECKSUMS_PATH in paths


def test_default_compile_has_no_release_evidence(engine: AgentGenerator, blueprint) -> None:
    plain = engine.compile_bundle(blueprint)
    assert PROVENANCE_PATH not in plain.paths()
    assert COSIGN_PATH not in plain.paths()


def test_provenance_is_valid_intoto(engine: AgentGenerator, blueprint) -> None:
    rel = engine.build_release_evidence(blueprint, version="1.0.0")
    statement = json.loads(rel.get(PROVENANCE_PATH).content)
    assert statement["_type"] == "https://in-toto.io/Statement/v1"
    assert statement["predicateType"] == "https://slsa.dev/provenance/v1"
    assert statement["subject"], "provenance lists payload subjects"


def test_checksums_cover_release_evidence(engine: AgentGenerator, blueprint) -> None:
    rel = engine.build_release_evidence(blueprint, version="1.0.0")
    files = rel.file_map()
    for line in files[CHECKSUMS_PATH].strip().splitlines():
        digest, path = line.split("  ", 1)
        assert hashlib.sha256(files[path].encode("utf-8")).hexdigest() == digest
    listed = {line.split("  ", 1)[1] for line in files[CHECKSUMS_PATH].strip().splitlines()}
    assert PROVENANCE_PATH in listed and COSIGN_PATH in listed and MANIFEST_PATH in listed


def test_cosign_bundle_subject_digests_verify(engine: AgentGenerator, blueprint) -> None:
    rel = engine.build_release_evidence(blueprint, version="1.0.0")
    files = rel.file_map()
    result = verify_cosign_bundle(files[COSIGN_PATH], files)
    assert result.digests_verified is True
    assert result.mode == "placeholder"


def test_cosign_detects_tampering(engine: AgentGenerator, blueprint) -> None:
    rel = engine.build_release_evidence(blueprint, version="1.0.0")
    files = dict(rel.file_map())
    files[MANIFEST_PATH] = files[MANIFEST_PATH] + "\n# tamper\n"
    result = verify_cosign_bundle(files[COSIGN_PATH], files)
    assert result.mode == "tampered"
    assert MANIFEST_PATH in result.mismatched


def test_release_export_is_deterministic(engine: AgentGenerator, blueprint, tmp_path) -> None:
    a = engine.export_zip(blueprint, tmp_path / "a.zip", release_evidence=True)
    b = AgentGenerator(fixed_now=FIXED_NOW).export_zip(
        AgentGenerator(fixed_now=FIXED_NOW).generate_controlled_blueprint(IDEA),
        tmp_path / "b.zip",
        release_evidence=True,
    )
    assert a.read_bytes() == b.read_bytes()
    with zipfile.ZipFile(a) as zf:
        assert PROVENANCE_PATH in zf.namelist()


# --- publishing gate (dry-run) ---------------------------------------------


def test_publish_rejected_without_validation(engine: AgentGenerator, blueprint) -> None:
    pub = engine.prepare_matrixhub_publication(blueprint, version="1.0.0")
    assert pub.accepted is False
    assert pub.status == "needs-validation"
    assert pub.trust_status == "unverified"


def test_publish_accepted_dry_run_with_approved_validation(
    engine: AgentGenerator, blueprint, tmp_path
) -> None:
    zip_path = engine.export_zip(blueprint, tmp_path / "b.zip")
    repo = tmp_path / "repo"
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(repo)
    report = engine.validate_ai_coder_patch("b", repo_path=repo, blueprint=blueprint)
    assert report.approved is True

    pub = engine.prepare_matrixhub_publication(blueprint, version="1.0.0", validation_report=report)
    assert pub.accepted is True
    assert pub.status == "accepted-dry-run"
    assert pub.dry_run is True
    assert pub.trust_status == "dry-run"
    assert pub.matrixhub_slug == "github-repo-intelligence-agent"
    assert not pub.missing_artifacts


def test_publish_rejected_when_artifact_missing(engine: AgentGenerator, blueprint) -> None:
    from agent_generator.publishing import build_publication

    # A plain (non-release) bundle lacks provenance -> the gate rejects it.
    plain = engine.compile_bundle(blueprint)
    pub = build_publication(plain)
    assert pub.accepted is False
    assert pub.status == "rejected"
    assert PROVENANCE_PATH in pub.missing_artifacts
