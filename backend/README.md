# Agent Generator · backend

FastAPI service that powers the agent-generator wizard, Marketplace, and
agent runs across the **web**, **desktop** (Tauri), and **mobile**
(Capacitor) shells. Wraps the existing `agent-generator` CLI as a
network service, brokers Matrix Hub + OllaBridge, and streams runs over
WebSocket.

## What's wired today (Batches 15-23 — Phase B complete)

| Concern         | Status                                       |
|-----------------|----------------------------------------------|
| App factory     | `app.main:app` (FastAPI 0.115+, lifespan)    |
| Settings        | `pydantic-settings`, `AG_*` env vars         |
| Logging         | `structlog` (JSON in prod, console in dev)   |
| Health probes   | `/livez` · `/readyz` · `/healthz`            |
| Compatibility   | `GET /api/compatibility/catalogue` · `POST /api/compatibility/diagnose` (mirror of the frontend matrix — single source of truth) |
| DB              | SQLAlchemy 2 async (SQLite dev → Postgres prod) |
| Auth            | GitHub OAuth → JWT (HS256), HttpOnly cookie + Bearer header; first user / `AG_ADMIN_EMAIL` ⇒ admin |
| Projects        | CRUD + files; private/public visibility, admin override |
| Runs            | REST start + replay; in-process bus + WebSocket stream  |
| Marketplace     | Matrix Hub proxy with 60s in-process cache + offline fixture |
| Docker builds   | `/api/builds/docker` trigger + signed CI workflow (cosign keyless · SPDX SBOM · SLSA-3 provenance · multi-arch amd64/arm64) |
| Secrets         | Pluggable backend (`memory` for dev, `vault` for prod); project-scoped CRUD; values never returned by `list`, key charset locked to `[A-Za-z][A-Za-z0-9_]{0,127}` |
| OllaBridge      | `/api/ollabridge/pair` proxy → exchanges device code for token, persists `(server_url, token)` in the project's secrets store |
| Telemetry       | OpenTelemetry traces (OTLP gRPC, optional) + Sentry errors (DSN-gated); both opt-in via env so dev stays quiet |
| Audit log       | `AuditMiddleware` records every mutating `/api/*` call with actor / IP / UA / request id; admins read via `/api/admin/audit` |
| Docker image    | Multi-stage `uv` → `distroless`, non-root    |
| Tests           | `pytest` + `pytest-asyncio` + `pytest-cov` — 57/57 passing at 81% coverage |

## Develop

```sh
cd backend
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
cp .env.example .env

# Run with hot reload.
uvicorn app.main:app --reload --port 8000

# Open http://localhost:8000/docs for the OpenAPI UI.
```

## Test / lint / type-check

```sh
ruff check app tests
mypy
pytest
```

## Docker

```sh
docker build -t agent-generator-backend:dev .
docker run --rm -p 8000:8000 agent-generator-backend:dev
```

The container runs as the non-root `nonroot` user shipped by Distroless,
has no shell, and weighs ~80 MB. Drop in a tagged release with `cosign`
keyless + SBOM in Batch 20.

## API surface — Batches 15-16

```text
GET  /livez                          → liveness probe
GET  /readyz                         → readiness probe
GET  /healthz                        → combined health

GET  /api/compatibility/catalogue    → wizard / Marketplace facets
POST /api/compatibility/diagnose     → Review · Compatibility rows

GET  /api/auth/github/login          → 302 to GitHub authorize URL
GET  /api/auth/github/callback       ← OAuth return, issues JWT + cookie
POST /api/auth/refresh               → swap refresh token for new pair
POST /api/auth/logout                → clear session cookie
GET  /api/auth/me                    → current user profile (requires auth)

GET    /api/projects?mine=true       → list (own / public)
POST   /api/projects                 → create (returns 201)
GET    /api/projects/{id}            → read (private requires owner/admin)
PATCH  /api/projects/{id}            → partial update (owner/admin)
DELETE /api/projects/{id}            → remove (owner/admin, returns 204)

POST   /api/projects/{id}/runs       → start a run (background engine)
GET    /api/runs/{run_id}            → run header + status
GET    /api/runs/{run_id}/events?after=N → replay events from seq>N
WS     /ws/runs/{run_id}?token=...   → live event stream (JSON frames)
```

The Run engine is a stub today (synthetic trace + result events) so
the wizard Run console renders end-to-end. Batches 22-23 swap the
stub for a real CLI invocation against the user's framework.

```text
GET  /api/marketplace/agents           → list (cached 60s, fixture when offline)
GET  /api/marketplace/agents/{id}      → detail (cached 60s)
POST /api/marketplace/publish          → publish a project to Matrix Hub

POST /api/builds/docker                → trigger a Docker build (modes:
                                          stub, local docker buildx, remote)

GET    /api/projects/{pid}/secrets         → list keys (values never returned)
PUT    /api/projects/{pid}/secrets/{key}   → write / overwrite a value
GET    /api/projects/{pid}/secrets/{key}   → read a value
DELETE /api/projects/{pid}/secrets/{key}   → remove the entry (204)

POST   /api/ollabridge/pair                → exchange device code, persist
                                              (OLLABRIDGE_URL, OLLABRIDGE_TOKEN)
                                              in the project secrets store
GET    /api/ollabridge/status/{pid}        → is this project paired?
POST   /api/ollabridge/unpair              → drop the stored credentials (204)

GET    /api/admin/audit?method=&path=      → admin-only audit log viewer
```

Production image builds are produced by the
`.github/workflows/backend-image.yml` GitHub Actions pipeline:

- multi-arch `linux/amd64` + `linux/arm64`
- pushed to `ghcr.io/${owner}/agent-generator-backend`
- cosign **keyless** signature (Sigstore + OIDC, no long-lived keys)
- SPDX SBOM attached as a cosign attestation
- SLSA-3 build provenance attached via `actions/attest-build-provenance`
- a `verify` job at the end re-checks the signature against the GitHub
  OIDC issuer so a broken release never reaches production

### GitHub OAuth setup

1. https://github.com/settings/applications/new
2. Homepage URL: `${AG_PUBLIC_URL}` (e.g. `http://localhost:5173`)
3. Authorization callback URL: `${AG_PUBLIC_URL}/api/auth/github/callback`
4. Copy client id / secret into `AG_GITHUB_CLIENT_ID` /
   `AG_GITHUB_CLIENT_SECRET`.
5. Optional: set `AG_ADMIN_EMAIL` to lock down which GitHub identity
   becomes admin. Without it, the first user to log in wins.

The compatibility module is the **single source of truth** the
TypeScript frontend mirrors at build time. Parity tests live in
`tests/test_compatibility.py` and the wider end-to-end parity check
lands in Batch 30.
