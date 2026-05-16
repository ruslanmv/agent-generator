# Platform overview

This page is about the **team-ready** shape of agent-generator: one
TypeScript codebase that runs as a web app, a desktop app, and an
Android app, all backed by one FastAPI service.

If you just need the CLI, you don't need any of this — `pip install
agent-generator` and you're done.

## The picture

```
              ┌──────────────────────────────┐
              │  frontend/  (Vite + React)   │
              │  one bundle, three shells    │
              └─────────────┬────────────────┘
                            │ same dist/
       ┌────────────┬───────┴───────┬────────────┐
       ▼            ▼               ▼            ▼
   Web (nginx)  Tauri desktop  Capacitor Android  iOS-ready
                .dmg/.msi/...   .aab/.apk        (cap add ios)
       └────────────┴───────┬───────┴────────────┘
                            ▼
              ┌──────────────────────────────┐
              │  backend/  (FastAPI)         │
              │  Auth · Projects · Runs WS   │
              │  Marketplace · Builds        │
              │  Secrets (Vault) · Audit log │
              └──────────────────────────────┘
```

## Three commands

```bash
make install   # CLI + backend + frontend
make test      # all the tests, in order
make start     # backend on :8000 + SPA on :5173
```

`make help` lists every target. The ones you'll reach for:

| Target | What it does |
|---|---|
| `make install` | Editable CLI install + backend `[dev]` extras + `npm install` for the SPA. |
| `make test` | CLI pytest, backend pytest, `tsc --noEmit` + `vite build`. |
| `make start` | Uvicorn (`--reload`) + Vite together. Logs in `.run/`. Ctrl-C stops both. |
| `make stop` | Kill the dev servers `make start` left running. |
| `make build` | SPA `dist/`, the backend Docker image, and the desktop installer for your host. |
| `make build-android` | Capacitor sync + `gradlew assembleDebug` → `app-debug.apk`. |

## Where things live

| Path | What it is |
|---|---|
| `frontend/` | Vite + React SPA. One bundle drives every shell. |
| `backend/` | FastAPI service (`app.main:app`). |
| `shells/desktop/` | Tauri 2 wrapper. Tray, native menus, deep links, auto-update. |
| `shells/mobile/` | Capacitor 6 wrapper. Android first, iOS-ready. |
| `e2e/web/` | Playwright smoke flows. |
| `e2e/mobile/` | Maestro flows. |
| `observability/` | Docker Compose stack: OTel · Prometheus · Loki · Tempo · Grafana. |
| `deploy/helm/` | Production Helm chart (backend + web + Ingress, HPA, non-root pods). |
| `.github/workflows/` | CI: backend image, desktop signing, mobile signing, e2e, release. |
| `src/agent_generator/` | The original CLI. |

## One source of truth for compatibility

The wizard, the Marketplace, the Review screen and the CLI all consume
the same compatibility matrix — **8 frameworks × 5 hyperscalers × 2
orchestration patterns × 7 models**. The frontend exports the
catalogues from `frontend/src/lib/{frameworks,hyperscalers,
orchestration,models,compatibility}.ts`; the backend mirrors them at
`backend/app/api/compatibility.py`.

To check it from a shell:

```bash
curl -s http://localhost:8000/api/compatibility/catalogue | jq '.frameworks[].id'

curl -s -X POST http://localhost:8000/api/compatibility/diagnose \
  -H 'content-type: application/json' \
  -d '{"framework":"langgraph","hyperscaler":"azure",
       "pattern":"supervisor","model":"gpt-5.1"}' | jq
```

## Deploying it for real

The backend is a distroless, non-root, multi-arch image. The SPA is
nginx. The Helm chart wires both behind one Ingress so the SPA reaches
the backend at `/api` and `/ws` without CORS gymnastics.

```bash
helm install agent-generator \
  oci://ghcr.io/ruslanmv/charts/agent-generator \
  --version <released-version> \
  --namespace ag --create-namespace \
  --set ingress.hosts[0].host=agent-generator.example.com \
  --set telemetry.otlpEndpoint=otel-collector.observability.svc:4317
```

Secrets come from a Kubernetes `Secret` you provision out-of-band
(External Secrets Operator or Vault Agent Injector recommended). See
[`deploy/helm/README.md`](../deploy/helm/README.md) for the
secret-wiring contract and HPA / probe defaults.

## Observability

`observability/docker-compose.yaml` is the local stack. Point
`AG_OTLP_ENDPOINT` at `http://localhost:4317` and the backend's traces,
metrics, and logs fan out to Tempo, Prometheus, and Loki. Grafana boots
with the **Agent Generator** dashboard pre-loaded.

Sentry stays opt-in via `AG_SENTRY_DSN`. The release pipeline stamps
the version on every tag push so source maps and commit metadata flow
through automatically.

## How a release happens

Tag `v*.*.*` and `.github/workflows/release-app.yml`:

1. Drafts a GitHub Release with auto-generated notes.
2. Builds the web Docker image (cosign keyless + SBOM + SLSA-3
   provenance).
3. Waits for `backend-image.yml`, `desktop.yml`, and `mobile.yml`.
4. Packages and pushes the Helm chart to `oci://ghcr.io/<owner>/charts`.
5. Stamps Sentry with the release id.
6. Promotes the draft release once every dependency is green.

Signing material (Authenticode EV cert, Apple notarisation profile, GPG
key, Android keystore, Play Store service account) lives in Actions
secrets. Every signed workflow falls back to producing an unsigned
artefact when its secret is absent — so PR CI keeps working for fork
contributors.

## See also

- [`docs/complete-solution-plan.md`](complete-solution-plan.md) — master plan, 24 batches across six phases.
- [`docs/wizard-compatibility-design.md`](wizard-compatibility-design.md) — hyperscaler-aware wizard design.
- [`docs/wizard-orchestration-patterns-design.md`](wizard-orchestration-patterns-design.md) — Supervisor vs ReAct rationale.
- [`docs/architecture.md`](architecture.md) — CLI architecture.
- [`docs/production-readiness.md`](production-readiness.md) — release checklist.
