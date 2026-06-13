"""Canary: release-bundle completeness and integrity."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

import pytest

from agent_generator.artifacts.checksums import CHECKSUMS_PATH
from agent_generator.artifacts.provenance import PROVENANCE_PATH
from agent_generator.artifacts.signatures import COSIGN_PATH, verify_cosign_bundle
from agent_generator.contracts import IdeaRequest
from agent_generator.engine import AgentGenerator
from agent_generator.publishing import REQUIRED_ARTIFACTS
from agent_generator.template_compiler.manifest import MANIFEST_PATH

FIXED_NOW = datetime(2026, 6, 12, 14, 0, 0, tzinfo=timezone.utc)


@pytest.fixture()
def release_bundle():
    engine = AgentGenerator(fixed_now=FIXED_NOW)
    blueprint = engine.generate_controlled_blueprint(
        IdeaRequest(idea="An AI agent that analyzes GitHub repositories for risks")
    )
    return engine.build_release_evidence(blueprint, version="1.0.0")


def test_all_required_artifacts_present(release_bundle) -> None:
    present = set(release_bundle.paths())
    missing = [a for a in REQUIRED_ARTIFACTS if a not in present]
    assert not missing, missing


def test_evidence_files_present(release_bundle) -> None:
    paths = set(release_bundle.paths())
    assert {PROVENANCE_PATH, COSIGN_PATH, MANIFEST_PATH, CHECKSUMS_PATH} <= paths


def test_checksums_verify_every_file(release_bundle) -> None:
    files = release_bundle.file_map()
    for line in files[CHECKSUMS_PATH].strip().splitlines():
        digest, path = line.split("  ", 1)
        assert hashlib.sha256(files[path].encode("utf-8")).hexdigest() == digest


def test_cosign_subject_digests_verify(release_bundle) -> None:
    files = release_bundle.file_map()
    result = verify_cosign_bundle(files[COSIGN_PATH], files)
    assert result.digests_verified is True


def test_release_bundle_is_deterministic() -> None:
    a = AgentGenerator(fixed_now=FIXED_NOW)
    b = AgentGenerator(fixed_now=FIXED_NOW)
    idea = IdeaRequest(idea="An AI agent that analyzes GitHub repositories for risks")
    ra = a.build_release_evidence(a.generate_controlled_blueprint(idea), version="1.0.0")
    rb = b.build_release_evidence(b.generate_controlled_blueprint(idea), version="1.0.0")
    assert ra.file_map() == rb.file_map()
