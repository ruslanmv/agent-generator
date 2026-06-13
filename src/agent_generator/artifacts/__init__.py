"""Artifacts — strict export wiring (Batch 6).

Canonical serialization, SBOM (placeholder), checksums, and the deterministic packager that
turns a compiled file plan into a byte-stable Matrix Bundle ZIP. Provenance and signatures
(Batch 10) will join this package.
"""

from __future__ import annotations

from agent_generator.artifacts.canonical import (
    canonical_json,
    canonical_yaml,
    normalize_newlines,
)
from agent_generator.artifacts.checksums import CHECKSUMS_PATH, build_checksums_txt
from agent_generator.artifacts.models import ArtifactEntry, ArtifactManifest
from agent_generator.artifacts.packager import write_strict_zip, zip_bytes
from agent_generator.artifacts.sbom import SBOM_PATH, build_sbom

__all__ = [
    "canonical_json",
    "canonical_yaml",
    "normalize_newlines",
    "CHECKSUMS_PATH",
    "build_checksums_txt",
    "SBOM_PATH",
    "build_sbom",
    "write_strict_zip",
    "zip_bytes",
    "ArtifactEntry",
    "ArtifactManifest",
]
