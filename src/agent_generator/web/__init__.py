# ────────────────────────────────────────────────────────────────
#  src/agent_generator/web/__init__.py
# ────────────────────────────────────────────────────────────────
"""
Flask application factory.
"""

from __future__ import annotations

from flask import Flask

from agent_generator.web.routes.api import api_bp
from agent_generator.web.routes.main import main_bp


def create_app() -> Flask:  # noqa: D401
    """Return a configured Flask app."""
    app = Flask(__name__)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    # Basic healthcheck
    @app.get("/health")
    def _health():
        return {"status": "ok"}

    return app
