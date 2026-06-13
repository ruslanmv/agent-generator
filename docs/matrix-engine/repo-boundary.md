# Repository boundary: what agent-generator owns

`agent-generator` is the **deterministic generation engine** behind Matrix Builder. This
document fixes the ownership line so responsibilities do not leak between repos as the engine
grows.

```
matrix-builder       → orchestration and public UX
agent-generator      → deterministic generation engine      (this repo)
matrix-definitions   → canonical rules and schemas
MatrixHub            → trusted registry and publishing layer
ruslanmv.com         → public standard and product authority
```

## agent-generator OWNS

- Idea parsing and normalization (`parse_idea`).
- Blueprint candidate generation (`generate_blueprint_candidates`).
- Controlled scaffold / blueprint compilation (`generate_controlled_blueprint`).
- Matrix Bundle export — ZIP, manifest, checksums, SBOM, provenance (`export_zip`, Batch 6).
- AI-coder prompt packs (`generate_coder_prompt_pack` / per-coder adapters, Batch 7).
- **Validation, drift detection, and repair prompts** — the single validation authority
  (Batch 8). After Batch 8, validation logic lives here and nowhere else.
- The standards **loader** that consumes signed matrix-definitions packs (Batch 3).

## agent-generator does NOT own

- The public Matrix Builder UX, accounts, quotas, or storage — that is **matrix-builder**.
- The MatrixHub registry UI, catalog, and live publishing endpoint — that is **MatrixHub**.
- **Authoring** canonical rules, schemas, or the Ruslan Magana Definitions — that is
  **matrix-definitions** (agent-generator consumes them; it never edits them).
- Marketing, the public standard pages, and product positioning — that is **ruslanmv.com**.

## Two consequences worth stating explicitly

**Single validation authority.** Matrix Builder must not keep its own divergent validator.
The target end state is: agent-generator validates, matrix-builder displays the result. A
state where matrix-builder says `approved` while agent-generator says `rejected` is a defect.

**No third schema universe.** Schemas are authored once in matrix-definitions. matrix-builder
and agent-generator are *consumers/mirrors* of those schemas (see
`src/agent_generator/contracts/SCHEMA_SOURCE.md`). Contract shapes are validated against the
matrix-definitions schemas in CI rather than re-invented.
