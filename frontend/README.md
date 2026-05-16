# Agent Generator — Frontend

Web UI for [agent-generator](https://github.com/ruslanmv/agent-generator). Describe an
agent in plain English, the wizard picks a framework, suggests tools, generates a
runnable Python project, and lets you publish it to Matrix Hub or hand it off to a
runtime such as HomePilot.

## Stack

- **Vite 5** + **React 18** + **TypeScript 5** (strict)
- **React Router 6** with a 768 px desktop/mobile split
- IBM Plex Sans / Mono / Serif via Google Fonts
- Single-source design tokens in `src/styles/tokens.ts` mirrored by CSS variables in
  `src/styles/global.css`
- No CSS-in-JS runtime — components render through inline `style` props or the
  shared CSS variables, so the bundle stays small and tree-shakable

The aesthetic is intentionally enterprise-light — sharp corners (0–2 px), tight
grid, neutral palette with a single deep accent. The accent is swappable from
**Settings → General → Accent** and persisted to `localStorage`.

## Project layout

```
frontend/
├── public/                 static assets served as-is
├── src/
│   ├── components/
│   │   ├── admin/          AdminAccountMenu, SettingsModal, AboutModal
│   │   ├── icons/          inline SVG icons + brand marks
│   │   └── primitives/     Button, Pill, Input, Stepper, Nav, Toggle
│   ├── layouts/
│   │   ├── DesktopShell    rail + topbar that wraps every desktop page
│   │   └── MobileShell     bottom-tab shell for narrow viewports
│   ├── lib/                wizard / run / pipeline / marketplace /
│   │                       export / settings catalogues, useMediaQuery,
│   │                       useAccent
│   ├── pages/              one folder per surface (generate, run, pipeline,
│   │                       marketplace, export, settings, mobile)
│   ├── styles/             tokens.ts + global.css
│   ├── App.tsx             routes (desktop + mobile)
│   └── main.tsx            entry; bootstraps the persisted accent
├── Dockerfile              multi-stage Node-build → nginx-serve
├── nginx.conf              SPA fallback + cache headers
├── index.html
├── package.json
├── tsconfig*.json
└── vite.config.ts
```

## Implementation roadmap (delivered)

| Batch | Scope |
|-------|-------|
| 1 | Foundation — tokens, primitives, `DesktopShell`, routing, Generate hero placeholder |
| 2 | Generate wizard — Describe → Framework → Tools → Review (file tree + permissions) |
| 3 | Run console + drag-and-drop pipeline editor |
| 4 | Marketplace (Matrix Hub) — browse, detail, install plan |
| 5 | Export & Publish + MatrixHub publish + HomePilot runtime adapter preview |
| 6 | AdminAccountMenu, Settings modal, About modal, OllaBridge provider |
| 7 | Mobile responsive flows (6-step generator, marketplace, export) |
| 8 | Theming, Dockerfile + nginx, CI workflow, deploy docs |

## Develop

```sh
cd frontend
npm install
npm run dev          # http://localhost:5173
npm run typecheck
npm run lint
npm run build        # outputs dist/
npm run preview      # serves dist/ on http://localhost:4173
```

## Theming

Five curated accent swatches ship out of the box (cobalt, teal, magenta, amber,
graphite). The active one is held in `localStorage` under `ag.accent` and applied
to both the CSS variables (`--ag-accent`, `--ag-accent-dim`, `--ag-accent-hi`)
and the `tokens` object exported from `src/styles/tokens.ts`, so both the
inline-style consumers and CSS-driven components stay in sync without a
re-render storm.

To swap the accent in code:

```ts
import { useAccent } from '@/lib/accent';
const { accent, setAccent } = useAccent();
setAccent('teal');
```

To add a new swatch, extend `ACCENTS` in `src/styles/tokens.ts` — the picker on
Settings → General reads from that array directly.

## Deploy

### Docker (recommended)

```sh
cd frontend
docker build -t agent-generator-frontend .
docker run --rm -p 8080:80 agent-generator-frontend
# → http://localhost:8080
```

The image is two stages: `node:20-alpine` for the build, then `nginx:1.27-alpine`
for serving. The included `nginx.conf` adds the SPA fallback (deep links such
as `/marketplace/agent:pdf-summarizer@1.4.2` resolve to `index.html`), long-cache
headers for hashed `/assets/*`, and `no-store` on `index.html` so deploys roll
out immediately.

### Static hosting (Pages, Netlify, Vercel, S3, Cloudflare Pages)

```sh
cd frontend
npm run build
# upload dist/ to your host of choice — make sure the host rewrites unknown
# paths to /index.html so the SPA router works.
```

## CI

`.github/workflows/frontend.yml` runs on every push/PR that touches `frontend/`:

1. `npm ci`
2. `npm run typecheck`
3. `npm run lint` (warn-only until lint is hardened)
4. `npm run build`
5. Uploads `frontend/dist` as a build artifact
6. On `push`, builds the Docker image too (cached via GHA cache)

## Contributing

Match the existing tokens before adding new colours — if you need a value that
isn't there yet, extend `tokens.ts` and the CSS variables together. Components
should accept primitive props (no styled-components, no CSS-in-JS runtime), so
the prototype stays light and tree-shakable.

When a feature isn't shipped yet, mark it with the existing `StagePillBadge`
(`core` / `beta` / `coming-soon` / `new` / `plugin` / `verified` / `recommended`)
so the user always sees an honest scope.
