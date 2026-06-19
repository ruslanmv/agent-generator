# Frontend Realization Plan — from HF demo to a real application

The Agent Generator [Hugging Face Space](https://huggingface.co/spaces/ruslanmv/agent-generator)
ships the React/Vite frontend on the **`hf`** build channel, which sets `IS_DEMO = true`. The
**backend is real and complete** (`backend/app/api/`), but most pages read **static `*-data.ts`
fixtures** instead of calling it. This plan removes every fake and wires the UI to the real API —
including **OllaBridge (cloud or a paired local node)** as the model provider — one governed batch at
a time.

## 1. Placeholder inventory → real endpoint mapping

| Fake module | Powers | Real backend endpoint(s) | Batch |
|---|---|---|---|
| `lib/wizard-data.ts` | Generate wizard: frameworks, models, tools, agents, spec | `GET /api/compatibility/catalogue` · `POST /api/compatibility/diagnose` · `POST /api/projects` | 2, 3 |
| `lib/marketplace-data.ts` | Marketplace Browse / Detail | `GET /api/marketplace/agents` · `/agents/{id}` · `POST /api/marketplace/publish` | 5 |
| `lib/run-data.ts` | Run console trace / agents / stream | `GET /api/runs/{id}` · WS `/api/runs/{id}/events` (`useRunStream.ts`) | 4 |
| `lib/settings-data.ts` | Providers (incl. OllaBridge), defaults, account | `GET /api/secrets` · `GET /api/auth/me` · `POST /api/ollabridge/pair` · `GET /api/ollabridge/status/{project_id}` | 7 |
| `lib/export-data.ts` | Export grid + publish | `POST /api/builds/docker` + WS `/ws/builds/{id}` · publish-hf api · marketplace publish | 6 |
| `lib/pipeline-data.ts` | Pipeline editor graph / library | ⚠️ **no backend route yet** — add one or derive from the project spec | 8 |
| `components/demo/{DemoBanner,DemoBadge}`, `IS_DEMO` | "DEMO" affordance | real capability check (backend reachable?) | 9 |
| `pages/Placeholder.tsx` | stub routes | the real page for each route | 9 |

**Already real (keep & build on):** `pages/projects/*`, `pages/History.tsx`, `pages/docker/*`,
`pages/test/*`, `pages/publish-hf/*`, `pages/wizard/api.ts` (partial). The real client `lib/api.ts`
(`api.get/post/patch/del`, JWT via `getAccessToken`, `wsUrl`) is the foundation.

**Backend routes available today:** `auth` (GitHub OAuth, `/me`, `/refresh`, `/logout`),
`compatibility` (`/catalogue`, `/diagnose`), `marketplace` (`/agents`, `/agents/{id}`, `/publish`),
`ollabridge` (`/pair`, `/status/{project_id}`), `projects` (CRUD), `runs` (`/{id}`, `/{id}/events`),
`secrets` (CRUD), `builds` (`POST /api/builds/docker` + WS `/ws/builds/{id}`), `audit`, `health`.

## 2. The batches

> **Rules (all batches):** keep `lib/api.ts` as the single client; every async call gets
> loading / error / empty states; no page may import a `*-data.ts` fixture once its batch lands; the
> deterministic offline fallback is allowed only on the public HF demo when the backend is
> unreachable. Each batch ends typecheck-clean (`npm run typecheck`) and builds.

### Batch 0 — API client foundation
- **Files:** `lib/api.ts`, `lib/api-types.ts` (new), `vite.config.ts`.
- **Do:** add a typed method per backend route; confirm `VITE_API_URL` / the HF same-origin `/api`
  proxy; standardize error envelope + a small `useApi` hook for loading/error.
- **Accept:** every backend route is callable with types; JWT auto-attached; a smoke call to
  `/api/health/readyz` succeeds.

### Batch 1 — Auth & session (real)
- **Files:** `components/admin/AdminAccountMenu.tsx`, `pages/settings/Account.tsx`, `lib/auth*` (new).
- **Do:** GitHub OAuth (`/auth/github/login` → `/callback`), persist + refresh the JWT, hydrate from
  `/auth/me`, logout.
- **Accept:** sign in with GitHub works end to end; the account menu shows the real user; protected
  calls carry the bearer token; logout clears it.

### Batch 2 — Wizard catalogues (frameworks / models / tools)
- **Files:** `pages/wizard/StepFramework.tsx`, `StepTools.tsx`, `StepDescribe.tsx`, `wizard/api.ts`;
  retire `lib/wizard-data.ts` static lists.
- **Do:** load the catalogue from `/compatibility/catalogue`; validate combos via `/compatibility/diagnose`.
- **Accept:** real frameworks/models/tools render; incompatible picks are flagged by the backend;
  no static catalogue remains.

### Batch 3 — Generate → create a real project
- **Files:** `pages/wizard/StepReview.tsx`, `review/ReviewGenerate.tsx`, `pages/projects/ProjectsHub.tsx`.
- **Do:** the wizard submit calls `POST /api/projects` with the assembled spec; `ProjectsHub` lists
  from `GET /api/projects`; open → `GET /api/projects/{id}`.
- **Accept:** finishing the wizard creates a **persisted** project and it appears in the hub for real.

### Batch 4 — Run console + live stream (real)
- **Files:** `pages/run/Console.tsx`, `TraceTree.tsx`, `AgentSidebar.tsx`, `lib/useRunStream.ts`;
  retire `lib/run-data.ts`.
- **Do:** load `GET /api/runs/{id}`; subscribe to the WS `/api/runs/{id}/events`; render real agent
  activity / trace / console.
- **Accept:** the Run page streams live events from the backend; no static run fixture.

### Batch 5 — Marketplace (Matrix Hub)
- **Files:** `pages/marketplace/Browse.tsx`, `Detail.tsx`, `TypeBadge.tsx`; retire `lib/marketplace-data.ts`.
- **Do:** `GET /marketplace/agents` + `/agents/{id}`; publish via `POST /marketplace/publish`.
- **Accept:** Browse/Detail render the real catalogue; publishing posts to the backend.

### Batch 6 — Export / Publish (real)
- **Files:** `pages/export/*`, `pages/docker/Build.tsx` (already partly real), `pages/publish-hf/*`;
  retire `lib/export-data.ts`.
- **Do:** Docker build via `POST /api/builds/docker` + WS `/ws/builds/{id}`; HF publish via the
  publish-hf api; MatrixHub publish via marketplace.
- **Accept:** a Docker build streams real logs; HF publish completes; the export grid reflects real targets.

### Batch 7 — Settings, providers & **OllaBridge**
- **Files:** `pages/settings/Providers.tsx`, `Defaults.tsx`, `Account.tsx`, `DataControls.tsx`;
  `pages/run/*` + `wizard/*` provider selection; retire `lib/settings-data.ts`.
- **Do:** secrets via `/api/secrets` (CRUD); account via `/auth/me`. **Wire OllaBridge:** pair a node
  or connect **OllaBridge Cloud** via `POST /api/ollabridge/pair`, show `GET /ollabridge/status/{id}`,
  and make OllaBridge (cloud **or** local) a selectable model provider used by generation and runs.
- **Accept:** secrets persist via the backend; OllaBridge pairs and becomes the active provider; the
  wizard/run actually call a model through it.

### Batch 8 — Pipeline editor
- **Files:** `pages/pipeline/*`; retire `lib/pipeline-data.ts`. **Backend:** add `GET/PUT
  /api/projects/{id}/pipeline` (or derive from the project spec).
- **Accept:** the pipeline graph reflects the real project; the static graph is gone.

### Batch 9 — De-demo
- **Files:** `lib/build-channel.ts`, `components/demo/*`, `pages/Placeholder.tsx`, the router.
- **Do:** turn `IS_DEMO` into a runtime **capability check** (is the backend reachable?) instead of a
  hard `hf` flag; remove the unconditional `DemoBanner` and every `Placeholder` route.
- **Accept:** on HF with the backend reachable there is **no "DEMO" banner**; the banner appears only
  when the backend is genuinely unavailable; every route is a real page.

### Batch 10 — E2E + hardening
- **Files:** `e2e/*`, loading/error/empty states across pages.
- **Accept:** the `e2e/` suite covers sign-in → wizard → generate → run → export against a live
  backend; **no page imports any `*-data.ts`**; typecheck + build clean.

## 3. Critical path

```
0 → 1 → 2 → 3 → 4   (+ 7 for OllaBridge)   ← this is "a real, usable app"
                5 · 6 · 8                   ← broaden the surface
                     9 · 10                 ← finish & de-demo
```

Start with **Batch 0** (the typed client), then **1–4 + 7**: that turns the demo into a real
application where a signed-in user designs an agent in the wizard, generates a persisted project,
watches it run live, and points it at **OllaBridge (cloud or local)** as the model — with GitPilot as
the AI coder behind the governed build.
