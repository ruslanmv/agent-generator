# Mobile E2E (Maestro)

Smoke flows that exercise the Android shell against an emulator or a
physical device. Maestro is YAML-driven, runs against the same APK
the `mobile.yml` workflow produces, and prints a deterministic
transcript per flow so flakes are obvious.

## Run locally

```sh
# Install Maestro CLI (one-time)
curl -Ls "https://get.maestro.mobile.dev" | bash

# Build the debug APK
( cd ../../shells/mobile && npm install && npx cap sync \
  && cd android && ./gradlew assembleDebug )

# Install on the connected device / emulator
adb install -r ../../shells/mobile/android/app/build/outputs/apk/debug/app-debug.apk

# Run all flows
maestro test flows/
```

## Run in CI

The `mobile-e2e` job in `.github/workflows/mobile.yml` (Batch 30
follow-up) boots an `android-x86_64` emulator on `reactivecircus/
android-emulator-runner`, installs the same debug APK, and pipes the
Maestro output into the workflow summary.

## Flows

| Flow                  | What it asserts                                      |
|-----------------------|------------------------------------------------------|
| `wizard.yaml`         | App launches, Generate tab opens, prompt accepted   |
| `marketplace.yaml`    | Marketplace tab renders the catalogue list          |
| `deep-link.yaml`      | Opening `agent-generator://generate?new=1` lands on the wizard |
