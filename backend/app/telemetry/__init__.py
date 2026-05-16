"""Telemetry: OpenTelemetry traces + metrics, Sentry errors, audit log.

OTel and Sentry are wired in ``setup_telemetry()`` from the app factory.
Both are opt-in: a missing endpoint / DSN disables the integration so
local dev stays quiet.
"""

from app.telemetry.bootstrap import setup_telemetry

__all__ = ["setup_telemetry"]
