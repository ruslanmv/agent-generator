# ────────────────────────────────────────────────────────────────
#  src/agent_generator/wsgi.py
# ────────────────────────────────────────────────────────────────
"""
ASGI entry-point for production deployments.

Used by uvicorn directly or via Gunicorn with UvicornWorker:

    uvicorn agent_generator.wsgi:app --host 0.0.0.0 --port 8000

    gunicorn agent_generator.wsgi:app \\
        -k uvicorn.workers.UvicornWorker \\
        -b 0.0.0.0:8000 --workers 4 --timeout 120
"""

from __future__ import annotations

from typing import Any

try:
    from agent_generator.web import create_app
except ModuleNotFoundError as exc:  # pragma: no cover
    raise RuntimeError(
        "FastAPI extras are not installed. " "Install with: pip install 'agent-generator[web]'"
    ) from exc

app: Any = create_app()
