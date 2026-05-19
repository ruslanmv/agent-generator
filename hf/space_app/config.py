"""Configuration for the Hugging Face Space demo backend.

All inputs come from environment variables so the Space can be
re-configured via HF Space secrets without rebuilding the image.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class SpaceSettings(BaseSettings):
    """Runtime knobs surfaced to the Space."""

    # ── Provider selection ────────────────────────────────────────
    # The demo defaults to OllaBridge so visitors get real LLM
    # planning out of the box — the public OllaBridge Space at
    # ruslanmv-ollabridge.hf.space serves a free tier
    # (qwen2.5:1.5b) without any credentials. Set AG_DEMO_PROVIDER to
    # `keyword` to disable LLM planning, or to `watsonx` / `openai`
    # with matching credentials for higher-quality plans.
    provider: Literal["keyword", "ollabridge", "ollama", "watsonx", "openai"] = "ollabridge"

    # OllaBridge — defaults point at the public free-tier Space.
    ollabridge_url: str = "https://ruslanmv-ollabridge.hf.space"
    ollabridge_model: str = "qwen2.5:1.5b"
    ollabridge_token: str | None = None

    # Other providers (only used when AG_DEMO_PROVIDER is set to them).
    watsonx_api_key: str | None = None
    watsonx_project_id: str | None = None
    openai_api_key: str | None = None

    # ── SPA static bundle ─────────────────────────────────────────
    spa_dir: Path = Path("/app/frontend_dist")

    # ── In-memory store limits ────────────────────────────────────
    max_projects: int = 50  # demo store ring-buffers at this size

    model_config = SettingsConfigDict(
        env_prefix="AG_DEMO_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> SpaceSettings:
    """Cached settings accessor used as a FastAPI dependency."""
    return SpaceSettings()
