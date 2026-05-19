from __future__ import annotations

import functools
from pathlib import Path
from typing import Literal, Optional

from dotenv import load_dotenv
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict, SettingsError

# ────────────────────────────────────────────────────────────────
# Immediately load .env from the current working directory
# ────────────────────────────────────────────────────────────────
load_dotenv(dotenv_path=Path.cwd() / ".env", override=False)


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
        env_file=str(Path.cwd() / ".env"),
        case_sensitive=False,
        extra="ignore",
    )

    # LLM provider - default is *watsonx*
    provider: Literal["watsonx", "openai", "ollabridge", "ollama"] = Field(
        default="watsonx",
        description="Default LLM provider; can be overridden by CLI flag or env.",
    )

    # Global model + sampling
    model: str = Field(
        default="meta-llama/llama-3-3-70b-instruct",
        description="Model identifier understood by the chosen provider.",
    )
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=4096, ge=16)

    # Provider-specific model overrides (use validation_alias for env mapping)
    watsonx_model: Optional[str] = Field(default=None, validation_alias="WATSONX_MODEL")
    openai_model: Optional[str] = Field(default=None, validation_alias="OPENAI_MODEL")

    # Credentials
    watsonx_api_key: Optional[str] = Field(default=None, validation_alias="WATSONX_API_KEY")
    watsonx_project_id: Optional[str] = Field(default=None, validation_alias="WATSONX_PROJECT_ID")
    watsonx_url: str = Field(
        default="https://us-south.ml.cloud.ibm.com",
        validation_alias="WATSONX_URL",
    )
    openai_api_key: Optional[str] = Field(default=None, validation_alias="OPENAI_API_KEY")

    # OllaBridge / Ollama (OpenAI-compatible /v1 endpoints).
    # No credentials are required — the public OllaBridge Space serves
    # a free tier at qwen2.5:1.5b. Provide a token to unlock paid tiers
    # (returned by the device-pairing exchange).
    ollabridge_url: str = Field(
        default="https://ruslanmv-ollabridge.hf.space",
        validation_alias="OLLABRIDGE_URL",
    )
    ollabridge_model: Optional[str] = Field(default=None, validation_alias="OLLABRIDGE_MODEL")
    ollabridge_token: Optional[str] = Field(default=None, validation_alias="OLLABRIDGE_TOKEN")
    ollama_url: str = Field(
        default="http://localhost:11434",
        validation_alias="OLLAMA_URL",
    )
    ollama_model: Optional[str] = Field(default=None, validation_alias="OLLAMA_MODEL")
    ollama_token: Optional[str] = Field(default=None, validation_alias="OLLAMA_TOKEN")

    # Misc
    log_level: str = Field(default="INFO")
    mcp_default_port: int = Field(default=8080, ge=1, le=65535)

    # Skip credential validation (for dry-run / testing)
    skip_credential_check: bool = Field(default=False)

    # ──────────────────────────────────────────────────
    # Validators
    # ──────────────────────────────────────────────────
    @field_validator("log_level", mode="before")
    @classmethod
    def _normalise_log_level(cls, v: str) -> str:
        v_up = v.upper()
        if v_up not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError("log_level must be one of DEBUG | INFO | WARNING | ERROR | CRITICAL")
        return v_up

    @model_validator(mode="after")
    def _apply_overrides_and_check(self):
        # Apply provider-specific model override
        if self.provider == "watsonx" and self.watsonx_model:
            object.__setattr__(self, "model", self.watsonx_model)

        # For OpenAI, use explicit override or default to gpt-4o
        if self.provider == "openai":
            if self.openai_model:
                object.__setattr__(self, "model", self.openai_model)
            else:
                object.__setattr__(self, "model", "gpt-4o")

        # For OllaBridge / Ollama, default to qwen2.5:1.5b (the free
        # tier the public OllaBridge Space exposes) when the user
        # hasn't pinned a model.
        if self.provider == "ollabridge":
            object.__setattr__(self, "model", self.ollabridge_model or "qwen2.5:1.5b")
        elif self.provider == "ollama":
            object.__setattr__(self, "model", self.ollama_model or "qwen2.5:1.5b")

        # Skip credential checks if requested
        if self.skip_credential_check:
            return self

        # Credential checks with copy-pasteable guidance.
        # OllaBridge / Ollama: no credentials required; the gateway
        # decides whether to gate model access via the bearer token.
        if self.provider == "openai":
            if not self.openai_api_key:
                raise SettingsError(
                    "OPENAI_API_KEY is required.\n"
                    "Run  pip install 'agent-generator[openai]'  to enable OpenAI support.\n"
                    "Set it in your environment or .env file, e.g.:\n"
                    "  export OPENAI_API_KEY=sk-your-key-here"
                )

        if self.provider == "watsonx":
            missing = []
            if not self.watsonx_api_key:
                missing.append("WATSONX_API_KEY")
            if not self.watsonx_project_id:
                missing.append("WATSONX_PROJECT_ID")
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

    @property
    def is_ollabridge(self) -> bool:
        return self.provider == "ollabridge"

    @property
    def is_ollama(self) -> bool:
        return self.provider == "ollama"


# ────────────────────────────────────────────────
# Singleton accessor
# ────────────────────────────────────────────────
@functools.lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a *cached* Settings instance (lazy `.env` read)."""
    return Settings()


def get_settings_lenient() -> Settings:
    """Return Settings without credential validation (for parsing/planning)."""
    return Settings(skip_credential_check=True)
