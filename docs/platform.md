# Platform overview

`agent-generator` ships in two shapes. The CLI (`pip install
agent-generator`) is the original one-shot generator. The **platform** is the
shape this page is about: one TypeScript codebase that runs as a web app, a
desktop app, and an Android app, on top of a single FastAPI backend.

## At a glance

```
                                 ┌──────────────────────────────┐
                                 │   frontend/  (Vite + React)  │
                                 │                              │
                                 │   one bundle, three shells   │
                                 └──────────────┬───────────────┘
                                                │ same dist/
              ┌──────────────────────┬──────────┴──────────┬──────────────────────┐
              ▼                      ▼                     ▼                      ▼
    ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
    │  Web (nginx)     │  │  Tauri 2 desktop │  │  Capacitor 6     │  │  iOS-ready       │
    │  Docker image    │  │  .dmg / .msi /   │  │  Android .aab/   │  │  (cap add ios)   │
    │                  │  │  .AppImage /     │  │  .apk            │  │                  │
    │                  │  │  .deb / .rpm     │  │                  │  │                  │
    └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘
             │                     │                     │                     │
             └─────────────────────┴──────────┬──────────┴─────────────────────┘
                                              ▼
                                ┌─────────────────────────────┐
                                │  backend/  (FastAPI · 81%)  │
                                │                             │
                                │  Auth · Projects · Runs WS  │
                                │  Marketplace · Builds       │
                                │  Secrets (Vault) · OllaBridge │
                                │  Telemetry · Audit log      │
                                └─────────────────────────────┘
```

## Three commands

```bash
make install   # CLI + backend + frontend
make test      # all the tests, in order
make start     # backend on :8000 + SPA on :5173
```

`make help` lists every target. The ones you'll reach for most:

| Target               | Outcome                                                            |
|----------------------|--------------------------------------------------------------------|
| `make install`       | Editable CLI install + `app-install` (backend `[dev]` extras + npm install for the SPA). |
| `make test`          | CLI pytest, then backend pytest, then `tsc --noEmit` + `vite build` on the SPA. |
| `make start`         | Uvicorn (`--reload`) + Vite, concurrently. Logs in `.run/`. Ctrl-C stops both. |
| `make stop`          | Kills the dev servers `make start` left running.                   |
| `make build`         | SPA `dist/`, `agent-generator-backend:dev` image, **plus** the desktop installer for this host (`.dmg` on macOS, `.msi`+setup `.exe` on Windows, `.AppImage`+`.deb`+`.rpm` on Linux). |
| `make build-android` | Capacitor sync + `gradlew assembleDebug` → `app-debug.apk`.        |

## Layout

| Path                       | What lives there                                                                 |
|----------------------------|----------------------------------------------------------------------------------|
| `frontend/`                | The Vite + React 18 + TS SPA. One bundle drives every shell.                     |
| `backend/`                 | FastAPI service (`app.main:app`). Auth, Projects, Runs, Marketplace, Builds, Secrets, OllaBridge, Telemetry, Audit. |
| `shells/desktop/`          | Tauri 2 wrapper. Tray, native menus, deep-link router, auto-update.              |
| `shells/mobile/`           | Capacitor 6 wrapper. Android first, iOS-ready.                                   |
| `e2e/web/`                 | Playwright smoke flows (golden path, marketplace, docker redirect).              |
| `e2e/mobile/`              | Maestro flows (wizard, marketplace, deep-link).                                  |
| `observability/`           | `docker compose` stack — OTel Collector + Prometheus + Loki + Tempo + Grafana.   |
| `deploy/helm/`             | Production Helm chart (`backend` + `web` + `Ingress`, HPA, non-root pod security). |
| `.github/workflows/`       | CI matrix: backend image, desktop signing, mobile signing, e2e, release.         |
| `src/agent_generator/`     | The original CLI (untouched).                                                    |

## Compatibility matrix

The platform's source of truth is the **compatibility matrix** — 8 frameworks ×
5 hyperscalers × 2 orchestration patterns × 7 models. The frontend exports
catalogues from `frontend/src/lib/{frameworks,hyperscalers,orchestration,
models,compatibility}.ts` and the backend mirrors them at
`backend/app/api/compatibility.py`. The wizard, the Marketplace, the
Compatibility card on Review, and the CLI all consume the same data.

To inspect from a shell:

```bash
curl -s http://localhost:8000/api/compatibility/catalogue | jq '.frameworks | map(.id)'
curl -s -X POST http://localhost:8000/api/compatibility/diagnose \
  -H 'content-type: application/json' \
  -d '{"framework":"langgraph","hyperscaler":"azure","pattern":"supervisor","model":"gpt-5.1"}' | jq
```

## Production deployment

The backend runs as a distroless, non-root, multi-arch image. The SPA
runs as nginx. The chart in `deploy/helm/agent-generator` wires both
behind a single Ingress so the SPA reaches the backend at `/api` and
`/ws` without CORS gymnastics. Secrets come from a Kubernetes `Secret`
you provision out-of-band (recommended: External Secrets Operator or
the Vault Agent Injector).

```bash
helm install agent-generator oci://ghcr.io/ruslanmv/charts/agent-generator \
  --version <released-version> \
  --namespace ag --create-namespace \
  --set ingress.hosts[0].host=agent-generator.example.com \
  --set telemetry.otlpEndpoint=otel-collector.observability.svc:4317
```

See [`deploy/helm/README.md`](../deploy/helm/README.md) for the
secret-wiring contract and HPA / probe defaults.

## Observability

`observability/docker-compose.yaml` is the local stack. Point
`AG_OTLP_ENDPOINT` at `http://localhost:4317` and the backend's traces,
metrics, and logs fan out to Tempo, Prometheus, and Loki. Grafana
boots with the `Agent Generator` dashboard auto-provisioned.

Sentry stays opt-in via `AG_SENTRY_DSN`; the release pipeline
(`.github/workflows/release-app.yml`) stamps the version on every tag
push so source maps + commit metadata flow automatically.

## Release pipeline

Tag `v*.*.*`. The orchestrator in `.github/workflows/release-app.yml`:

1. Drafts a GitHub Release with auto-generated notes.
2. Builds the web Docker image (cosign keyless + SBOM + SLSA-3 provenance).
3. Waits for `backend-image.yml`, `desktop.yml`, and `mobile.yml` to finish.
4. Packages and pushes the Helm chart to `oci://ghcr.io/<owner>/charts`.
5. Stamps Sentry with the release id.
6. Promotes the draft release to public once every dependency is green.

The signing material the production path consumes (Authenticode EV cert,
Apple notarization profile, GPG key, Android keystore, Play Store service
account) lives in repo Actions secrets — every signed workflow falls back
to producing an unsigned artefact when its secret is absent, so PR CI
keeps working for fork contributors.

## See also

- [`docs/complete-solution-plan.md`](complete-solution-plan.md) — the master plan that broke the work into 24 batches across six phases.
- [`docs/wizard-compatibility-design.md`](wizard-compatibility-design.md) — design doc for the hyperscaler-aware wizard.
- [`docs/wizard-orchestration-patterns-design.md`](wizard-orchestration-patterns-design.md) — Supervisor vs ReAct rationale.
- [`docs/architecture.md`](architecture.md) — original CLI architecture (still accurate for the CLI surface).
- [`docs/production-readiness.md`](production-readiness.md) — pre-existing production checklist.
