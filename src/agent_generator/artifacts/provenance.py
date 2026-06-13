"""SLSA provenance (Batch 10) — deterministic in-toto attestation for a bundle.

Records what produced the bundle and the digests of every payload file. This is build
*metadata*; cryptographic signing happens in the release pipeline (CI). Marked accordingly so
trust stays honest.
"""

from __future__ import annotations

from collections.abc import Sequence

from agent_generator.artifacts.canonical import normalize_newlines
from agent_generator.contracts.common import JsonDict

PROVENANCE_PATH = "artifacts/provenance.intoto.jsonl"


def build_provenance(
    *,
    slug: str,
    version: str,
    contract_hash: str,
    subjects: Sequence[tuple[str, str]],  # (path, "sha256:...")
    timestamp: str,
    engine_version: str,
) -> str:
    """Return an in-toto SLSA provenance statement as a single JSONL line."""
    statement: JsonDict = {
        "_type": "https://in-toto.io/Statement/v1",
        "predicateType": "https://slsa.dev/provenance/v1",
        "subject": [
            {"name": path, "digest": {"sha256": digest.removeprefix("sha256:")}}
            for path, digest in sorted(subjects)
        ],
        "predicate": {
            "buildDefinition": {
                "buildType": "https://ruslanmv.com/matrix/agent-generator",
                "externalParameters": {"slug": slug, "version": version},
                "internalParameters": {"contract_hash": contract_hash},
            },
            "runDetails": {
                "builder": {"id": f"agent-generator@{engine_version}"},
                "metadata": {"startedOn": timestamp, "finishedOn": timestamp},
            },
            "status": "build-metadata",
            "note": "Generation-time provenance; cryptographic signing occurs at release.",
        },
    }
    # JSONL: one canonical JSON object on a single line.
    import json

    return normalize_newlines(json.dumps(statement, sort_keys=True, separators=(",", ":"))) + "\n"


__all__ = ["PROVENANCE_PATH", "build_provenance"]
