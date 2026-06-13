"""Immutable blueprint contract — hash-locking (Batch 5).

The contract hash is a single deterministic digest over the *immutable* files in a bundle
(``MATRIX_BLUEPRINT.yaml`` and ``MATRIX_STANDARDS.lock``). It is recorded in the bundle
manifest so the validator (Batch 8) can recompute it and detect any post-approval tampering
with the locked contract surface.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass

#: Files that are locked once a blueprint is approved. Editing them is rule RMD-001.
IMMUTABLE_FILES: tuple[str, ...] = ("MATRIX_BLUEPRINT.yaml", "MATRIX_STANDARDS.lock")


def compute_contract_hash(immutable_files: Mapping[str, str]) -> str:
    """Deterministic ``sha256:`` digest over the immutable files.

    Order-independent: files are hashed in sorted path order with an explicit NUL separator
    so two bundles with identical locked content always produce the same hash.
    """
    h = hashlib.sha256()
    for path in sorted(immutable_files):
        h.update(path.encode("utf-8"))
        h.update(b"\0")
        h.update(immutable_files[path].encode("utf-8"))
        h.update(b"\0")
    return "sha256:" + h.hexdigest()


@dataclass(frozen=True)
class BlueprintContract:
    blueprint_id: str
    version: str
    immutable_files: tuple[str, ...]
    contract_hash: str

    def verify(self, current_files: Mapping[str, str]) -> bool:
        """Return True if the current immutable files still match the locked hash."""
        subset = {p: current_files[p] for p in self.immutable_files if p in current_files}
        if len(subset) != len(self.immutable_files):
            return False
        return compute_contract_hash(subset) == self.contract_hash


def build_contract(
    blueprint_id: str,
    version: str,
    immutable_files: Mapping[str, str],
) -> BlueprintContract:
    return BlueprintContract(
        blueprint_id=blueprint_id,
        version=version,
        immutable_files=tuple(sorted(immutable_files)),
        contract_hash=compute_contract_hash(immutable_files),
    )


__all__ = ["IMMUTABLE_FILES", "compute_contract_hash", "BlueprintContract", "build_contract"]
