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
    Runtime configuration for *agent-generator*.

    Environment variables with the prefix **AGENTGEN_** are read automatically,
    but none are required.
    If **AGENTGEN_PROVIDER** is *omitted*, the provider defaults to **watsonx**.
    """

    model_config = SettingsConfigDict(
        env_prefix="AGENTGEN_",
        env_file=str(_project_root() / ".env"),
        case_sensitive=False,
        extra="ignore",
    )

    # LLM provider ─ default is *watsonx* when nothing is specified
    provider: Literal["watsonx", "openai"] = Field(
        default="watsonx",
        description="Default LLM provider; can be overridden by CLI flag or env.",
    )

    # Global model + sampling
    model: str = Field(
        default="meta-llama/llama-3-2-90b-vision-instruct",
        description="Model identifier understood by the chosen provider.",
    )
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=4096, ge=16)

    # Provider-specific model overrides
    watsonx_model: Optional[str] = Field(default=None, env="WATSONX_MODEL")
    openai_model: Optional[str] = Field(default=None, env="OPENAI_MODEL")

    # Credentials
    watsonx_api_key: Optional[str] = Field(default=None, env="WATSONX_API_KEY")
    watsonx_project_id: Optional[str] = Field(default=None, env="WATSONX_PROJECT_ID")
    watsonx_url: str = Field(
        default="https://us-south.ml.cloud.ibm.com", env="WATSONX_URL"
    )
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")

    # Misc
    log_level: str = Field(default="INFO")
    mcp_default_port: int = Field(default=8080, ge=1, le=65535)

    # ──────────────────────────────────────────────────
    # Validators
    # ──────────────────────────────────────────────────
    @field_validator("log_level", mode="before")
    @classmethod
    def _normalise_log_level(cls, v: str) -> str:
        v_up = v.upper()
        if v_up not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError(
                "log_level must be one of DEBUG | INFO | WARNING | ERROR | CRITICAL"
            )
        return v_up

    @model_validator(mode="after")
    def _apply_overrides_and_check(self):
        # Apply provider-specific model override
        if self.provider == "watsonx" and self.watsonx_model:
            object.__setattr__(self, "model", self.watsonx_model)
        if self.provider == "openai" and self.openai_model:
            object.__setattr__(self, "model", self.openai_model)

        # Credential checks with copy-pasteable guidance
        if self.provider == "openai":
            if not self.openai_api_key:
                raise SettingsError(
                    "OPENAI_API_KEY is required.\n"
                    "Set it in your environment or .env file, e.g.\n"
                    "  export OPENAI_API_KEY=sk-your-key-here"
                )

        if self.provider == "watsonx":
            missing = []
            if not self.watsonx_api_key:
                missing.append("WATSONX_API_KEY")
            if not self.watsonx_project_id:
                missing.append("WATSONX_PROJECT_ID")
            # watsonx_url has a default, so it's never technically missing, but we
            # still show the recommended export in the error message for clarity.
            if missing:
                raise SettingsError(
                    "Watsonx credentials missing: " + ", ".join(missing) + ".\n"
                    "Set the required environment variables (example):\n"
                    "  export WATSONX_API_KEY=...\n"
                    "  export WATSONX_PROJECT_ID=...\n"
                    "  export WATSONX_URL=https://us-south.ml.cloud.ibm.com\n"
                    "Or add the same keys to your .env file."
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
