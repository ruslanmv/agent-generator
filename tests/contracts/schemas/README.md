# Vendored matrix-definitions schemas

These JSON Schemas are **vendored copies** synced from
[`agent-matrix/matrix-definitions`](https://github.com/agent-matrix/matrix-definitions)
(`schemas/`). They exist so the cross-repo contract test
(`tests/contracts/test_matrix_definitions_schema.py`) runs hermetically in
`agent-generator` CI without needing the matrix-definitions repo checked out.

matrix-definitions remains the **source of truth**. To validate against a live
checkout instead of these copies, set `MATRIX_DEFINITIONS_DIR` to the
matrix-definitions repo root (the test will use `$MATRIX_DEFINITIONS_DIR/schemas`).

When matrix-definitions changes a schema, re-sync the relevant file here and bump
`agent_generator.contracts.CONTRACTS_VERSION` if a shared shape changed.

Synced files:

- `blueprint-candidate.schema.json`
- `matrix-blueprint.schema.json`
- `matrix-standards-lock.schema.json`
- `validation-report.schema.json`
