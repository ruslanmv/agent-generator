# Production readiness

The enterprise checklist. Skim before you ship.

## Where we are

Release candidate. CLI is stable; the platform is wired end-to-end and
running in pre-prod environments.

## One pipeline, three entry points

```
Prompt → PlanningService → ProjectSpec → BuildService → ArtifactBundle
```

CLI, web UI, and REST API all go through it. No alternate paths, no
duplicate code, no untested branches.

## Release gates

A release ships only when all of these are green:

- CI passes on Python 3.10, 3.11, 3.12
- `pytest` passes (51+ tests)
- Wheel + sdist build cleanly
- `ruff` + `mypy` clean
- Security validator enabled on every generated artifact
- No errors in generated outputs across the smoke matrix

## Framework maturity

| Framework | Maturity | Output |
|---|---|---|
| CrewAI | Beta | Python + YAML |
| LangGraph | Beta | Python |
| WatsonX Orchestrate | Stable | YAML |
| CrewAI Flow | Beta | Python |
| ReAct | Beta | Python |

For most enterprise rollouts we recommend **LangGraph** as the primary
target — typed state, explicit graphs, easiest to test and observe.

## Security guarantees

Every generated file passes through the AST-based scanner. It blocks:

- `eval()` and `exec()`
- `os.system()`
- bare `subprocess` calls
- `requests`/`httpx` calls without an explicit `timeout`

The scanner is on by default. There is no flag to disable it. If you
need to ship code with one of these patterns, override it in your fork
of the tool template rather than in the generator.

## What you should know going in

- LLM planning enrichment is **off** by default. Turn it on per-call
  when you need richer multi-agent decomposition.
- Some legacy single-file generators (`frameworks/*`) still exist
  alongside the spec-first renderers. They share the same domain
  models, so output is consistent — but new work should target the
  spec-first path.
- The platform stores **only the spec**, not the rendered output. If
  you need diffs across runs, save the bundle alongside the spec.

## Operational defaults

- Backend image: distroless, non-root, multi-arch.
- SPA: nginx with strict CSP.
- Helm chart ships with HPA, liveness + readiness probes, and a
  `PodSecurityPolicy`-equivalent `securityContext` (read-only root FS,
  `runAsNonRoot: true`, `seccompProfile: RuntimeDefault`).
- Secrets: never baked into images. Use External Secrets or Vault.
- Telemetry: OpenTelemetry-first; Sentry is opt-in.

## When to escalate

Open a GitHub issue with the `production` label if you hit:

- Generated artifacts that fail the security scan against safe input.
- Reproducibility drift (same spec, different output).
- Pipeline regressions on the supported Python matrix.

---

**Next:** [Release process](release-process.md)
