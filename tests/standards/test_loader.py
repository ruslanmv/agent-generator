"""Batch 3 — standards loader: load + verify the bundled pack."""

from __future__ import annotations

import shutil

import pytest

from agent_generator.errors import StandardsError
from agent_generator.standards import load_pack, load_profile, validate_pack
from agent_generator.standards.loader import BUNDLED_ROOT


def test_bundled_pack_loads_and_verifies() -> None:
    pack = load_pack()  # bundled snapshot
    assert pack.pack_id == "matrix-definitions-current"
    assert pack.version == "2026.06.0"
    assert pack.rules, "pack should expose rules"
    assert pack.checksums is not None and pack.checksums.ok
    assert pack.combined_digest and len(pack.combined_digest) == 64


def test_bundled_pack_is_structurally_valid() -> None:
    issues = validate_pack(load_pack())
    assert issues == [], issues


def test_signature_is_placeholder_in_warn_mode() -> None:
    pack = load_pack(signature_mode="warn")
    assert pack.signature is not None
    assert pack.signature.mode == "placeholder"
    assert pack.signature.verified is False
    assert pack.warnings, "placeholder signature should produce a warning"


def test_signature_require_mode_raises_on_placeholder() -> None:
    with pytest.raises(StandardsError):
        load_pack(signature_mode="require")


def test_profiles_load_with_required_rules() -> None:
    for level in ("starter", "standard", "production", "enterprise"):
        profile = load_profile(None, level)
        assert profile.profile == level
        assert profile.required_rules, f"{level} profile has no required_rules"


def test_checksum_failure_is_fail_closed(tmp_path) -> None:
    root = tmp_path / "md"
    shutil.copytree(BUNDLED_ROOT, root)
    tampered = root / "packs" / "current" / "combined.pack.yaml"
    tampered.write_text(tampered.read_text() + "\n# tamper\n")

    with pytest.raises(StandardsError):
        load_pack(root, verify=True)

    # With verification disabled the loader still returns, but flags the dirty checksums.
    pack = load_pack(root, verify=False)
    assert pack.checksums is not None and not pack.checksums.ok
