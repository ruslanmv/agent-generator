# Agent Generator · desktop shell (Tauri 2)

Wraps `frontend/dist` to produce native binaries for macOS, Windows, and
Linux. Same React app as the web build — no second codebase, no
component-level branching beyond the `lib/platform` adapter.

| Target | Output |
|--------|--------|
| macOS  | `.app` · `.dmg` (Intel + arm64) |
| Windows | `.msi` (WiX) · `.exe` (NSIS) |
| Linux  | `.AppImage` · `.deb` · `.rpm` |

## Prerequisites

- **Rust** 1.77+ (`rustup default stable`)
- **Node.js** 20+
- Per-OS toolchain:
  - macOS: Xcode Command Line Tools
  - Windows: VS Build Tools 2022 (with C++ workload), WebView2 runtime
  - Linux: `libwebkit2gtk-4.1-dev libgtk-3-dev libayatana-appindicator3-dev librsvg2-dev`

## Develop

```sh
cd shells/desktop
npm install
npm run dev        # boots the Vite dev server + launches a Tauri window
```

The dev window opens at the Vite dev URL (`http://localhost:5173`); hot
module reload works as it does in a browser tab.

## Build

```sh
npm run build         # release artefacts in src-tauri/target/release/bundle/
npm run build:debug   # debug build, faster compile, no signing
```

Production signing happens in CI (Batch 27) — `desktop.yml` matrix
across `macos-latest` (notarised via `notarytool`), `windows-latest`
(Authenticode EV), `ubuntu-latest` (GPG-signed `.deb`/`.rpm`).

## Icons

Drop a 1024×1024 PNG at `src-tauri/icons/source.png` and run:

```sh
npm run icons
```

Tauri's CLI generates every platform-specific variant
(`32x32.png` · `128x128.png` · `128x128@2x.png` · `icon.icns` · `icon.ico`).
We only commit `source.png` — the variants are build artefacts.

## What's wired today (Batch 25)

- Single-instance enforcement (`agent-generator://` deep links wake the
  existing window instead of spawning a duplicate).
- All Tauri plugins the frontend's `platform/tauri.ts` adapter expects:
  `store`, `stronghold`, `dialog`, `fs`, `shell`, `opener`, `os`,
  `notification`, `deep-link`. (`updater` is gated behind a Cargo
  feature so dev builds don't need a signing key.)
- A `version_info` IPC command + `ping` liveness probe.
- Tight CSP allowing the local backend (`localhost:8000`) and the two
  known external endpoints (Matrix Hub catalog + OllaBridge cloud).
- Capability file pinning the plugin permissions to the `main` window.
- Hardened-runtime entitlements ready for macOS notarisation.

## What's still coming

- **Batch 26** — concrete plugin glue (tray menu, menu bar, deep-link
  router hooked into React Router).
- **Batch 27** — signed multi-platform CI matrix + auto-update JSON
  manifest publishing.

## Why Tauri 2 and not Electron?

See `docs/complete-solution-plan.md` §4 — short version: ~15 MB binaries
vs Electron's 150 MB+, native code-signing/notarisation/updater built
in, no bundled Chromium.
