"""Signature wiring (Batch 10) — cosign bundle placeholder + digest verification.

The engine emits a cosign *bundle* that lists the signed subjects and their digests. Like
matrix-definitions, it is a development placeholder (``status: placeholder``) until keyless
signing runs in CI — we never claim a verified cryptographic signature we don't have.

What we *can* verify now, and do, is **digest integrity**: that the subject digests in a
bundle match the actual files. ``verify_cosign_bundle`` performs that check, graduating the
standards loader's plain warn mode into "digests verified, signing identity pending".
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from agent_generator.artifacts.canonical import canonical_json

COSIGN_PATH = "artifacts/cosign.bundle.json"


def build_cosign_bundle(
    *,
    subjects: Sequence[tuple[str, str]],  # (path, "sha256:...")
    version: str,
    timestamp: str,
) -> str:
    """Return a deterministic cosign-style bundle (development placeholder)."""
    doc = {
        "schema_version": "1.0",
        "status": "placeholder",
        "mode": "development-metadata",
        "warning": (
            "Not a production cryptographic signature. Release artifacts are Cosign "
            "keyless-signed in GitHub Actions."
        ),
        "created_at": timestamp,
        "tool": f"agent-generator@{version}",
        "subject": [
            {"name": path, "digest": {"sha256": digest.removeprefix("sha256:")}}
            for path, digest in sorted(subjects)
        ],
    }
    return canonical_json(doc)


@dataclass(frozen=True)
class SignatureVerification:
    mode: str  # "placeholder" | "unverified" | "tampered" | "missing"
    digests_verified: bool
    mismatched: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def verify_cosign_bundle(bundle_text: str, files: Mapping[str, str]) -> SignatureVerification:
    """Verify the bundle's subject digests against ``files`` (path -> content).

    Returns ``digests_verified=True`` when every listed subject's digest matches the file. A
    mismatch yields ``mode="tampered"``. Cryptographic identity verification is not yet
    enabled, so a clean placeholder bundle reports ``mode="placeholder"``.
    """
    try:
        bundle = json.loads(bundle_text)
    except json.JSONDecodeError as exc:
        return SignatureVerification("unverified", False, warnings=[f"unreadable bundle: {exc}"])

    subjects = bundle.get("subject") or []
    mismatched: list[str] = []
    missing: list[str] = []
    for subject in subjects:
        name = subject.get("name")
        digest = (subject.get("digest") or {}).get("sha256")
        if name not in files:
            missing.append(name)
            continue
        if _sha256_hex(files[name]) != digest:
            mismatched.append(name)

    if mismatched:
        return SignatureVerification(
            "tampered",
            False,
            mismatched=mismatched,
            missing=missing,
            warnings=["subject digests do not match files; bundle integrity failed"],
        )
    status = str(bundle.get("status", "")).lower()
    mode = "placeholder" if status == "placeholder" else "unverified"
    warnings = []
    if mode == "placeholder":
        warnings.append("placeholder signature: digests verified, signing identity pending")
    return SignatureVerification(
        mode, bool(subjects) and not missing, missing=missing, warnings=warnings
    )


__all__ = ["COSIGN_PATH", "build_cosign_bundle", "verify_cosign_bundle", "SignatureVerification"]
