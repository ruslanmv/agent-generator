"""Deterministic ``MATRIX_STANDARDS.lock`` construction.

The lock pins exactly which signed standards a generated bundle was built against: the pack
id/version, the combined-pack digest, the applied rule ids (from the quality profile), and
the digests of the pack inputs. Given the same pack, quality level, and ``generated_at``, the
lock is byte-identical — which is what makes it safe to drift-check later.
"""

from __future__ import annotations

import yaml

from agent_generator.contracts.common import QualityLevel
from agent_generator.contracts.standards import DefinitionsPackRef, StandardsLock
from agent_generator.standards.models import Profile, StandardsPack

#: Matrix control files a generated bundle locks (canonical order).
DEFAULT_CONTROL_FILES = (
    "MATRIX_BLUEPRINT.yaml",
    "MATRIX_STANDARDS.lock",
    "MATRIX_TASKS.md",
    "MATRIX_ALLOWED_CHANGES.md",
    "MATRIX_ACCEPTANCE_CRITERIA.md",
    "MATRIX_VALIDATION.md",
)


def build_standards_lock(
    pack: StandardsPack,
    *,
    quality_level: QualityLevel | str,
    profile: Profile,
    generated_at: str,
    control_files: list[str] | None = None,
) -> StandardsLock:
    """Build a deterministic ``StandardsLock`` from a pack and a quality profile."""
    level = (
        quality_level if isinstance(quality_level, QualityLevel) else QualityLevel(quality_level)
    )
    rules = sorted(set(profile.required_rules))
    checksums = {rel: f"sha256:{digest}" for rel, digest in sorted(pack.file_digests.items())}
    return StandardsLock(
        generated_at=generated_at,
        definitions_pack=DefinitionsPackRef(
            pack_id=pack.pack_id,
            version=pack.version,
            checksum=f"sha256:{pack.combined_digest}",
        ),
        quality_level=level,
        rules=rules,
        control_files=list(control_files or DEFAULT_CONTROL_FILES),
        checksums=checksums,
    )


def render_lock_yaml(lock: StandardsLock) -> str:
    """Render the lock as deterministic YAML (sorted keys, block style)."""
    return yaml.safe_dump(lock.to_definitions_dict(), sort_keys=True, default_flow_style=False)


__all__ = ["DEFAULT_CONTROL_FILES", "build_standards_lock", "render_lock_yaml"]
