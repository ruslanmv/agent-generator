"""matrix-definitions standards loader (Batch 3).

Loads a signed standards pack, verifies it (checksums fail-closed; signature in warn mode
until production signing lands), checks engine compatibility, and emits a deterministic
``MATRIX_STANDARDS.lock``.
"""

from __future__ import annotations

from agent_generator.standards.compatibility import check_compatibility
from agent_generator.standards.loader import (
    BUNDLED_ROOT,
    load_pack,
    load_profile,
    resolve_root,
)
from agent_generator.standards.lock import (
    DEFAULT_CONTROL_FILES,
    build_standards_lock,
    render_lock_yaml,
)
from agent_generator.standards.models import (
    ChecksumResult,
    CompatibilityResult,
    PackManifest,
    PackRule,
    Profile,
    SignatureResult,
    StandardsPack,
)
from agent_generator.standards.registry import StandardsRegistry
from agent_generator.standards.validator import (
    validate_pack,
    validate_profile_against_pack,
)

__all__ = [
    "BUNDLED_ROOT",
    "load_pack",
    "load_profile",
    "resolve_root",
    "build_standards_lock",
    "render_lock_yaml",
    "DEFAULT_CONTROL_FILES",
    "check_compatibility",
    "StandardsRegistry",
    "validate_pack",
    "validate_profile_against_pack",
    "ChecksumResult",
    "CompatibilityResult",
    "PackManifest",
    "PackRule",
    "Profile",
    "SignatureResult",
    "StandardsPack",
]
