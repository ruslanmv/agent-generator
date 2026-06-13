"""Attach release evidence to a compiled bundle (Batch 10).

Adds ``artifacts/provenance.intoto.jsonl`` (SLSA build provenance) and
``artifacts/cosign.bundle.json`` (signature placeholder) to a compiled bundle, then rebuilds
the manifest and checksums so they cover the new artifacts. The core ``compile_bundle`` is
left unchanged; release evidence is an explicit, opt-in layer.

Nesting (each layer covers the previous):
  payload + provenance  →  manifest.json  →  cosign.bundle.json  →  checksums.txt
"""

from __future__ import annotations

from agent_generator.artifacts.checksums import CHECKSUMS_PATH, build_checksums_txt
from agent_generator.artifacts.provenance import PROVENANCE_PATH, build_provenance
from agent_generator.artifacts.signatures import COSIGN_PATH, build_cosign_bundle
from agent_generator.contracts.blueprint import BlueprintResult
from agent_generator.template_compiler.file_plan import CompiledBundle, CompiledFile
from agent_generator.template_compiler.manifest import MANIFEST_PATH, build_manifest_json

_EVIDENCE_PATHS = {MANIFEST_PATH, CHECKSUMS_PATH, PROVENANCE_PATH, COSIGN_PATH}


def add_release_evidence(
    compiled: CompiledBundle,
    blueprint: BlueprintResult,
    *,
    engine_version: str,
    timestamp: str,
) -> CompiledBundle:
    """Return a new bundle with provenance, signature, and rebuilt manifest/checksums."""
    # Payload = everything except the index/evidence layer.
    payload = [f for f in compiled.files if f.path not in _EVIDENCE_PATHS]

    # 1. Provenance over the payload.
    provenance = CompiledFile(
        PROVENANCE_PATH,
        build_provenance(
            slug=compiled.slug,
            version=compiled.version,
            contract_hash=compiled.contract_hash,
            subjects=[(f.path, f.digest) for f in payload],
            timestamp=timestamp,
            engine_version=engine_version,
        ),
        kind="provenance",
    )
    payload_with_prov = [*payload, provenance]

    # 2. Manifest indexes payload + provenance (excludes manifest/checksums/cosign).
    manifest = CompiledFile(
        MANIFEST_PATH,
        build_manifest_json(
            blueprint_id=compiled.blueprint_id,
            slug=compiled.slug,
            version=compiled.version,
            files=payload_with_prov,
            immutable_files=compiled.immutable_files,
            contract_hash=compiled.contract_hash,
            sbom_ref="artifacts/sbom.cdx.json",
        ),
        kind="manifest",
    )

    # 3. Cosign signs the manifest + provenance (the bundle's indexes).
    cosign = CompiledFile(
        COSIGN_PATH,
        build_cosign_bundle(
            subjects=[(MANIFEST_PATH, manifest.digest), (PROVENANCE_PATH, provenance.digest)],
            version=engine_version,
            timestamp=timestamp,
        ),
        kind="signature",
    )

    files = [*payload_with_prov, manifest, cosign]

    # 4. checksums.txt covers everything except itself.
    checksums = CompiledFile(
        CHECKSUMS_PATH,
        build_checksums_txt({f.path: f.content for f in files}),
        kind="checksums",
    )
    files.append(checksums)

    return CompiledBundle(
        blueprint_id=compiled.blueprint_id,
        slug=compiled.slug,
        version=compiled.version,
        files=tuple(sorted(files, key=lambda f: f.path)),
        contract_hash=compiled.contract_hash,
        immutable_files=compiled.immutable_files,
    )


__all__ = ["add_release_evidence"]
