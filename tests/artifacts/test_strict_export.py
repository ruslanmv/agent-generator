"""Batch 6 — strict, byte-deterministic Matrix Bundle export."""

from __future__ import annotations

import hashlib
import json
import zipfile
from datetime import datetime, timezone

import pytest

from agent_generator.artifacts.canonical import canonical_json, canonical_yaml, normalize_newlines
from agent_generator.artifacts.checksums import CHECKSUMS_PATH, build_checksums_txt
from agent_generator.artifacts.sbom import SBOM_PATH
from agent_generator.contracts import IdeaRequest
from agent_generator.engine import AgentGenerator
from agent_generator.template_compiler.manifest import MANIFEST_PATH

FIXED_NOW = datetime(2026, 6, 12, 14, 0, 0, tzinfo=timezone.utc)
IDEA = IdeaRequest(idea="An AI agent that analyzes GitHub repositories for risks")


@pytest.fixture()
def compiled():
    engine = AgentGenerator(fixed_now=FIXED_NOW)
    return engine.compile_bundle(engine.generate_controlled_blueprint(IDEA))


# --- canonical serializers -------------------------------------------------


def test_normalize_newlines_strips_crlf() -> None:
    assert normalize_newlines("a\r\nb\rc\n") == "a\nb\nc\n"


def test_canonical_json_is_sorted_and_lf() -> None:
    out = canonical_json({"b": 1, "a": 2})
    assert out == '{\n  "a": 2,\n  "b": 1\n}\n'
    assert "\r" not in out


def test_canonical_yaml_is_sorted_and_lf() -> None:
    out = canonical_yaml({"b": 1, "a": 2})
    assert out == "a: 2\nb: 1\n"
    assert "\r" not in out


# --- bundle artifacts ------------------------------------------------------


def test_bundle_has_sbom_manifest_and_checksums(compiled) -> None:
    paths = set(compiled.paths())
    assert {SBOM_PATH, MANIFEST_PATH, CHECKSUMS_PATH} <= paths


def test_sbom_is_valid_cyclonedx_placeholder(compiled) -> None:
    sbom = json.loads(compiled.get(SBOM_PATH).content)
    assert sbom["bomFormat"] == "CycloneDX"
    assert sbom["specVersion"] == "1.5"
    assert sbom["components"], "components derived from the stack"
    props = {p["name"]: p["value"] for p in sbom["metadata"]["properties"]}
    assert props["matrix:sbom-status"] == "placeholder"


def test_checksums_cover_every_file_except_itself(compiled) -> None:
    files = compiled.file_map()
    expected = build_checksums_txt(files)
    assert compiled.get(CHECKSUMS_PATH).content == expected

    # Every line verifies against the actual bundle content.
    listed_paths = set()
    for line in expected.splitlines():
        digest, path = line.split("  ", 1)
        listed_paths.add(path)
        assert hashlib.sha256(files[path].encode("utf-8")).hexdigest() == digest
    assert listed_paths == set(files) - {CHECKSUMS_PATH}


def test_all_files_use_lf_line_endings(compiled) -> None:
    for path, content in compiled.file_map().items():
        assert "\r" not in content, f"CR found in {path}"


# --- strict ZIP determinism ------------------------------------------------


def test_zip_is_byte_identical_across_engines(tmp_path) -> None:
    a = AgentGenerator(fixed_now=FIXED_NOW)
    b = AgentGenerator(fixed_now=FIXED_NOW)
    bp_a = a.generate_controlled_blueprint(IDEA)
    bp_b = b.generate_controlled_blueprint(IDEA)
    za = a.export_zip(bp_a, tmp_path / "a.zip")
    zb = b.export_zip(bp_b, tmp_path / "b.zip")
    assert za.read_bytes() == zb.read_bytes()


def test_zip_entries_use_fixed_timestamp(tmp_path) -> None:
    engine = AgentGenerator(fixed_now=FIXED_NOW)
    bp = engine.generate_controlled_blueprint(IDEA)
    out = engine.export_zip(bp, tmp_path / "bundle.zip")
    with zipfile.ZipFile(out) as zf:
        infos = zf.infolist()
        assert infos == sorted(infos, key=lambda i: i.filename), "entries must be sorted"
        for info in infos:
            assert info.date_time == (1980, 1, 1, 0, 0, 0)
