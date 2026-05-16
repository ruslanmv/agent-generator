# Agent Generator — Complete End-to-End Solution Plan

> Status: **design draft (master plan)** · supersedes the per-feature design
> docs by referencing them · Owner: full-stack · Target: Batches 9 → 32
>
> Plan only — no code lands as part of this change. Each batch in the
> table at the bottom is independently shippable.

## 0 · TL;DR

We ship **one TypeScript codebase** that runs as:

| Shell | Artefact | Audience |
|---|---|---|
| Web | Docker image (Batch 8 — shipped) | Self-hosted / cloud |
| Desktop (Tauri 2) | `.exe` / `.msi` · `.dmg` · `.AppImage` / `.deb` / `.rpm` | macOS · Windows · Linux |
| Mobile (Capacitor 6) | `.aab` / `.apk` (Android) · `.ipa` (iOS-ready) | Field use, demos |

A **single FastAPI backend** powers all three. The frontend's runtime
`platform.ts` layer routes file-system / secret-store / deep-link / OS
notification calls to the right shell — `fetch` everywhere else.

Total scope: **24 new batches** (9 → 32) on top of the 8 already
shipped on `claude/implement-agent-generator-9OP2X`.

## 1 · What the new design bundle adds

The new Claude Design handoff (`ns2-n8nKC0QbgfOkJHLRNg`) is a superset of
the previous one, with three substantive new surfaces:

| Surface | New? | Source file |
|---|---|---|
| **Test (Chat) tab** | Yes | `desktop-chat.jsx` |
| **Docker wizard** (5 steps) | Yes | `desktop-docker.jsx` |
| **Framework & Model v2** | Yes (matches our design doc) | `desktop-framework-v2.jsx` |
| **Compatibility data layer** | Yes (matches our design doc) | `compatibility.jsx` |
| **Settings · 7 tabs** | Expanded | `desktop-admin.jsx` |
| **About modal · 7 sections** | Expanded | `desktop-admin.jsx` |
| **Marketplace · Hyperscaler facet** | Expanded | `desktop-marketplace.jsx` |
| Everything else | unchanged | — |

Two design docs already on the branch cover the Framework v2 +
Compatibility data layer:

- [`docs/wizard-compatibility-design.md`](./wizard-compatibility-design.md)
- [`docs/wizard-orchestration-patterns-design.md`](./wizard-orchestration-patterns-design.md)

This master plan absorbs both and adds the three new surfaces plus the
backend, platform abstraction, Tauri shell, Capacitor shell, and
production-readiness work.

## 2 · Top-level architecture

```
┌─────────────────────────────────── User-facing artefacts ────────────────────────────────────┐
│                                                                                              │
│   ╔══════════════╗   ╔══════════════╗   ╔══════════════╗   ╔══════════════╗   ╔════════════╗ │
│   ║   Web        ║   ║   Windows    ║   ║   macOS      ║   ║   Linux      ║   ║  Android   ║ │
│   ║   nginx+SPA  ║   ║   .exe/.msi  ║   ║   .dmg       ║   ║  .AppImage   ║   ║   .aab     ║ │
│   ╚══════════════╝   ╚══════════════╝   ╚══════════════╝   ╚══════════════╝   ╚════════════╝ │
│         ▲                  ▲                  ▲                  ▲                  ▲       │
│         │  same dist/      │  Tauri 2 shell ──┴──── shells/desktop                  │       │
│         │                                                          Capacitor 6 ─────┘       │
│   ┌─────┴────────────────────────────────────────────────────────────────────────────┐      │
│   │  frontend/                                                                       │      │
│   │   Vite + React 18 + TS strict · routes · components · lib/platform.ts            │      │
│   │   talks to backend over fetch + WebSocket · no business logic here               │      │
│   └─────┬──────────────────────────────────────────────────────────────────────────┬─┘      │
│         │ HTTPS + WS                                                               │        │
│   ┌─────▼──────────────────────────────────────────────────────────────────────────▼──┐     │
│   │  backend/  (FastAPI · Python 3.11)                                                │     │
│   │                                                                                   │     │
│   │   Wrapper around the existing `agent_generator` CLI + new endpoints:              │     │
│   │     /api/compatibility    /api/projects   /api/projects/{id}/run                  │     │
│   │     /api/marketplace      /api/docker     /api/docker/{id}/build (WS)             │     │
│   │     /api/secrets/backends /api/ollabridge/pair                                    │     │
│   │     /api/settings         /api/auth                                               │     │
│   │                                                                                   │     │
│   │   Adapters: MatrixHub catalog · BuildKit (buildx) · cosign · Vault/AWS-SM/        │     │
│   │             Azure-KV/IBM-SM/Doppler/K8s/GCP-SM · OllaBridge `/device/pair-simple` │     │
│   │   Storage: SQLite (default) → swappable to Postgres · Alembic migrations          │     │
│   │   Auth:    OAuth (GitHub/Google/Azure-AD) + local admin · sessions in cookie      │     │
│   │   Streaming: WebSocket for /run and /docker/build; SSE fallback                   │     │
│   │   Telemetry: OpenTelemetry traces + Prometheus metrics + structured logs (JSON)   │     │
│   └─────┬──────────────────────────────────────────────────────────────────────────┬──┘     │
│         │                                                                          │        │
│   ┌─────▼─────┐  ┌──────────────────────┐  ┌─────────────────┐  ┌─────────────────▼─┐      │
│   │ Postgres/ │  │ MatrixHub            │  │ OllaBridge       │  │  Secret backends   │     │
│   │ SQLite    │  │ catalog API          │  │ Cloud /v1 + /pair│  │  (Vault, KV, SM…)  │     │
│   └───────────┘  └──────────────────────┘  └─────────────────┘  └────────────────────┘     │
│                                                                                              │
└───────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 3 · Monorepo layout (target)

```
agent-generator/
├── src/agent_generator/         existing Python CLI (don't touch)
├── frontend/                     Vite + React + TS  (Batches 1–8 shipped)
│   ├── src/
│   │   ├── lib/
│   │   │   ├── compatibility.ts             (Batch 9)
│   │   │   ├── platform.ts                  (Batch 24)
│   │   │   └── api/                         typed fetch + WS client
│   │   ├── pages/
│   │   │   ├── wizard/ (steps + Framework v2)        (Batches 10–11)
│   │   │   ├── chat/   (Test surface)                (Batch 12)
│   │   │   └── docker/ (5-step Docker wizard)        (Batches 13–14)
│   │   └── …
│   ├── Dockerfile                Batch 8
│   └── nginx.conf
│
├── backend/                      FastAPI service     (Batches 15–23)
│   ├── pyproject.toml
│   ├── app/
│   │   ├── main.py               FastAPI app + lifespan
│   │   ├── api/                  routers (compat, projects, run, marketplace,
│   │   │                                  docker, secrets, ollabridge, auth)
│   │   ├── services/             agent-gen-CLI wrapper, BuildKit, cosign,
│   │   │                         secret-backend adapters, telemetry
│   │   ├── models/               SQLAlchemy models + Pydantic schemas
│   │   ├── migrations/           Alembic
│   │   └── settings.py           pydantic-settings
│   ├── tests/                    pytest + httpx
│   └── Dockerfile                multi-stage: uv build → distroless
│
├── shells/
│   ├── desktop/                  Tauri 2 wrapper       (Batches 25–27)
│   │   ├── src-tauri/
│   │   │   ├── tauri.conf.json
│   │   │   ├── Cargo.toml
│   │   │   ├── icons/
│   │   │   └── src/main.rs       ~50 lines: deep-link handler, updater, tray
│   │   └── package.json
│   └── mobile/                   Capacitor 6 wrapper   (Batches 28–29)
│       ├── capacitor.config.ts
│       ├── android/              generated
│       └── package.json
│
├── docs/                         design docs (this file + 2 prior)
├── deploy/
│   ├── docker-compose.yml        local dev: frontend + backend + postgres
│   ├── helm/                     k8s chart for production
│   └── terraform/                AWS/Azure/GCP reference deployments
│
├── .github/workflows/
│   ├── frontend.yml              shipped (Batch 8)
│   ├── backend.yml               Batch 15: lint + test + image
│   ├── desktop.yml               Batch 27: macOS/Windows/Linux matrix
│   ├── mobile.yml                Batch 29: Android AAB + sign
│   └── release.yml               Batch 32: tag → all artefacts + release notes
│
├── Makefile                      existing — `make install` works
└── compose.dev.yml               one-command local dev
```

## 4 · Tech-stack decisions (industry baseline · 2025)

| Layer | Choice | Why |
|---|---|---|
| Frontend framework | **React 18 + TS strict** (already shipped) | Largest talent pool, mature in every shell |
| Frontend bundler | **Vite 5** (already shipped) | Fast dev loop, simple Tauri/Capacitor handoff |
| Routing | **React Router 6** | Stable, deep-link friendly |
| State | **React state + tiny context** (today) → **React Query** for server cache | Keeps the prototype simple; React Query is the de-facto choice for REST/WS apps |
| Styling | Inline tokens + CSS vars (already shipped) | Tree-shakable, theme-swap friendly |
| Backend | **FastAPI 0.110+** on **Python 3.11** | Same runtime as agent-generator → zero deserialise-then-shell hop |
| Backend deps | **uv** (already used) for lockfile + install | Matches the Docker wizard's example Dockerfile |
| DB | **SQLite** default → **PostgreSQL 16** in prod via env switch | Zero-config local dev; postgres for HA |
| Migrations | **Alembic** | Standard for SQLAlchemy |
| Auth | **OAuth (GitHub/Google/Azure-AD)** via `authlib` + local admin fallback | Matches the existing AdminAccountMenu (single-admin assumption) |
| Streaming | **WebSocket** primary + **SSE** fallback | Works behind every corporate proxy |
| Secrets | Pluggable adapters: **HashiCorp Vault** · **AWS SM** · **Azure KV** · **IBM SM** · **GCP SM** · **Doppler** · **Kubernetes Secrets** · **1Password Connect** | Mirrors the Docker wizard's Env & Secrets table verbatim |
| Container build | **buildx** (BuildKit) shelled out from backend | Real builds, real logs, real layers |
| Signing | **cosign keyless** + **SLSA 3** + **SBOM (syft)** | Already promised in the Docker wizard's UI |
| Desktop shell | **Tauri 2** | Tiny binaries (~15 MB), native auto-update, real signing |
| Mobile shell | **Capacitor 6** | Same `dist/`, native plugins in TS, Play Store-ready |
| Observability | **OpenTelemetry** (traces + metrics) + **Sentry** (errors) + **JSON logs** | Vendor-neutral, every cloud accepts it |
| CI | **GitHub Actions** with reusable workflows + GHA cache | Already wired for frontend |

## 5 · Frontend / backend contract

Typed once, generated everywhere:

1. Backend declares Pydantic schemas (e.g. `Project`, `RunEvent`,
   `BuildEvent`, `Diagnostic`).
2. FastAPI emits an **OpenAPI 3.1** spec at `/openapi.json`.
3. CI runs `openapi-typescript` to emit `frontend/src/lib/api/schema.d.ts`.
4. The hand-written `frontend/src/lib/api/client.ts` wraps `fetch` + WS
   and re-exports the typed methods.

No drift, ever — type-mismatched PRs fail CI.

WebSocket messages use a single envelope:

```ts
type ServerMessage =
  | { type: 'run.event';    runId: string;   event: RunEvent }
  | { type: 'run.done';     runId: string;   ok: boolean; tokens: number }
  | { type: 'build.event';  buildId: string; line: BuildLogLine }
  | { type: 'build.stage';  buildId: string; stage: BuildStage; status: 'ok'|'run'|'err' }
  | { type: 'build.done';   buildId: string; digest: string; size: number };
```

## 6 · The compatibility & orchestration data layer

Verbatim from `docs/wizard-compatibility-design.md` +
`docs/wizard-orchestration-patterns-design.md`, materialised as:

- `frontend/src/lib/compatibility.ts` — `HYPERSCALERS`,
  `FRAMEWORKS_X`, `ORCHESTRATION_PATTERNS`, `MODELS`, `PATTERN_BY_FW`,
  `compatibilityFor(state) → Diagnostic[]`.
- `backend/app/services/compatibility.py` — same matrix, exposed at
  `GET /api/compatibility` so plug-in templates (Settings → Plug-in
  templates) can extend it at runtime without a frontend deploy.

## 7 · The Test (Chat) surface — first-class agent testing

Matches `desktop-chat.jsx` exactly:

- **Left rail (256 px)** — searchable agent list with status dots,
  recent runs grouping, "Load from file…" pinned at the bottom.
- **Center** — Claude-style role-labelled messages (28 px square
  avatar, no bubbles), tool calls rendered as **collapsible cards**
  inline with args + result, typewriter cursor on streaming.
- **Right inspector (320 px)** — loaded agent metadata, permission
  mode segmented (Safe / Dev / Ask), live token + cost + elapsed
  counters, recent tool calls list, quick actions
  (live run, trace JSON, share, export .md).
- **Composer (pinned)** — outlined input, attach / tools / model
  picker / send + Stop button when streaming, `⌘↵` hint.
- **Agent picker** — `⌘P` popover with searchable list and keyboard
  navigation.

Backend wiring:

```
POST /api/chat/sessions               → { sessionId, agentId }
WS   /api/chat/sessions/{id}/stream   → user message → assistant tokens + tool calls
POST /api/chat/sessions/{id}/stop     → cancel mid-stream
```

The assistant message wraps the existing `agent_generator` runtime —
each tool call becomes a `tool.invoke` event on the WS, so the chat UI
and the existing Run console share one event protocol.

## 8 · The Docker wizard — production registry publishing

5-step wizard verbatim from `desktop-docker.jsx`:

| Step | Surface | Backend endpoint |
|---|---|---|
| 1. Configure | image/tag/base/arch/ports/build-args + live Dockerfile preview + size estimate | `POST /api/docker/configs` |
| 2. Env & Secrets | dev/staging/prod profile, env-vars table, secrets table with **backend adapter per row** (Vault / AWS SM / Azure KV / IBM SM / Doppler / K8s / GCP SM / 1Password), policy toggles, pre-build scan | `GET /api/secrets/backends` + per-backend test endpoints |
| 3. Build (streaming) | BuildKit-style 6-stage progress, resource panel (CPU / memory / cache-hit / net), terminal stream, cancel | `WS /api/docker/{id}/build` |
| 4. Publish · choose registries | 6 registries (Docker Hub · GHCR · ICR · ECR · ACR · GAR) with auth state, tags to push, **cosign keyless + SBOM (syft) + SLSA-3 attest** panel | `POST /api/docker/{id}/publish` |
| 5. Published | success card per registry with copyable `docker pull …`, "Run anywhere" snippet, next actions, image metadata (digest, layers, size, signed, SBOM attached, SLSA level) | `GET /api/docker/{id}/published` |

### 8.1 Env & Secrets — the enterprise bit

The wizard's Env & Secrets step is the highest-risk surface. Design
guarantees enforced server-side:

| Policy | Server enforcement |
|---|---|
| Refuse to build with plaintext secrets | `pre_build_scan()` rejects any literal secret matching `^(AKIA|sk-|ghp_|xoxp-|hf_|…)` |
| Strip `.env` from build context | buildx `--build-context` excludes; the Dockerfile preview surfaces this with a `.dockerignore` augmentation |
| Mask secrets in build/run logs | log filter regex compiled per-backend; stream replaces with `***` |
| Rotate runtime tokens on container start | injected as a sidecar `init.sh` calling the backend with the issued JIT token |
| Audit secret reads | every backend adapter records `(secret_ref, requester, build_id, ts)` to `audit_log` |

BuildKit injects secrets via `--mount=type=secret,id=…` (build-time)
and the container runtime injects via env / file mount as the table's
Mode column specifies. Both paths are visible in the right rail's
"How it injects" terminal snippet.

## 9 · Updated Settings (7 tabs) + About modal

Matches `desktop-admin.jsx` exactly. Already covered in Batch 6; this
plan upgrades the tabs to the new content:

- **General** — Appearance · Locale · Workspace · Privacy.
- **Account** — identity hero, security, **API keys table** with
  rotate/revoke, danger zone.
- **Providers** — already shipped, now grouped Cloud LLM / Enterprise / Local.
- **Plug-in templates** — installed templates table; add-from-URL.
- **Defaults** — Generation defaults (framework / pattern / provider /
  model / agents / memory), Output (language / lint / Docker / tests),
  Safety (permission mode · shell-exec default).
- **Shortcuts** — three grouped tables (Global, Test, Pipeline) with
  mono key caps.
- **Data controls** — storage size, retention, export ZIP, cloud
  backup, clear data table.

About modal: hero · System KV grid · Components · Integrations grid ·
License & compliance pills · Acknowledgements · footer.

## 10 · Tauri & Capacitor wiring — the cross-platform contract

### 10.1 Platform abstraction (one file)

```ts
// frontend/src/lib/platform.ts
export type Platform = 'web' | 'tauri' | 'capacitor';

export const platform: Platform = (() => {
  if ('__TAURI_INTERNALS__' in window) return 'tauri';
  if ('Capacitor' in window) return 'capacitor';
  return 'web';
})();

export const fs = {
  saveFile: async (name: string, bytes: Uint8Array) => {
    if (platform === 'tauri')      return tauriFs.save(name, bytes);
    if (platform === 'capacitor')  return capFilesystem.writeFile(name, bytes);
    /* web */                       return browserDownload(name, bytes);
  },
  // openFile, watchFile, …
};

export const store = {
  // Secure store: macOS Keychain · Win Credential Manager · libsecret · Android KeyStore
  set: async (k: string, v: string) => …,
  get: async (k: string) => …,
};

export const deepLink = { onUrl: (cb) => … };
export const updater  = { check: () => …, install: () => … };
export const notify   = { send: (title, body) => … };
```

Every page imports from `@/lib/platform`; the shell-specific code lives
in three adapter files (`platform/web.ts`, `platform/tauri.ts`,
`platform/capacitor.ts`). 95% of components stay platform-blind.

### 10.2 Tauri 2 desktop shell

- `shells/desktop/src-tauri/tauri.conf.json` declares:
  - `windows`: 1440×900 default, min 960×600.
  - `bundle.targets`: `app · dmg · msi · nsis · deb · rpm · appimage`.
  - `updater`: signed JSON manifest at `https://releases.…/latest.json`.
  - `security.csp`: tight CSP allowing only our backend host + Google
    Fonts (already used).
- `tauri.conf.json → plugins`:
  - `tauri-plugin-store` for non-secret prefs.
  - `tauri-plugin-stronghold` (or OS keychain) for secrets.
  - `tauri-plugin-deep-link` for `agent-generator://…` URLs.
  - `tauri-plugin-updater` for signed delta updates.
  - `tauri-plugin-notification`.
  - `tauri-plugin-shell` (scoped) for the rare `pip` / `docker` shellout
    when the user opts to run the agent locally on desktop.
- `main.rs` (~50 lines): window setup + deep-link handler + tray menu.
- **Code signing**:
  - macOS: Apple Developer ID + notarisation via `notarytool` in CI.
  - Windows: Authenticode with an EV cert from DigiCert/Sectigo.
  - Linux: GPG-signed `.deb` / `.rpm`.
- **Auto-update**: signed JSON manifest at `https://releases.agent-generator.io/latest.json`,
  delta updates, fallback to full install on signature mismatch.

### 10.3 Capacitor 6 mobile shell

- `shells/mobile/capacitor.config.ts` points `webDir` at `../../frontend/dist`.
- Plugins:
  - `@capacitor/preferences` (non-secret).
  - `@capacitor-community/keep-awake` (during runs).
  - `@capacitor/filesystem` (download generated projects).
  - `@capacitor/share` (export `.zip` / share install command).
  - `@capacitor/app` (deep links + back button).
  - `@capacitor/network` (offline detection).
  - `@aparajita/capacitor-secure-storage` (Android KeyStore-backed).
- **Android signing**: Play Console upload key + app signing key
  managed by Google; the CI workflow stores the upload key encrypted
  in GitHub Secrets.
- **iOS** ships off the same `dist/` with `npx cap add ios` when the
  org has an Apple Developer Program seat — out of scope for the
  first release but the architecture supports it day-one.

## 11 · The batched implementation plan (Batches 9 → 32)

Each batch is independently shippable. Batches are ordered so any
single PR can land in main without breaking the rest.

### Phase A — Frontend parity with new design (Batches 9–14)

| # | Title | Deliverables | Effort |
|---|---|---|---|
| **9** | Compatibility data layer | `src/lib/compatibility.ts` + `src/lib/hyperscalers.ts` + `src/lib/orchestration.ts` + `src/lib/models.ts`. Pure data — no UI change | ½ day |
| **10** | Framework & Model v2 (Step 2 rebuild) | Facet rail · philosophy filter · 8 framework cards · Model row · Pattern row · Pattern card · "Why" block | 1 day |
| **11** | Review · Compatibility card | New card above the file-preview in Step 4 · diagnostic rows · Resolve action | ½ day |
| **12** | Test (Chat) surface | New `/test` route · agent rail · message thread with collapsible tool-call cards · streaming · agent ⌘P picker · right inspector | 1.5 days |
| **13** | Docker wizard · Steps 1–3 | Configure + Env/Secrets + Build (streaming) | 1.5 days |
| **14** | Docker wizard · Steps 4–5 | Publish (multi-registry · cosign · SBOM · SLSA) + Published | 1 day |

### Phase B — Backend (Batches 15–23)

| # | Title | Deliverables | Effort |
|---|---|---|---|
| **15** | Backend scaffold | FastAPI · uv · SQLite default · Pydantic Settings · Alembic baseline · Dockerfile · OpenAPI emission · CI | 1 day |
| **16** | Auth · admin + OAuth | GitHub/Google/Azure-AD OAuth via authlib + local admin fallback + signed cookie sessions + RBAC stub | 1 day |
| **17** | Wizard + Projects API | `/api/compatibility`, `/api/projects` CRUD wrapping the existing CLI's `agent_generator` package (no shell-out) | 1 day |
| **18** | Run API + WS streaming | `POST /api/projects/{id}/run` returns `runId`; `WS /api/runs/{id}` streams the event protocol; powers existing Run + new Chat | 1 day |
| **19** | Marketplace proxy | Server-side proxy to MatrixHub catalog, with cache + ETag · `POST /api/marketplace/install` triggers the existing CLI install path | ½ day |
| **20** | Docker build/publish | buildx shell-out · structured log parser → WS · publish with skopeo/oras · cosign keyless · syft SBOM · SLSA provenance | 2 days |
| **21** | Secrets adapters | One module per backend (Vault, AWS SM, Azure KV, IBM SM, GCP SM, Doppler, K8s, 1Password). Common interface + connection-test endpoint + audit log writer | 2 days |
| **22** | OllaBridge pairing | `POST /api/ollabridge/pair` proxies `/device/pair-simple`; tokens stored in the secure store layer; provider table in Settings → Providers reads paired state | ½ day |
| **23** | Telemetry & audit | OTel traces for every endpoint · JSON logs · Prometheus `/metrics` · audit-log table · Sentry sink behind the Telemetry toggle from Settings · GDPR-compliant retention | 1 day |

### Phase C — Platform abstraction (Batch 24)

| # | Title | Deliverables | Effort |
|---|---|---|---|
| **24** | `lib/platform.ts` + adapters | Runtime detect · fs / store / deepLink / updater / notify shims · web adapter (existing behaviour, no regression) · stubs for tauri & capacitor | 1 day |

### Phase D — Tauri desktop shell (Batches 25–27)

| # | Title | Deliverables | Effort |
|---|---|---|---|
| **25** | Tauri 2 scaffold | `shells/desktop/` · `tauri.conf.json` · 50-line `main.rs` · icon set generated from one SVG · `npm run tauri dev` produces a working window pointing at the local Vite dev server | 1 day |
| **26** | Native plugins | tauri-plugin-store, stronghold/keychain, deep-link (`agent-generator://`), updater (signed manifest), notifications, scoped shell · wire each into `platform/tauri.ts` | 1.5 days |
| **27** | Signed builds in CI | `.github/workflows/desktop.yml` matrix: macos-latest (Intel + arm64 + notarisation), windows-latest (Authenticode EV), ubuntu-latest (AppImage + deb + rpm + GPG sign) · attaches all to a draft release on tag | 2 days |

### Phase E — Capacitor Android (Batches 28–29)

| # | Title | Deliverables | Effort |
|---|---|---|---|
| **28** | Capacitor 6 scaffold | `shells/mobile/` · `capacitor.config.ts` · `npx cap add android` · icons + splash · `platform/capacitor.ts` plugin shims | 1 day |
| **29** | Signed Android in CI | `.github/workflows/mobile.yml` · uses Android SDK action · builds AAB · signs with upload-key from GH Secrets · uploads to Play Console internal track via `r0adkll/upload-google-play` | 1 day |

### Phase F — Production readiness (Batches 30–32)

| # | Title | Deliverables | Effort |
|---|---|---|---|
| **30** | E2E tests | Playwright on web + Tauri (`@tauri-apps/cli driver`) covering the 4 critical journeys (generate → run, marketplace install, docker build, chat session) · Maestro flows for Android | 2 days |
| **31** | Observability end-to-end | OTel collector in compose · Grafana dashboards (latency · run success rate · build time · token cost) · Sentry releases · structured logs landing in Loki | 1 day |
| **32** | Release pipeline | `release.yml` triggered on `v*` tag · runs all build matrices · generates release notes from conventional commits · uploads signed artefacts · cuts the Play Store internal track · auto-publishes the updater manifest | 1.5 days |

**Total new effort estimate: ~24 days of focused work**, ~5 of which is
sequential (15 → 16 → 17 → 18 → 30/31/32). Phases A, B, D, E can be
parallelised across two engineers.

## 12 · Risks, sequencing, and dependencies

- **Code-signing certificates are procurement-bound.** Apple Developer
  ID + Windows EV cert can take 1–4 weeks to issue. Start the legal
  paperwork in parallel with Batch 9, not at Batch 27.
- **Tauri 2 ↔ React 18 ↔ Vite 5** is a known-good triple as of 2025-Q3.
  Don't bump React 19 until after Batch 27.
- **buildx in CI** needs `docker/setup-buildx-action@v3` and rootless
  containerd; both already provided by `ubuntu-latest`. macOS runners
  for desktop builds can't run Docker — keep the Docker wizard backend
  on Linux only.
- **Secret-backend connectors** are the most-likely scope creep. Ship
  Vault + AWS SM + Azure KV + GitHub Secrets in Batch 21, defer the
  others to a `21b` follow-up if needed.
- **Mobile permissions** (filesystem, camera, biometric) need a
  privacy policy URL before Play Store accepts the listing. Coordinate
  with the OllaBridge / MatrixHub docs to publish at
  `agent-generator.io/privacy` before Batch 29.
- **Backwards compatibility.** The existing CLI keeps working — the
  backend is a *wrapper*, not a rewrite. Every code path the CLI uses
  today must remain green in CI.

## 13 · Definition of done

The whole solution is done when:

1. A user can `docker compose up` the backend + frontend, hit
   `http://localhost:5173`, generate an agent through the wizard, run
   it in the Test surface, and publish a signed Docker image to GHCR
   from the Docker wizard — all from one URL.
2. The same flow works on a signed `.dmg` / `.exe` / `.AppImage`
   downloaded from the GitHub Release page, opening to the same UI
   pointed at a chosen backend.
3. The same flow works on Android (Play Store internal track), with
   sessions persisted via Capacitor's secure storage.
4. CI for `frontend/`, `backend/`, `shells/desktop/`, `shells/mobile/`
   is green on every push; tagged commits cut signed artefacts to a
   GitHub Release in under 20 minutes.
5. The Test surface and Run console both consume the same WebSocket
   event protocol — adding a new event kind requires touching one
   schema file.
6. Hyperscaler / framework / pattern / model compatibility is enforced
   on both frontend (UX) and backend (validation), with the matrix
   declared in a single TypeScript-mirrored Python module.

## 14 · Out of scope (deferred)

- iOS shell (architecture supports it; needs Apple Developer Program
  enrolment).
- Plug-in templates writing custom compatibility rows into the matrix
  at runtime — design-only in this plan; implement once the v1 ships.
- Cost / token estimator chip on the Pattern card.
- Federated identity for org accounts beyond a single admin — the
  current AdminAccountMenu assumes one user.
- Streaming model output to the Pipeline editor live-preview.

## 15 · Open questions for confirmation

1. **Default secret backend**: Vault or AWS SM? (Affects which adapter
   we ship first in Batch 21.) — *Recommendation: Vault, the
   open-source default.*
2. **OAuth providers in Batch 16**: GitHub-only first, or all three
   day-one? — *Recommendation: GitHub-only, others behind a config
   flag.*
3. **Desktop auto-update host**: GitHub Releases (free, public) or a
   private CDN? — *Recommendation: GitHub Releases for v1, swap later
   via a Tauri config change.*
4. **Android distribution**: Play Store + direct APK side-load, or
   Play Store only? — *Recommendation: both. APK side-load matters
   for enterprises that pre-load their fleet.*
5. **Backend deployment target**: Plain Docker, Kubernetes, or both?
   — *Recommendation: ship both the `Dockerfile` and a Helm chart
   under `deploy/helm/`. Same image, two deployment shapes.*

If you confirm 1–5 (or override any of the recommendations), I can
cut Batch 9 immediately and start the long pole on code-signing
procurement in parallel.
