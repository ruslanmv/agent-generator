"""Standards contracts — pack reference and the standards lock file.

These mirror matrix-definitions ``matrix-standards-lock.schema.json``. The full pack
loader (fetch, digest verification, compatibility resolution) arrives in Batch 3; this
module defines the shared shape so the engine, Matrix Builder, and matrix-definitions
agree on what a ``MATRIX_STANDARDS.lock`` contains.
"""

from __future__ import annotations

from pydantic import Field

from agent_generator.contracts.common import JsonDict, QualityLevel, StrictModel


class DefinitionsPackRef(StrictModel):
    pack_id: str
    version: str
    checksum: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")


class StandardsLock(StrictModel):
    schema_version: str = "1.0"
    generated_at: str = Field(pattern=r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")
    definitions_pack: DefinitionsPackRef
    quality_level: QualityLevel = QualityLevel.STANDARD
    rules: list[str] = Field(default_factory=list)
    control_files: list[str] = Field(default_factory=list)
    checksums: dict[str, str] = Field(default_factory=dict)

    def to_definitions_dict(self) -> JsonDict:
        """Project onto matrix-definitions ``matrix-standards-lock.schema.json``."""
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "definitions_pack": self.definitions_pack.model_dump(),
            "quality_level": self.quality_level.value,
            "rules": list(self.rules),
            "control_files": list(self.control_files),
            "checksums": dict(self.checksums),
        }


__all__ = ["DefinitionsPackRef", "StandardsLock"]
