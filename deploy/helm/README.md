# Helm chart · agent-generator

Single chart that ships both surfaces of the Agent Generator
production deployment:

- **backend** (`ghcr.io/.../agent-generator-backend`) — FastAPI,
  liveness/readiness probes, HPA, non-root pod security, env from a
  Kubernetes `Secret` you wire up out-of-band.
- **web** (`ghcr.io/.../agent-generator-web`) — nginx serving the
  Vite bundle, fronted by the same ingress so the SPA reaches its
  backend at `/api` and `/ws` with no CORS dance.

## Install

```sh
helm install agent-generator oci://ghcr.io/ruslanmv/charts/agent-generator \
  --version 0.1.0 \
  --namespace ag --create-namespace \
  --set ingress.hosts[0].host=agent-generator.example.com \
  --set telemetry.otlpEndpoint=otel-collector.observability.svc:4317
```

## Upgrade

The `release-app.yml` workflow bumps `appVersion`, `version`, and
`backend.image.tag` / `web.image.tag` on every `v*.*.*` tag, then
pushes the packaged chart to `oci://ghcr.io/.../charts`. You can
`helm upgrade ... --version <new>` straight away.

## Secret wiring

The backend reads its sensitive env vars from the Kubernetes Secret
named in `backend.envFromSecret` (defaults to
`agent-generator-backend`). Minimum contents:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: agent-generator-backend
stringData:
  AG_JWT_SECRET:            <64-byte random>
  AG_GITHUB_CLIENT_ID:      <from GitHub OAuth app>
  AG_GITHUB_CLIENT_SECRET:  <from GitHub OAuth app>
  AG_VAULT_ADDR:            https://vault.example.com:8200
  AG_VAULT_TOKEN:           <kubernetes-auth or static>
  AG_DATABASE_URL:          postgresql+asyncpg://...
```

In clusters with [External Secrets Operator](https://external-secrets.io)
or Vault Agent Injector, point the chart at the secret it
materialises instead.
