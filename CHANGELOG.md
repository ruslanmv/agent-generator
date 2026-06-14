# Changelog

## 0.2.0 (2026-06-14)

The Matrix Builder engine — the Matrix Builder-facing `AgentGenerator` SDK
(idea → blueprint → bundle → coder prompt → validation), the `mb` local-first CLI,
batch planning, commit snapshots/diffs, and repair prompts. This is the milestone that
unlocks matrix-definitions compatibility: it can load and verify a signed standards pack
(`compatibility.agent_generator >= 0.2.0`), so Matrix Builder can run in `AGENT_GENERATOR_MODE=sdk`.



The Continuous Build engine track (milestones N1): plan incremental batches, snapshot/diff
commits, and hand work to AI coders with tool-native instruction files.

### Batch planning (E1)

- `plan_batch(blueprint, goal_md, change_type)` — the next small change *inside the current
  version*: appends scoped tasks (continuing `TASK-NNN`), never mutates the blueprint or bumps
  the version. `BatchChangeType` {small-update, add-feature, fix-issue}; `BatchPlan` /
  `BatchExecutionRequest` contracts; deterministic `bat-…` ids.
- `plan_repair_batch(report)` — a `fix-issue` batch scoped to exactly the violating files.

### Commit snapshots and diffs (E2)

- `agent_generator.control.snapshot`: `tree_hash` (LF-normalized, order-independent),
  `diff_submissions` (added/changed/deleted + byte-stable unified `diff.patch`),
  `build_commit_manifest` (`CommitManifest` contract). CRLF working copies hash/diff
  identically to their LF originals.
- The validator gains `base_submission=`: change-scoped checks (forbidden/allowlist/secrets)
  run against the **batch delta**, while presence/dependency/architecture checks see the full
  head tree. Engine: `bundle_tree_hash`, `diff_bundles`, `build_commit`;
  `validate_ai_coder_patch` gains `base_repo_path`/`base_zip_path`.

### Tool-native exports + HTTP/CLI surface (E3)

- Each coder adapter emits a tool-native helper file: **`CLAUDE.md`** (Claude Code),
  **`AGENTS.md`** (Codex) — both officially supported instruction surfaces — and
  `MATRIX_INSTRUCTIONS.md` (Cursor/GitPilot/IBM Bob/generic), all contract-derived and ending
  in `MATRIX_STATUS`. Prompts gain batch context ("this batch only", parent commit).
- `coder_handoff(blueprint, coder, batch=…)` → `CoderHandoff` (prompt + helper files).
- HTTP: `POST /api/v1/batches/plan`, `/batches/prompt-packs`, `/commits/diff`.
- CLI: `agent-generator matrix batch plan|prompt` (`--helper-dir` writes the helper file).

All six coders retained; Cursor stays the conservative patch-scoped adapter (RMD-108) until
its docs are directly reviewable. 269 tests pass; `make lint` clean; golden snapshot stable.

## 1.0.0 (2026-06-12)

**Matrix Engine v1.0.0** — the public-credibility milestone (M5). agent-generator is now the
production deterministic engine behind Matrix Builder.

### Public credibility (Batch 11 + RC)

- **`agent-generator matrix` CLI**: `candidates`, `generate`, `export` (with
  `--release-evidence`), and `validate` (exit 0/1/2). The legacy `generate` default command and
  `--version` are preserved via a custom default-command group.
- **Acceptance script** (`scripts/acceptance.py`): the full promise — idea → 3 candidates →
  blueprint → prompt pack → release bundle → validate (approved) → dry-run publish → tamper
  (rejected). Runs with no credentials or network.
- **Canary suite** (`tests/canary/`): positive (the three flagship templates generate and
  validate clean), negative (forbidden-file, dependency-drift, denied-dependency, secret, and
  route-drift injections are all caught), release-bundle completeness, the acceptance script,
  the CLI flow, and **matrix-builder e2e in both SDK and HTTP modes**.
- Docs: quickstart, Ruslan Magana Definitions, HTTP API, plus README repositioning. README,
  package classifier (Production/Stable), and version frozen at 1.0.0.

### Verified at the freeze

236 tests pass; `make lint` clean; golden snapshot frozen; the acceptance script passes
verbatim; matrix-builder e2e green in SDK and HTTP modes. Live MatrixHub publishing remains a
post-1.0 feature, surfaced later as "Submit as public template".

## 0.5.0 (2026-06-12)

The platform milestone (M4): HTTP facade, versioning over the wire, release evidence, and a
dry-run MatrixHub publication gate.

### Backend HTTP facade (Batch 9)

- `agent_generator.http` — a thin, stateless FastAPI app over the SDK (`uvicorn
  agent_generator.http.app:app`, or `create_app()` to mount). Endpoints: `/health`,
  `/api/v1/standards/current`, `/ideas/parse`, `/blueprints/candidates`, `/blueprints`,
  `/blueprints/regenerate`, `/bundles`, `/prompts`, `/validations`, `/exports` (streams a
  deterministic ZIP). FastAPI is the optional `web` extra; the core engine never requires it.

### Release evidence + dry-run publishing (Batch 10)

- `agent_generator.release` — `build_release_evidence` adds SLSA provenance
  (`artifacts/provenance.intoto.jsonl`) and a cosign signature bundle
  (`artifacts/cosign.bundle.json`) to a bundle, rebuilding the manifest and checksums to
  cover them. The default `compile_bundle` is unchanged; evidence is opt-in.
- `agent_generator.publishing` — the MatrixHub trust gate (`prepare_matrixhub_publication`):
  **dry-run only**. Accepts a bundle only when all required artifacts are present and
  validation approved it; otherwise rejected/needs-validation. Live publishing remains out of
  the MVP.
- Standards signature verification graduated from blind warn mode to **subject-digest
  verification** (`SignatureResult.digests_verified`); `verify_cosign_bundle` detects tampering.

## 0.4.0 (2026-06-12)

The control loop (milestone M3): prompt → AI coder → validation → repair or approval.

### AI-coder prompt adapters (Batch 7)

- Per-coder adapters (`agent_generator.coder_adapters`) replace the single template. Each is
  grounded in the matrix-definitions rule that governs it — Claude Code (RMD-110), Codex/
  ChatGPT (RMD-111), Cursor (RMD-108), GitPilot (RMD-113), IBM Bob (RMD-112), generic
  (RMD-114) — and every prompt is task-scoped, cites the lock's RMD-1xx rules, includes the
  bundle-fetch URL, and ends with a `MATRIX_STATUS` stop condition (RMD-118).
- `generate_coder_prompt_pack` carries the coder's `handoff_mode`.

### Single validation authority (Batch 8)

- `agent_generator.control`: one validator for the whole ecosystem. Accepts a request, a repo
  directory, a ZIP, or a unified diff and normalizes them to a `Submission`.
- Full check set: forbidden/immutable contract files (RMD-001/002), allowlist scope (RMD-107),
  required files (DOC-001), dependency drift (RMD-003 denied / RMD-116 unapproved), secrets
  (SEC-001), and architecture/route drift (RMD-115).
- Returns `approved` / `needs-repair` / `rejected` with per-check summaries, a score, and a
  minimal bounded repair prompt (RMD-120). `validate_ai_coder_patch` is the entry point;
  Matrix Builder should retire its own drift adapter and call this.

## 0.3.0 (2026-06-12)

Real generation (milestone M2). The engine now turns an idea into template-aware candidates,
compiles a full hash-locked bundle, supports versioned regeneration, and exports a
byte-deterministic Matrix Bundle ZIP.

### Blueprint candidate engine (Batch 4)

- Deterministic idea parser with three flagship template families
  (`github-repo-intelligence-agent`, `document-qa-agent`, `developer-portfolio-reviewer`) and
  a generic fallback; scored candidates with human-readable rationale.

### Controlled compiler + versioned regeneration (Batch 5)

- `compile_bundle` → a deterministic `CompiledBundle`: six MATRIX control files, docs,
  stack-aware scaffold, prompts, and a manifest with per-file digests; immutable files are
  hash-locked into a contract hash (`agent_generator.control`).
- `regenerate(base, change_request, change_type)` → new version without mutating the base
  (the "Update requirements" capability); semver bump by change type.

### Strict Matrix Bundle exporter (Batch 6)

- Byte-deterministic export: fixed file ordering, fixed timestamps, LF line endings, and
  canonical JSON/YAML serialization (`agent_generator.artifacts.canonical`).
- Per-bundle `artifacts/manifest.json` (files + digests + contract hash + `sbom_ref`),
  `artifacts/checksums.txt` (sha256sum format, the outermost index), and
  `artifacts/sbom.cdx.json` (CycloneDX 1.5 placeholder derived from the stack).
- `export_zip` uses the strict packager; golden snapshot locks the full rendered bundle.

## 0.2.0 (2026-06-12)

The Matrix engine boundary. This release turns agent-generator into the deterministic engine
behind Matrix Builder, additively — the existing CLI, frameworks, and tests are unchanged.
This is the version matrix-definitions requires (`agent_generator >= 0.2.0`), so Matrix
Builder can now run in SDK mode (`AGENT_GENERATOR_MODE=sdk`).

### Public engine API (Batch 1)

- `agent_generator.engine.AgentGenerator`: the stable SDK Matrix Builder imports. Implements
  the six adapter methods (`parse_idea`, `generate_blueprint_candidates`,
  `generate_controlled_blueprint`, `generate_matrix_bundle`, `generate_coder_prompt_pack`,
  `validate_ai_coder_patch`) plus `generate_coder_prompt`/`validate_bundle` aliases and
  additive helpers (`build_prompt_pack`, `generate_repair_prompt`, `export_zip`).
- `generate_controlled_blueprint` is wired to the existing keyword planner.
- Deterministic by default (`runtime.py`); `errors.py`, `result.py`, `version.py`.

### Shared Matrix contracts (Batch 2)

- `agent_generator.contracts`: mirrors Matrix Builder's API schemas and projects onto
  matrix-definitions canonical schemas via `to_definitions_dict()`.
- Cross-repo contract tests (matrix-builder parity + matrix-definitions schema validation);
  back-compat adapter between the legacy `ProjectSpec` and the contracts.

### matrix-definitions standards loader (Batch 3)

- `agent_generator.standards`: loads a signed standards pack, verifies `checksums.txt`
  (fail-closed), verifies the cosign signature in **warn mode** (the pack ships a placeholder
  bundle), and checks engine compatibility.
- Emits a deterministic `MATRIX_STANDARDS.lock` from the active pack and a quality profile.
- Ships a version-pinned snapshot of matrix-definitions `2026.06.0` so the engine is
  self-contained; override with `MATRIX_DEFINITIONS_DIR`.
- `export_zip` now embeds the real standards lock.

### Repo self-compliance (Batch 0)

- `.github/CODEOWNERS` (GHA-003); `scripts/pin_github_actions.py` for GHA-002.
- `tests/baseline/` freezes the CLI/public surface; `scripts/check_matrix_engine_baseline.py`
  smoke gate; `docs/matrix-engine/` documentation.

## 0.1.3 (2026-04-01)

### New Architecture

- **Domain layer**: `ProjectSpec` canonical schema, `RenderPlan`, `CapabilityMatrix`
- **Planners**: `KeywordPlanner` (instant, no LLM), `LLMPlanner` (structured output), `SpecNormalizer`
- **Renderers**: CrewAI (11-file projects), LangGraph (StateGraph), WatsonX (YAML), `Packager` (ZIP)
- **Tool catalog**: 6 approved templates (web_search, pdf_reader, http_client, sql_query, file_writer, vector_search)
- **Validators**: Spec validation, Python AST + security scan, YAML validation, pipeline orchestrator

### Framework Upgrades

- CrewAI generator: real `@CrewBase`/`@agent`/`@task` decorators, agents.yaml + tasks.yaml config
- LangGraph generator: `StateGraph` with `TypedDict` state, `START`/`END` constants
- CrewAI Flow generator: `Flow[FlowState]` with `@start`/`@listen` decorators
- ReAct generator: real reasoning loop with tool registry and `MAX_ITERATIONS` guard
- WatsonX Orchestrate: already production-ready (unchanged)

### Web UI

- Migrated from Flask to FastAPI
- Enterprise 4-step wizard: Describe -> Plan & Edit -> Configure -> Generate & Export
- Glassmorphism dark theme with file tree, syntax highlighting, ZIP download
- OllaBridge inference integration for AI-enhanced planning
- Framework capability matrix with live validation
- Grouped tool selection (Data, Document, Integration)

### HF Spaces Demo

- Self-contained demo at https://huggingface.co/spaces/ruslanmv/agent-generator
- Works without LLM credentials (keyword-based planning)
- All 5 frameworks supported
- OllaBridge-compatible for real inference when connected

### Infrastructure

- Pydantic v1 validators migrated to v2 (`@field_validator`, `@model_validator`)
- Dependencies updated to latest (pydantic 2.12, fastapi 0.135, crewai 1.12, langgraph 1.1)
- 31 tests passing (up from 2)
- Updated README, docs, Dockerfile
- Python 3.10+ required (was 3.9+)

## 0.1.2 (2025-07-22)

- Initial alpha release
- CLI with 5 framework generators
- WatsonX + OpenAI providers
- Flask web UI
- MCP wrapper support
