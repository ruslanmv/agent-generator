from __future__ import annotations

import functools
from pathlib import Path
from typing import Literal, Optional

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict, SettingsError


# ────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────
def _project_root() -> Path:
    """Return repo root (two levels up from this file)."""
    return Path(__file__).resolve().parents[2]


# ────────────────────────────────────────────────────────────────
# Settings model
# ────────────────────────────────────────────────────────────────
class Settings(BaseSettings):
    """
    Runtime configuration for *agent‑generator*.

    Env‑vars are read with the `AGENTGEN_` prefix, e.g.:

        AGENTGEN_MODEL=gpt-4o
    """

    model_config = SettingsConfigDict(
        env_prefix="AGENTGEN_",
        env_file=str(_project_root() / ".env"),
        case_sensitive=False,
        extra="ignore",  # ignore unknown/legacy vars (e.g. WATSONX_MODEL)
    )

    # LLM provider
    provider: Literal["watsonx", "openai"] = Field(
        default="watsonx",
        description="Default LLM provider; can be overridden by CLI flag.",
    )

    # Global model + sampling (may be overridden by provider-specific)
    model: str = Field(
        default="meta-llama/llama-3-2-90b-vision-instruct",
        description="Model identifier understood by the chosen provider.",
    )
    temperature: float = Field(
        default=0.7,
        ge=0,
        le=2,
        description="Sampling temperature.",
    )
    max_tokens: int = Field(
        default=4096,
        ge=16,
        description="Token cap for a single call.",
    )

    # Provider-specific model overrides
    watsonx_model: Optional[str] = Field(
        default=None,
        env="WATSONX_MODEL",
        description="Optional override for WatsonX model ID.",
    )
    openai_model: Optional[str] = Field(
        default=None,
        env="OPENAI_MODEL",
        description="Optional override for OpenAI model ID.",
    )

    # WatsonX credentials
    watsonx_api_key: Optional[str] = Field(
        default=None,
        env="WATSONX_API_KEY",
        description="IBM WatsonX API key.",
    )
    watsonx_project_id: Optional[str] = Field(
        default=None,
        env="WATSONX_PROJECT_ID",
        description="WatsonX project ID.",
    )
    watsonx_url: str = Field(
        default="https://us-south.ml.cloud.ibm.com",
        env="WATSONX_URL",
        description="WatsonX base URL.",
    )

    # OpenAI credentials
    openai_api_key: Optional[str] = Field(
        default=None,
        env="OPENAI_API_KEY",
        description="OpenAI API key.",
    )

    # Misc
    log_level: str = Field(
        default="INFO",
        description="Root logger level (DEBUG, INFO, WARNING, ERROR, CRITICAL).",
    )
    mcp_default_port: int = Field(
        default=8080,
        ge=1,
        le=65535,
        description="Port used by generated MCP servers.",
    )

    # ──────────────────────────────────────────────────
    # Field validator for log_level
    # ──────────────────────────────────────────────────
    @field_validator("log_level", mode="before")
    @classmethod
    def _normalise_log_level(cls, v: str) -> str:
        v_up = v.upper()
        if v_up not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError(
                "log_level must be one of DEBUG|INFO|WARNING|ERROR|CRITICAL"
            )
        return v_up

    # ──────────────────────────────────────────────────
    # Model-level validator: apply overrides and check creds
    # ──────────────────────────────────────────────────
    @model_validator(mode="after")
    def _apply_overrides_and_check(self):
        # Apply provider-specific model override
        if self.provider == "watsonx" and self.watsonx_model:
            object.__setattr__(self, "model", self.watsonx_model)
        if self.provider == "openai" and self.openai_model:
            object.__setattr__(self, "model", self.openai_model)

        # Ensure API keys present
        if self.provider == "openai" and not self.openai_api_key:
            raise SettingsError(
                "Selected provider 'openai' but OPENAI_API_KEY is not set."
            )
        if self.provider == "watsonx" and not self.watsonx_api_key:
            raise SettingsError(
                "Selected provider 'watsonx' but WATSONX_API_KEY is not set."
            )
        return self

    # Convenience flags
    @property
    def is_watsonx(self) -> bool:
        return self.provider == "watsonx"

    @property
    def is_openai(self) -> bool:
        return self.provider == "openai"


# ────────────────────────────────────────────────
# Singleton accessor
# ────────────────────────────────────────────────
@functools.lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a *cached* Settings instance (lazy `.env` read)."""
    return Settings()
