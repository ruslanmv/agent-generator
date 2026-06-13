# Contract schema provenance

The contracts in this package are kept in agreement with two upstream sources:

1. **matrix-definitions** — the canonical, signed JSON Schemas (source of truth). Our
   models project onto these via `to_definitions_dict()` and are validated against the
   vendored copies in `tests/contracts/schemas/` by
   `tests/contracts/test_matrix_definitions_schema.py`.
2. **matrix-builder** — the API schema shapes our models mirror field-for-field, verified by
   `tests/contracts/test_matrix_builder_parity.py`.

This file records what those contracts were synced against, so contract drift is auditable.

## Provenance

| Field | Value |
|---|---|
| Contracts version (`CONTRACTS_VERSION`) | `1.0` |
| matrix-definitions pack version | `2026.06.0` |
| matrix-builder version (mirrored API shapes) | `0.9.0-batch.9` |
| Sync date | `2026-06-12` |
| Synced by | Batch 2 (shared Matrix contracts) |

## Vendored schema digests (sha256)

These are the matrix-definitions schemas backing the cross-repo validation test. Re-compute
and update on every re-sync (`sha256sum tests/contracts/schemas/*.schema.json`).

| Schema | Digest |
|---|---|
| `blueprint-candidate.schema.json` | `sha256:96206896897d32c0f6fd0367561b2bc0850a01a327ee64deec905dd0b10c89f2` |
| `matrix-blueprint.schema.json` | `sha256:1f5dda869818fc8369cf4824e3e001e74083480af82e01864912378dfc101dba` |
| `matrix-standards-lock.schema.json` | `sha256:d7fcb83e91783fa2b06b11d32a431273d126e719ab4f51fb5478571abc35b718` |
| `validation-report.schema.json` | `sha256:fccde8c128f84aa39e11497cd6d32661b9dde1cdecf3a2ee7cf6ff4ffb66a612` |

## Re-sync procedure

1. Copy the changed schema(s) from `matrix-definitions/schemas/` into
   `tests/contracts/schemas/`.
2. Update the digest table above and the versions/date.
3. Adjust the affected Pydantic model and its `to_definitions_dict()` projection.
4. If a shared shape changed, bump `CONTRACTS_VERSION`.
5. Run `pytest tests/contracts/` — both parity and schema-validation tests must pass.

> Note: Batch 3 (the standards loader) records the **runtime** pack version and digest into
> each generated `MATRIX_STANDARDS.lock`. This file tracks the **build-time** schema source
> the contract models were written against.
