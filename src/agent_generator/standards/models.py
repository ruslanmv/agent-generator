"""Standards loader models.

These describe the matrix-definitions pack as the loader sees it on disk. The *output* of
the loader (the ``MATRIX_STANDARDS.lock``) is the shared contract
``agent_generator.contracts.StandardsLock``; these models are loader-internal.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class PackRule(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    path: str = ""
    domain: str = ""
    severity: str = "medium"


class PackManifest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    schema_version: str
    pack_id: str
    version: str
    status: str = "stable"
    created_at: str | None = None
    owner: str | None = None
    brand: str | None = None
    website: str | None = None
    compatibility: dict[str, str] = Field(default_factory=dict)
    packs: dict[str, str] = Field(default_factory=dict)
    signatures: dict[str, str] = Field(default_factory=dict)
    checksums: str = "checksums.txt"


@dataclass(frozen=True)
class ChecksumResult:
    """Outcome of verifying pack files against ``checksums.txt``."""

    ok: bool
    verified: list[str] = field(default_factory=list)
    mismatched: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)

    @property
    def summary(self) -> str:
        return (
            f"{len(self.verified)} verified, "
            f"{len(self.mismatched)} mismatched, "
            f"{len(self.missing)} missing"
        )


@dataclass(frozen=True)
class SignatureResult:
    """Outcome of verifying the pack signature.

    ``mode`` is one of: ``verified`` (real signature checked), ``placeholder`` (dev-metadata
    bundle, not a real signature), ``tampered`` (subject digests do not match), ``missing``, or
    ``unverified``. ``digests_verified`` reports whether the bundle's subject digests match the
    actual pack files (the integrity check available before keyless signing lands).
    """

    mode: str
    verified: bool
    bundle_path: str | None = None
    digests_verified: bool = False
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CompatibilityResult:
    ok: bool
    requirement: str
    actual: str
    message: str


class StandardsPack(BaseModel):
    """A loaded, (optionally) verified standards pack."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    root: Path
    pack_dir: Path
    manifest: PackManifest
    rules: list[PackRule] = Field(default_factory=list)
    combined_digest: str = ""
    file_digests: dict[str, str] = Field(default_factory=dict)
    checksums: ChecksumResult | None = None
    signature: SignatureResult | None = None
    warnings: list[str] = Field(default_factory=list)

    @property
    def pack_id(self) -> str:
        return self.manifest.pack_id

    @property
    def version(self) -> str:
        return self.manifest.version

    def rule_ids(self) -> list[str]:
        return [rule.id for rule in self.rules]


class Profile(BaseModel):
    model_config = ConfigDict(extra="ignore")

    schema_version: str = "1.0"
    profile: str
    description: str = ""
    required_rules: list[str] = Field(default_factory=list)


__all__ = [
    "PackRule",
    "PackManifest",
    "ChecksumResult",
    "SignatureResult",
    "CompatibilityResult",
    "StandardsPack",
    "Profile",
]
