# Release process

Cutting a release takes one tag push. Everything else is automation.

## The short version

```bash
# 1. Bump versions (see "Version locations" below).
# 2. Commit & push to master.
# 3. Tag and push the tag:
git tag v0.2.1
git push origin v0.2.1
```

Tag `v*.*.*` and `.github/workflows/release-app.yml` takes over:

1. Drafts a GitHub Release with auto-generated notes.
2. Builds the backend image (cosign keyless · SBOM · SLSA-3 provenance).
3. Builds desktop installers (macOS / Windows / Linux) — signed when
   secrets are present, unsigned fallback otherwise.
4. Builds the Android AAB and uploads to the Play Store internal
   track if the keystore + service-account secrets are set.
5. Packages and pushes the Helm chart to `oci://ghcr.io/<owner>/charts`.
6. Stamps Sentry with the release id.
7. Promotes the draft release to public once every dependency goes
   green.

## Doing it by hand (when you have to)

```bash
ruff check src/
pytest tests/ -v
python -m build
pip install dist/*.whl       # smoke-test the wheel locally
git tag v0.2.1
twine upload dist/*
```

## Version locations

Bump all four. They should agree.

- `pyproject.toml` — package version
- `src/agent_generator/__init__.py` — runtime `__version__`
- `src/agent_generator/cli.py` — version printed by `--version`
- `src/agent_generator/application/build_service.py` —
  `generator_version` stamped into every manifest

## Where signing material lives

In repo Actions secrets. Missing secrets degrade gracefully to
unsigned artefacts so PR CI keeps working for forks.

| Secret | Used by |
|---|---|
| `APPLE_CERTIFICATE`, `APPLE_ID`, `APPLE_PASSWORD`, `APPLE_TEAM_ID` | macOS notarisation |
| `WINDOWS_CERTIFICATE`, `WINDOWS_CERTIFICATE_PASSWORD` | Authenticode signing |
| `GPG_PRIVATE_KEY`, `GPG_PASSPHRASE` | `.deb` / `.rpm` / `.AppImage` |
| `TAURI_SIGNING_PRIVATE_KEY`, `TAURI_SIGNING_PRIVATE_KEY_PASSWORD` | Tauri auto-updater |
| `ANDROID_KEYSTORE_BASE64`, `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS`, `ANDROID_KEY_PASSWORD` | Android AAB |
| `PLAY_SERVICE_ACCOUNT_JSON` | Play Store internal track |

---

**Next:** [Platform overview](platform.md)
