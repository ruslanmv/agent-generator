"""Matrix engine HTTP facade (Batch 9).

FastAPI is an optional dependency (the ``web`` extra). Importing this package without it
raises a clear error; importing ``agent_generator`` itself never requires FastAPI.
"""

from __future__ import annotations


def create_app(engine=None):
    """Create the Matrix engine FastAPI app. Requires the ``web`` extra (FastAPI)."""
    try:
        from agent_generator.http.app import create_app as _create_app
    except ImportError as exc:  # pragma: no cover - only when FastAPI is absent
        raise ImportError(
            "The Matrix engine HTTP facade requires FastAPI. Install with: "
            "pip install 'agent-generator[web]'"
        ) from exc
    return _create_app(engine)


__all__ = ["create_app"]
