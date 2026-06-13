# agent-generator current-state audit (Batch 0)

This is the pre-upgrade inventory that the engine work is built on. The strategy is to
**harden, not rewrite**: the repository already contains the generation engine, CLI,
backend, frontend, tests, and packaging. The Matrix upgrade adds a governed contract layer
on top of those proven pieces.

## What already exists

| Area | State | Location |
|---|---|---|
| Generation frameworks (5) | CrewAI, CrewAI Flow, LangGraph, ReAct, WatsonX Orchestrate | `src/agent_generator/frameworks/` |
| LLM providers | WatsonX (default), OpenAI, OllaBridge | `src/agent_generator/providers/` |
| Planning pipeline | Keyword planner, LLM planner, spec normalizer | `src/agent_generator/planners/`, `application/planning_service.py` |
| Build pipeline | Spec -> framework code/YAML, artifact bundle | `application/build_service.py`, `renderers/` |
| Validators | Spec, Python AST, security, YAML | `src/agent_generator/validators/` |
| Domain models | `ProjectSpec`, `ArtifactBundle`, `CapabilityMatrix`, `RenderPlan` | `src/agent_generator/domain/` |
| CLI | `agent-generator generate ...` (+ `--version`) | `src/agent_generator/cli.py` |
| Backend API | 10 routers (health, projects, runs, marketplace, builds, …) | `backend/app/api/` |
| Frontend | Vite + React 18 + TS wizard (describe → framework → ZIP) | `frontend/` |
| CI/CD | 12 workflows; container build has cosign + SBOM + SLSA-3 | `.github/workflows/` |
| Observability | OTel traces + Sentry; Grafana/Prometheus stack | `backend/app/telemetry/`, `observability/` |

## What was missing for a Matrix Builder engine

| Gap | Addressed in |
|---|---|
| Public, stable SDK facade Matrix Builder can import | Batch 1 (`engine.py`) |
| Shared, versioned data contracts across repos | Batch 2 (`contracts/`) |
| Standards pack loader + `MATRIX_STANDARDS.lock` | Batch 3 |
| Blueprint candidate engine | Batch 4 |
| Controlled compiler + Matrix control files | Batch 5 |
| Matrix Bundle exporter (SBOM/provenance) | Batch 6 |
| Per-coder prompt adapters | Batch 7 |
| Drift detection + repair | Batch 8 |
| HTTP facade for the engine | Batch 9 |
| MatrixHub publishing + release evidence | Batch 10 |
| Self-compliance: `CODEOWNERS`, SHA-pinned actions | Batch 0 (this batch) |

## Frozen baseline

The pre-upgrade behavior is pinned by `tests/baseline/` and the smoke gate
`scripts/check_matrix_engine_baseline.py`. The compatibility promise: **the engine upgrade
is additive.** The CLI commands, the five frameworks, and the legacy public exports
(`Settings`, `get_settings`, `FRAMEWORKS`, `PROVIDERS`) keep working unchanged.
