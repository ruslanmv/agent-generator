"""Artifact manifest models for Matrix Bundle exports.

A minimal, stable shape now; SBOM/attestation references are optional and become populated
by the release-evidence pipeline in Batch 6/Batch 10.
"""

from __future__ import annotations

from pydantic import Field

from agent_generator.contracts.common import JsonDict, StrictModel


class ArtifactEntry(StrictModel):
    path: str = Field(min_length=1)
    digest: str | None = None
    size_bytes: int | None = Field(default=None, ge=0)
    kind: str = "file"


class ArtifactManifest(StrictModel):
    schema_version: str = "1.0"
    bundle_id: str
    blueprint_id: str
    files: list[ArtifactEntry] = Field(default_factory=list)
    sbom_ref: str | None = None
    attestation_ref: str | None = None
    metadata: JsonDict = Field(default_factory=dict)


__all__ = ["ArtifactEntry", "ArtifactManifest"]
