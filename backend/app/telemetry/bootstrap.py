"""Wire OpenTelemetry + Sentry at startup.

OTel: traces only for now. Metrics + log correlation land in Batch 31
alongside the Grafana / OpenSearch dashboards. The OTLP exporter
pushes to ``AG_OTLP_ENDPOINT`` (gRPC); without it, the SDK is left in
the default no-op state.

Sentry: error tracking only. ``AG_SENTRY_DSN`` enables it; otherwise
the SDK is not imported.

Both integrations are guarded so a missing optional dependency doesn't
crash the service — telemetry is observability, not a feature, and a
broken telemetry stack must never take the API down.
"""

from __future__ import annotations

import importlib
from typing import Any

import structlog
from fastapi import FastAPI

from app import __version__
from app.settings import Settings

log = structlog.get_logger("telemetry")


def _try_setup_otel(app: FastAPI, settings: Settings) -> None:
    if settings.otlp_endpoint is None:
        return
    try:
        Resource = importlib.import_module(
            "opentelemetry.sdk.resources"
        ).Resource
        trace_sdk = importlib.import_module("opentelemetry.sdk.trace")
        export_mod = importlib.import_module(
            "opentelemetry.sdk.trace.export"
        )
        otlp_exp = importlib.import_module(
            "opentelemetry.exporter.otlp.proto.grpc.trace_exporter"
        )
        instr = importlib.import_module(
            "opentelemetry.instrumentation.fastapi"
        )
        trace_api = importlib.import_module("opentelemetry.trace")
    except ImportError as exc:
        log.warning("telemetry.otel_missing_deps", error=str(exc))
        return

    resource = Resource.create(
        {
            "service.name": settings.service_name,
            "service.version": __version__,
            "deployment.environment": settings.env,
        }
    )
    provider = trace_sdk.TracerProvider(resource=resource)
    exporter = otlp_exp.OTLPSpanExporter(endpoint=str(settings.otlp_endpoint))
    provider.add_span_processor(export_mod.BatchSpanProcessor(exporter))
    trace_api.set_tracer_provider(provider)
    instr.FastAPIInstrumentor.instrument_app(app)
    log.info("telemetry.otel_enabled", endpoint=str(settings.otlp_endpoint))


def _try_setup_sentry(settings: Settings) -> None:
    if settings.sentry_dsn is None:
        return
    try:
        sentry_sdk: Any = importlib.import_module("sentry_sdk")
    except ImportError:
        log.warning("telemetry.sentry_missing_deps")
        return
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.env,
        release=f"{settings.service_name}@{__version__}",
        traces_sample_rate=0.1 if settings.env == "prod" else 1.0,
        send_default_pii=False,
    )
    log.info("telemetry.sentry_enabled")


def setup_telemetry(app: FastAPI, settings: Settings) -> None:
    _try_setup_otel(app, settings)
    _try_setup_sentry(settings)
