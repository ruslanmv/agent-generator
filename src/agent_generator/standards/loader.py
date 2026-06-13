"""Load and verify a matrix-definitions standards pack from disk.

Resolution order for the matrix-definitions root (the directory containing ``packs/`` and
``profiles/``):

1. an explicit ``root`` argument
2. the ``MATRIX_DEFINITIONS_DIR`` environment variable
3. the version-pinned snapshot bundled with this package (``standards/data/matrix-definitions``)

The bundled snapshot makes the engine self-contained: it can emit a real, verified
``MATRIX_STANDARDS.lock`` with no external checkout, while an env/explicit root lets
deployments point at a live, freshly-signed pack.

Verification posture (Batch 3):
* **checksums** are verified now via ``checksums.txt`` (fail-closed by default).
* **signature** (cosign) is verified in **warn mode**: the current pack ships a placeholder
  bundle, so a real cryptographic check is not yet possible. The loader records the
  signature state and warns rather than failing, until production signing lands.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import yaml

from agent_generator.errors import StandardsError
from agent_generator.standards.models import (
    ChecksumResult,
    PackManifest,
    PackRule,
    Profile,
    SignatureResult,
    StandardsPack,
)

BUNDLED_ROOT = Path(__file__).parent / "data" / "matrix-definitions"
_ENV_VAR = "MATRIX_DEFINITIONS_DIR"


def resolve_root(root: str | Path | None = None) -> Path:
    """Resolve the matrix-definitions root directory."""
    candidates: list[Path] = []
    if root is not None:
        candidates.append(Path(root))
    env = os.environ.get(_ENV_VAR)
    if env:
        candidates.append(Path(env))
    candidates.append(BUNDLED_ROOT)
    for candidate in candidates:
        if (candidate / "packs" / "current" / "manifest.json").exists():
            return candidate
    raise StandardsError(
        "No matrix-definitions pack found. Set MATRIX_DEFINITIONS_DIR to a checkout root "
        "containing packs/current/manifest.json, or reinstall the bundled snapshot."
    )


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _parse_checksums(text: str) -> dict[str, str]:
    """Parse ``sha256sum``-style lines: ``<digest><spaces><relative path>``."""
    result: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        digest, _, path = line.partition(" ")
        path = path.strip().lstrip("*").strip()
        if digest and path:
            result[path] = digest
    return result


def _verify_checksums(pack_dir: Path, expected: dict[str, str]) -> ChecksumResult:
    verified: list[str] = []
    mismatched: list[str] = []
    missing: list[str] = []
    for rel, digest in sorted(expected.items()):
        target = pack_dir / rel
        if not target.exists():
            missing.append(rel)
            continue
        if _sha256_file(target) == digest:
            verified.append(rel)
        else:
            mismatched.append(rel)
    return ChecksumResult(
        ok=not mismatched and not missing,
        verified=verified,
        mismatched=mismatched,
        missing=missing,
    )


def _verify_subject_digests(root: Path, bundle: dict) -> tuple[bool, list[str]]:
    """Verify the cosign bundle's subject digests against the actual files (Batch 10).

    Subject names are root-relative (e.g. ``packs/current/combined.pack.yaml``). Returns
    ``(all_match, mismatched)``; missing files count as not-matched.
    """
    subjects = bundle.get("subject") or []
    mismatched: list[str] = []
    checked = 0
    for subject in subjects:
        name = subject.get("name")
        digest = (subject.get("digest") or {}).get("sha256")
        target = root / name if name else None
        if not target or not target.exists():
            mismatched.append(name or "<unnamed>")
            continue
        checked += 1
        if _sha256_file(target) != digest:
            mismatched.append(name)
    return (checked > 0 and not mismatched), mismatched


def _verify_signature(
    root: Path, pack_dir: Path, manifest: PackManifest, mode: str
) -> SignatureResult:
    rel = manifest.signatures.get("cosign_bundle")
    if not rel:
        return SignatureResult(
            mode="missing", verified=False, warnings=["no cosign bundle declared"]
        )
    bundle_path = pack_dir / rel
    if not bundle_path.exists():
        return SignatureResult(
            mode="missing",
            verified=False,
            bundle_path=rel,
            warnings=[f"signature bundle not found: {rel}"],
        )
    try:
        bundle = json.loads(bundle_path.read_text())
    except json.JSONDecodeError as exc:
        return SignatureResult(
            mode="unverified",
            verified=False,
            bundle_path=rel,
            warnings=[f"unreadable signature bundle: {exc}"],
        )

    digests_ok, mismatched = _verify_subject_digests(root, bundle)
    if mismatched and any(m not in {None, "<unnamed>"} for m in mismatched):
        # Subjects are listed but their digests do not match: integrity failure.
        if mode == "require":
            raise StandardsError(f"standards pack signature digest mismatch: {mismatched}")
        return SignatureResult(
            mode="tampered",
            verified=False,
            bundle_path=rel,
            digests_verified=False,
            warnings=[f"cosign subject digests do not match pack files: {mismatched}"],
        )

    status = str(bundle.get("status", "")).lower()
    is_placeholder = status == "placeholder" or bundle.get("mode") == "development-metadata"
    if is_placeholder:
        if mode == "require":
            raise StandardsError(
                "signature_mode='require' but the pack carries a placeholder cosign bundle"
            )
        note = (
            "placeholder signature: subject digests verified, signing identity pending"
            if digests_ok
            else "placeholder signature; no verifiable subjects"
        )
        return SignatureResult(
            mode="placeholder",
            verified=False,
            bundle_path=rel,
            digests_verified=digests_ok,
            warnings=[note],
        )

    # A real (non-placeholder) bundle: cryptographic identity verification lands with CI signing.
    if mode == "require" and not digests_ok:
        raise StandardsError("standards pack signature could not be verified")
    return SignatureResult(
        mode="verified" if digests_ok else "unverified",
        verified=digests_ok,
        bundle_path=rel,
        digests_verified=digests_ok,
        warnings=[] if digests_ok else ["signature present but subjects unverifiable"],
    )


def _load_rules(pack_dir: Path, manifest: PackManifest) -> tuple[list[PackRule], str]:
    combined_rel = manifest.packs.get("combined", "combined.pack.yaml")
    combined_path = pack_dir / combined_rel
    if not combined_path.exists():
        raise StandardsError(f"combined pack not found: {combined_rel}")
    digest = _sha256_file(combined_path)
    data = yaml.safe_load(combined_path.read_text()) or {}
    rules = [PackRule(**rule) for rule in data.get("rules", [])]
    return rules, digest


def load_pack(
    root: str | Path | None = None,
    *,
    verify: bool = True,
    signature_mode: str = "warn",
) -> StandardsPack:
    """Load (and by default verify) the current standards pack."""
    resolved = resolve_root(root)
    pack_dir = resolved / "packs" / "current"
    manifest = PackManifest.model_validate_json((pack_dir / "manifest.json").read_text())

    expected = _parse_checksums((pack_dir / manifest.checksums).read_text())
    checksums = _verify_checksums(pack_dir, expected)
    if verify and not checksums.ok:
        raise StandardsError(
            f"standards pack checksum verification failed ({checksums.summary}); "
            f"mismatched={checksums.mismatched} missing={checksums.missing}"
        )

    signature = _verify_signature(resolved, pack_dir, manifest, signature_mode)
    rules, combined_digest = _load_rules(pack_dir, manifest)

    warnings = list(signature.warnings)
    if not checksums.ok:
        warnings.append(f"checksum verification not clean: {checksums.summary}")

    return StandardsPack(
        root=resolved,
        pack_dir=pack_dir,
        manifest=manifest,
        rules=rules,
        combined_digest=combined_digest,
        file_digests=expected,
        checksums=checksums,
        signature=signature,
        warnings=warnings,
    )


def load_profile(root: str | Path | None, profile_name: str) -> Profile:
    """Load a quality profile (``starter`` / ``standard`` / ``production`` / ``enterprise``)."""
    resolved = resolve_root(root)
    path = resolved / "profiles" / f"{profile_name}.yaml"
    if not path.exists():
        raise StandardsError(f"profile not found: {profile_name} ({path})")
    data = yaml.safe_load(path.read_text()) or {}
    return Profile(**data)


__all__ = ["BUNDLED_ROOT", "resolve_root", "load_pack", "load_profile"]
