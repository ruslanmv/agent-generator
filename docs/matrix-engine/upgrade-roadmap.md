# agent-generator → Matrix engine upgrade roadmap

The engine is upgraded in additive batches. Each batch keeps the existing CLI, frameworks,
and tests green (enforced by `tests/baseline/`).

| Batch | Title | Status | Version milestone |
|---|---|---|---|
| 0 | Audit, baseline + repo self-compliance | **done** | — |
| 1 | Public engine API boundary | **done** | — |
| 2 | Shared Matrix contracts | **done** | — |
| 3 | matrix-definitions standards loader | **done** | **0.2.0** ✅ released |
| 4 | Blueprint candidate engine | **done** | — |
| 5 | Controlled blueprint compiler **+ versioned regeneration** | **done** | — |
| 6 | Matrix Bundle exporter (strict + SBOM placeholder) | **done** | **0.3.0** ✅ released (M2 complete) |
| 7 | AI-coder prompt adapters | **done** | — |
| 8 | Validation, drift detection, repair (single authority) | **done** | **0.4.0** ✅ released (M3 complete) |
| 9 | Backend HTTP facade | **done** | — |
| 10 | Release evidence + dry-run publishing | **done** | **0.5.0** ✅ released (M4 complete) |
| 11 | Docs, examples, canaries, positioning | **done** | — |
| RC | Matrix Engine v1.0.0 | **done** | **1.0.0** ✅ released (M5 complete) |

## Delivered in Batches 0–2

**Batch 0 — self-compliance + baseline**
- `.github/CODEOWNERS` (satisfies GHA-003).
- `scripts/pin_github_actions.py` — reproducible GHA-002 remediation (`--check` / `--apply`).
- `tests/baseline/` — freezes CLI + public surface (the additive-upgrade guarantee).
- `scripts/check_matrix_engine_baseline.py` — engine smoke gate.
- Audit + compatibility + CI self-compliance docs.

**Batch 1 — public engine API boundary**
- `agent_generator.engine.AgentGenerator` with the six SDK methods Matrix Builder calls,
  plus additive helpers (`build_prompt_pack`, `generate_repair_prompt`, `export_zip`,
  `status`, `info`).
- `generate_controlled_blueprint` is wired to the real keyword planner.
- Deterministic by default (`EngineRuntime`, content-addressed ids, pinnable clock).
- `version.py`, `errors.py`, `runtime.py`, `result.py`.

**Batch 2 — shared Matrix contracts**
- `agent_generator.contracts` mirrors Matrix Builder's API schemas exactly and projects
  onto matrix-definitions' canonical schemas (`to_definitions_dict()`).
- Cross-repo contract tests (parity + schema validation).
- Back-compat adapter between the legacy `ProjectSpec` and the new contracts.

## Milestone meanings

| Milestone | Batches | Proves | Release |
|---|---|---|---|
| M1 | 0–3 | Integration: Matrix Builder can use SDK mode | `0.2.0` |
| M2 | 4–6 | Real generation: idea → candidates → scaffold → Matrix Bundle ZIP | `0.3.0` |
| M3 | 7–8 | The control loop / product promise: prompt → coder → validation → repair or approval | `0.4.0` |
| M4 | 9–10 | Platform: HTTP API + dry-run MatrixHub publish | `0.5.0` |
| M5 | 11 + RC | Public credibility: docs, examples, canaries, strict signing | `1.0.0` |

**M1 proves integration; M3 proves the product.** The smallest real demo is M3, not M1.

**Batch 4 — blueprint candidate engine**
- Deterministic idea parser (template detection, build-type refinement, auth/agent/api
  signals) — no LLM, no network.
- Three flagship template families matching the Matrix Builder UI:
  `github-repo-intelligence-agent`, `document-qa-agent`, `developer-portfolio-reviewer`,
  plus a generic fallback driven by the keyword planner.
- Deterministic candidate scoring with human-readable rationale; candidates map to the
  matrix-definitions quality profiles.
- `generate_controlled_blueprint` uses the template's curated page/route/task plan for
  flagship ideas. `examples/ideas/` regenerated from the real engine.

**Batch 5 — controlled blueprint compiler + versioned regeneration**
- `compile_bundle` produces a deterministic `CompiledBundle`: six MATRIX control files with
  real content, README + docs, stack-aware scaffold (runnable health route + test), coder
  prompts, and a manifest with per-file digests.
- Hash-locking: the immutable files (`MATRIX_BLUEPRINT.yaml`, `MATRIX_STANDARDS.lock`) feed an
  order-independent contract hash recorded in the manifest (`agent_generator.control`).
- `regenerate(base, change_request, change_type)` — pure versioned regeneration behind the
  "Update requirements" page; semver bump by change type, deterministic change detection,
  `RegenerationResult` with a human-readable summary. Base version is never mutated.
- `export_zip`/`generate_matrix_bundle` now build from the compiler's file plan.
- `tests/golden/` snapshots the full rendered bundle.

**Scope held from product direction (private-first):** Batch 10's live MatrixHub publishing
remains out of the MVP (dry-run + release evidence only).

## First integration milestone

Batches 1–3 together let Matrix Builder stop using its mock engine. After Batch 3 publishes
`0.2.0`, Matrix Builder sets `AGENT_GENERATOR_MODE=sdk` and calls the real engine. The
SDK-mode round-trip already works today against the in-progress engine (verified through
Matrix Builder's real adapter); Batch 3 adds the signed standards lock that makes it
production-meaningful.

## Carried-forward requirements (locked in by review)

- **Batch 6 — strict deterministic export.** The ZIP exporter must enforce fixed file
  ordering, fixed timestamps, stable line endings, and stable JSON/YAML formatting so
  checksums and golden tests are byte-stable. Batch 1's `export_zip` already pins ordering
  and timestamps; Batch 6 makes this a hard, tested contract.
- **Batch 8 — single validation authority.** Validation logic consolidates in
  agent-generator. Matrix Builder calls it and displays the result; it keeps no divergent
  validator. See `repo-boundary.md`.
- **Batch 10 — publishing is dry-run first.** Live MatrixHub publish waits until MatrixHub
  ships `POST /catalog/publish`, real signature/SBOM checks, and the matrix-definitions
  publication gates. Until then the engine prepares and dry-runs payloads only.

## Continuous Build program (post-1.0)

A second additive program adds the "Continue build" workflow (incremental batches, commit
timeline, tool-native handoffs). Engine track only; matrix-builder persistence/UX is a parallel
track.

| Batch | Title | Status | Release |
|---|---|---|---|
| E1 | Batch contracts + planner (`plan_batch`, `plan_repair_batch`) | **done** | — |
| E2 | Commit snapshots + diffs (`tree_hash`, `diff_submissions`, base-delta validation) | **done** | — |
| E3 | Tool-native exports (`CLAUDE.md`/`AGENTS.md`) + HTTP/CLI batch surface | **done** | **1.1.0** ✅ (milestone N1) |

**N1 — engine ready:** plan a batch, diff commits, hand off to a coder with its native
instruction file. Everything the control plane (matrix-builder) and the `mb` CLI need to build
the Continuous Build UX.
