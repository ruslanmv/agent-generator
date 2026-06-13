# Matrix Bundle export (Batch 6)

The exporter turns a compiled blueprint into a **byte-deterministic** Matrix Bundle ZIP. Two
exports of the same idea — on any machine, any run — produce identical bytes. That is a
correctness property: it makes version diffs meaningful and lets golden snapshots catch
unintended change.

## The strict contract

| Guarantee | How |
|---|---|
| Fixed file ordering | Entries written in sorted path order |
| Fixed timestamps | Every ZIP entry uses the ZIP epoch (1980-01-01) |
| Stable line endings | All content LF-normalized at compile time (`normalize_newlines`) |
| Stable JSON | `canonical_json`: sorted keys, 2-space indent, trailing newline |
| Stable YAML | `canonical_yaml`: sorted keys, block style, `allow_unicode` |
| Fixed compression | `ZIP_DEFLATED`, level 9, fixed permissions |

Normalization happens at **compile time**, so the digests recorded in the manifest and
checksums match the exact bytes written to the ZIP.

## Per-bundle artifacts

```
artifacts/
  sbom.cdx.json     CycloneDX 1.5 SBOM (placeholder), derived from the stack
  manifest.json     index of every file: path, kind, digest, size + contract_hash + sbom_ref
  checksums.txt     sha256sum format; the outermost index
```

These form three nested layers, each covering the previous so there is no hashing cycle:

```
content files + sbom.cdx.json
        └── manifest.json   (indexes content + sbom; excludes manifest + checksums)
                └── checksums.txt   (covers everything except itself)
```

Verify a downloaded bundle from its root:

```bash
sha256sum -c artifacts/checksums.txt
```

## SBOM status (honest by default)

`artifacts/sbom.cdx.json` is a **generation-time** SBOM: a CycloneDX document listing the
dependencies implied by the blueprint stack, marked `matrix:sbom-status: placeholder`. The
resolved, verified dependency SBOM and cryptographic signatures are produced by the release
pipeline (Batch 10). We never label an artifact as verified when it isn't.

## API

```python
engine = AgentGenerator(fixed_now=pinned)        # determinism for snapshots/tests
compiled = engine.compile_bundle(blueprint, version="1.1.0")   # CompiledBundle
zip_path = engine.export_zip(blueprint, "dist/app.zip", version="1.1.0")
```

`generate_matrix_bundle`'s file list and `manifest_digest` are the compiler's real files and
contract hash, so the bundle metadata the UI shows matches the downloadable ZIP exactly.

## Golden snapshot

`tests/golden/` pins the full rendered bundle for the GitHub flagship template. Refresh after
an intentional change:

```bash
UPDATE_GOLDEN=1 pytest tests/golden -q
```
