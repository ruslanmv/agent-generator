# ────────────────────────────────────────────────────────────────
#  src/agent_generator/wsgi.py
# ────────────────────────────────────────────────────────────────
"""
WSGI/ASGI entry‑point ⚙️

Used by Gunicorn in both Docker and production setups:

    gunicorn agent_generator.wsgi:create_app \
        -k uvicorn.workers.UvicornWorker \
        -b 0.0.0.0:8000 --workers 4 --timeout 120

`create_app()` is imported from the `agent_generator.web` package,
allowing the core CLI package to remain installable without web extras.
"""

from __future__ import annotations

from typing import Any

try:
    # Optional dependency: only present when the “web” extras are installed.
    from agent_generator.web import create_app
except ModuleNotFoundError as exc:  # pragma: no cover
    raise RuntimeError(
        "Flask extras are not installed. "
        "Install with: pip install 'agent-generator[web]'"
    ) from exc

# Gunicorn expects a module‑level callable named `app` by default.
app: Any = create_app()
