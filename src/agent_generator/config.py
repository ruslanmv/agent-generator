# ────────────────────────────────────────────────────────────────
#  src/agent_generator/config.py
# ────────────────────────────────────────────────────────────────
"""
Centralised, typed settings that every layer of *agent‑generator* reads
(CLI, providers, Flask UI, tests).

Configuration order of precedence
---------------------------------
1. Function arguments you pass to `Settings(**kwargs)`
2. Environment variables prefixed with ``AGENTGEN_``
3. Values loaded from a ``.env`` file in the project root
4. Hard‑coded defaults below

Example::

    export AGENTGEN_PROVIDER=openai
    export AGENTGEN_MODEL=gpt-4o
    agent-generator "Write a poem" ...

Anything in *all‑caps* matches the field name (upper‑snake) after the
``AGENTGEN_`` prefix::

    AGENTGEN_TEMPERATURE=0.5
"""

from __future__ import annotations

import functools
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseSettings, Field, validator
from pydantic.env_settings import SettingsError

# ────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────


def _project_root() -> Path:
    """Return repo root (two levels up from this file)."""
    return Path(__file__).resolve().parents[2]


# ────────────────────────────────────────────────
# Settings model
# ────────────────────────────────────────────────


class Settings(BaseSettings):
    """
    Runtime configuration for *agent‑generator*.

    Environment variables are read with the ``AGENTGEN_`` prefix, e.g.:

    * ``AGENTGEN_PROVIDER``
    * ``AGENTGEN_MODEL``
    """

    # LLM provider
    provider: Literal["watsonx", "openai"] = Field(
        default="watsonx",
        description="Name of the default LLM provider. "
        "May be overridden per request via CLI flags.",
    )

    # Model + sampling
    model: str = Field(
        default="meta-llama-3-70b-instruct",
        description="Model identifier understood by the chosen provider.",
    )
    temperature: float = Field(
        default=0.7,
        ge=0,
        le=2,
        description="Completion sampling temperature.",
    )
    max_tokens: int = Field(
        default=4096,
        ge=16,
        description="Token cap for a single completion.",
    )

    # Optional WatsonX credentials
    watsonx_api_key: Optional[str] = Field(
        default=None, env="WATSONX_API_KEY", description="IBM WatsonX API key."
    )
    watsonx_project_id: Optional[str] = Field(
        default=None, env="WATSONX_PROJECT_ID", description="WatsonX project ID."
    )
    watsonx_url: str = Field(
        default="https://us-south.ml.cloud.ibm.com",
        env="WATSONX_URL",
        description="WatsonX base URL.",
    )

    # Optional OpenAI credentials
    openai_api_key: Optional[str] = Field(
        default=None, env="OPENAI_API_KEY", description="OpenAI API key."
    )

    # Misc
    log_level: str = Field(
        default="INFO",
        regex="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$",
        description="Root logger level.",
    )
    mcp_default_port: int = Field(
        default=8080,
        ge=1,
        le=65535,
        description="Port used by generated MCP servers.",
    )

    class Config:  # noqa: D401, WPS306
        env_prefix = "AGENTGEN_"
        env_file = _project_root() / ".env"
        case_sensitive = False

    # ──────────────────────────────────
    # Validators / derived helpers
    # ──────────────────────────────────

    @validator("provider")
    def _validate_provider(cls, v: str) -> str:  # noqa: D401,N805
        if v == "openai" and not cls().openai_api_key:
            raise SettingsError(
                "Selected provider 'openai' but OPENAI_API_KEY is not set."
            )
        if v == "watsonx" and not cls().watsonx_api_key:
            raise SettingsError(
                "Selected provider 'watsonx' but WATSONX_API_KEY is not set."
            )
        return v

    # Convenience flags
    @property
    def is_watsonx(self) -> bool:  # noqa: D401
        return self.provider == "watsonx"

    @property
    def is_openai(self) -> bool:  # noqa: D401
        return self.provider == "openai"


# ────────────────────────────────────────────────
# Singleton accessor
# ────────────────────────────────────────────────


@functools.lru_cache(maxsize=1)
def get_settings() -> Settings:  # noqa: D401
    """
    Return a **cached** Settings instance.

    Import this function everywhere instead of constructing *Settings*
    manually; it guarantees single‑source‑of‑truth and lazy `.env`
    evaluation.
    """
    return Settings()  # type: ignore[arg-type]
