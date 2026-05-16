"""Runtime configuration via pydantic-settings.

All settings come from environment variables (12-factor). A `.env` file
in the working directory is loaded automatically in development.

Production deployments override via real env vars (Helm values map into
container env, Tauri's sidecar passes them via stdin/argv, etc.).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Top-level service settings.

    Grouped by concern. Each field documents the env var that overrides
    it (the field name uppercased + prefixed with ``AG_``).
    """

    model_config = SettingsConfigDict(
        env_prefix="AG_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── identity ────────────────────────────────────────────────────────
    env: Literal["dev", "test", "staging", "prod"] = "dev"
    service_name: str = "agent-generator-backend"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # ── network ─────────────────────────────────────────────────────────
    host: str = "0.0.0.0"  # noqa: S104 — explicit listen-all for container
    port: int = 8000
    # CORS for the five shells: web (nginx), Tauri (file://, tauri://),
    # Capacitor (capacitor://, http://localhost), and the dev Vite server.
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "tauri://localhost",
            "https://tauri.localhost",
            "capacitor://localhost",
            "http://localhost",
        ]
    )

    # ── storage ─────────────────────────────────────────────────────────
    # SQLAlchemy URL. SQLite by default so `uvicorn app.main:app` works
    # with zero infra. Override with postgres+asyncpg://... in prod.
    database_url: str = "sqlite+aiosqlite:///./agent_generator.db"

    # ── upstream services ───────────────────────────────────────────────
    matrix_hub_url: AnyHttpUrl | None = None
    ollabridge_url: AnyHttpUrl | None = None

    # ── secrets backend (Batch 21) ──────────────────────────────────────
    # "memory" for dev, "vault" for prod. Vault wiring lands in Batch 21.
    secrets_backend: Literal["memory", "vault"] = "memory"
    vault_addr: AnyHttpUrl | None = None
    vault_token: str | None = None
    vault_namespace: str | None = None

    # ── auth (Batch 16) ─────────────────────────────────────────────────
    # JWT signing key. MUST be overridden in prod — the default raises a
    # warning at startup so insecure deployments are caught early.
    jwt_secret: str = "change-me-or-the-app-will-yell-at-you"  # noqa: S105
    jwt_algorithm: Literal["HS256", "RS256"] = "HS256"
    jwt_access_ttl_seconds: int = 60 * 60          # 1 hour
    jwt_refresh_ttl_seconds: int = 60 * 60 * 24 * 30  # 30 days

    # GitHub OAuth app. Create one at
    # https://github.com/settings/applications/new and set the callback
    # to ``${PUBLIC_URL}/api/auth/github/callback``.
    github_client_id: str | None = None
    github_client_secret: str | None = None
    # Public URL the SPA reaches (used to build OAuth redirect_uri and
    # the post-login bounce destination).
    public_url: str = "http://localhost:5173"

    # Bootstrap admin: the first GitHub login matching this email (or
    # username for users without a public email) is granted admin role.
    admin_email: str | None = None

    # CSRF / state cookie signing key. Reuses `jwt_secret` if unset.
    cookie_secret: str | None = None

    # ── telemetry (Batch 31) ────────────────────────────────────────────
    otlp_endpoint: AnyHttpUrl | None = None
    sentry_dsn: str | None = None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings accessor. Use this from FastAPI dependencies."""
    return Settings()
