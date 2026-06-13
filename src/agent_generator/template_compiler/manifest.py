"""Bundle manifest builder (Batch 5, hardened in Batch 6).

``artifacts/manifest.json`` is the machine-readable index of a compiled bundle: every file
with its digest and kind, the immutable-file list, the blueprint contract hash, and the SBOM
reference. It lists all files except the two index files it cannot describe without a cycle:
itself and ``checksums.txt`` (which is generated last and covers the manifest).
"""

from __future__ import annotations

from collections.abc import Sequence

from agent_generator.artifacts.canonical import canonical_json
from agent_generator.artifacts.checksums import CHECKSUMS_PATH
from agent_generator.artifacts.signatures import COSIGN_PATH
from agent_generator.template_compiler.file_plan import CompiledFile

MANIFEST_PATH = "artifacts/manifest.json"
# Index/signing files a manifest cannot describe without a cycle.
_INDEX_FILES = {MANIFEST_PATH, CHECKSUMS_PATH, COSIGN_PATH}


def build_manifest_json(
    *,
    blueprint_id: str,
    slug: str,
    version: str,
    files: Sequence[CompiledFile],
    immutable_files: Sequence[str],
    contract_hash: str,
    sbom_ref: str | None = None,
) -> str:
    payload = {
        "schema_version": "1.0",
        "blueprint_id": blueprint_id,
        "slug": slug,
        "version": version,
        "contract_hash": contract_hash,
        "immutable_files": sorted(immutable_files),
        "sbom_ref": sbom_ref,
        "files": [
            {"path": f.path, "kind": f.kind, "digest": f.digest, "size_bytes": f.size_bytes}
            for f in sorted(files, key=lambda f: f.path)
            if f.path not in _INDEX_FILES
        ],
    }
    return canonical_json(payload)


__all__ = ["MANIFEST_PATH", "build_manifest_json"]
