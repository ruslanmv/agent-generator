# Release evidence & MatrixHub publishing (Batch 10)

## Release evidence

`build_release_evidence(blueprint, version=...)` (or `compile_bundle(..., release_evidence=True)`)
adds, on top of the standard bundle:

- `artifacts/provenance.intoto.jsonl` — SLSA build provenance (in-toto v1) listing every
  payload file digest.
- `artifacts/cosign.bundle.json` — a cosign-style signature bundle.

The manifest and `checksums.txt` are rebuilt to cover them, preserving the nested-index
property:

```
payload + provenance → manifest.json → cosign.bundle.json → checksums.txt
```

Release evidence is **opt-in** — the default `compile_bundle` is unchanged, so M2/M3 bundles
and their golden snapshot are stable.

## Honest signing status

The cosign bundle is a development placeholder (`status: placeholder`) until keyless signing
runs in CI. What is verifiable now, and is verified, is **digest integrity**:
`verify_cosign_bundle(bundle, files)` checks every subject digest against the actual file and
returns `tampered` on any mismatch. The standards loader applies the same check to the pack's
own cosign bundle, so `SignatureResult.digests_verified` is now `True` for the bundled pack —
graduating Batch 3's blind warn mode into "digests verified, signing identity pending".

## MatrixHub publishing — dry-run only

Per the private-first product direction, **live publishing is out of the MVP**. The engine
prepares and dry-runs a publication, enforcing the trust gate:

```python
pub = engine.prepare_matrixhub_publication(blueprint, version="1.0.0",
                                           validation_report=report)
```

A bundle is publishable only when **all required artifacts are present** and **validation
approved it**:

| Outcome | When |
|---|---|
| `rejected` (missing artifacts) | a required file is absent (e.g. no provenance) |
| `needs-validation` | no approved `ValidationReport` was supplied |
| `accepted-dry-run` | release-ready and validation `approved` |

Required artifacts: README, `MATRIX_BLUEPRINT.yaml`, `MATRIX_STANDARDS.lock`, `docs/security.md`,
`docs/standards-report.md`, the SBOM, provenance, manifest, and checksums.

Live MatrixHub publishing waits on the matrix-hub track (a `POST /catalog/publish` endpoint,
real signature/SBOM verification, and the matrix-definitions publication gates) and is surfaced
later as **"Submit as public template"** — not in this milestone.
