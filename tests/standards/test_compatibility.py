"""Batch 3 — engine/pack compatibility. This is the 0.2.0 milestone proof."""

from __future__ import annotations

import agent_generator
from agent_generator.standards import check_compatibility, load_pack
from agent_generator.standards.models import PackManifest


def test_engine_satisfies_definitions_floor() -> None:
    # matrix-definitions requires agent_generator >= 0.2.0; the engine is at or above it.
    from packaging.version import Version

    assert Version(agent_generator.__version__) >= Version("0.2.0")


def test_bundled_pack_compatibility_passes() -> None:
    # The whole point of the >=0.2.0 floor: the running engine satisfies it.
    result = check_compatibility(load_pack().manifest)
    assert result.ok, result.message
    assert result.requirement == ">=0.2.0"


def test_old_version_would_not_satisfy() -> None:
    manifest = load_pack().manifest
    result = check_compatibility(manifest, version="0.1.3")
    assert result.ok is False


def test_missing_requirement_is_compatible() -> None:
    manifest = PackManifest(schema_version="1.0", pack_id="p", version="1.0", compatibility={})
    assert check_compatibility(manifest).ok is True
