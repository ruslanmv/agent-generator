# Observability

Drop-in OpenTelemetry + Sentry stack the backend already emits to.
Boot it with `docker compose up` from this directory and the backend
will start filling the dashboards as soon as it points
`AG_OTLP_ENDPOINT` at `http://localhost:4317`.

## Stack

| Component        | Port  | Why                                                                          |
|------------------|-------|------------------------------------------------------------------------------|
| OTel Collector   | 4317  | Receives OTLP/gRPC from `app.telemetry.bootstrap`; fans out to Prometheus + Loki + Tempo |
| Prometheus       | 9090  | Scrapes metrics from the collector                                           |
| Loki             | 3100  | Stores the structured logs piped from `structlog` via the collector          |
| Tempo            | 3200  | Stores traces                                                                 |
| Grafana          | 3000  | Dashboards (`dashboards/agent-generator.json`)                               |

Datasources are provisioned from `grafana/provisioning/datasources.yaml`
and the dashboard is auto-imported from `dashboards/agent-generator.json`
(see `grafana/provisioning/dashboards.yaml`).

## Use

```sh
docker compose up -d
# Backend
export AG_OTLP_ENDPOINT=http://localhost:4317
export AG_SENTRY_DSN=...  # optional
uvicorn app.main:app --reload --port 8000
```

Open Grafana at <http://localhost:3000> (admin / admin) → Dashboards →
*Agent Generator*.

## Sentry

`AG_SENTRY_DSN` enables the SDK; `AG_ENV` populates the environment
filter; the backend's `__version__` populates the release. Hook into
the GitHub Release pipeline (Batch 32) with `sentry-cli releases new`
+ `releases set-commits` so source maps + commit metadata are
attached automatically.
