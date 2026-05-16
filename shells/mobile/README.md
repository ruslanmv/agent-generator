# Agent Generator · mobile shell (Capacitor 6)

Wraps `frontend/dist` to produce signed Android binaries for the Play
Store internal track. iOS-ready — `npx cap add ios` on a Mac with an
Apple Developer Program seat is the only extra step.

| Target | Output |
|--------|--------|
| Android | `.aab` (Play Store) · `.apk` (sideload / enterprise fleet) |
| iOS | `.ipa` (when iOS shell is added — Batch 29 follow-up) |

## Prerequisites

- **Node.js** 20+
- **Java** 17 (JDK)
- **Android Studio** (or just **Android SDK + cmdline-tools**) — SDK
  Platform 34, Build-Tools 34.0.0
- An ANDROID_HOME pointing at the SDK install

## First-time setup

The native `android/` project isn't committed to git as a generated
directory — Capacitor regenerates it deterministically from
`capacitor.config.ts`. Bootstrap once:

```sh
cd shells/mobile
npm install
npm run add:android
```

That writes a tree under `android/` with the package id, app icons,
and Gradle wrapper. From then on every developer (and CI) gets the
same project.

## Develop

```sh
# Plug in an Android device with USB debugging enabled, or boot an
# AVD emulator first.
CAP_SERVER_URL=http://192.168.1.42:5173 npm run run:android
```

`CAP_SERVER_URL` points the in-app webview at the Vite dev server on
your LAN — code changes hot-reload onto the device. Drop the env var
to bundle assets into the APK.

## Build

```sh
# Debug APK (unsigned) — fine for QA fleets, won't install on a stock
# device without enabling "Install unknown apps".
npm run build:android:debug

# Production AAB (signed if the keystore is wired) for the Play Store.
npm run build:android
```

Signed CI builds + Play Store internal-track upload land in Batch 29.

## What's wired today (Batch 28)

- `capacitor.config.ts` — `appId: io.agent_generator.app`,
  `webDir: ../../frontend/dist`, plugin defaults for SplashScreen,
  StatusBar, Keyboard, LocalNotifications.
- Plugin set matching `frontend/src/lib/platform/capacitor.ts`
  (Preferences · SecureStorage · Filesystem · App · LocalNotifications
  · Browser · Network · Share · SplashScreen · StatusBar · Keyboard).
- npm scripts: `sync`, `add:android`, `open:android`, `run:android`,
  `build:android`, `build:android:debug`, `doctor`.

## What's still coming

- **Batch 29** — `.github/workflows/mobile.yml` that builds + signs
  the AAB and uploads to the Play Store internal track via
  `r0adkll/upload-google-play`.
- **iOS shell** — `npx cap add ios` once an Apple Developer Program
  seat exists.
- A privacy-policy URL at `agent-generator.io/privacy` (required by
  Play Store review before the listing goes public).

## Why Capacitor and not React Native?

See `docs/complete-solution-plan.md` §4 — short version: Capacitor
consumes the *same Vite `dist/`* we already ship to desktop and web;
no second component tree to maintain, no React Native primitives to
rewrite.
