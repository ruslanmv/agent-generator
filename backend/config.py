# backend/config.py
"""
Runtime configuration for agent-generator (12-factor, import-safe).

Key guarantees:
- No import-time crashes. All fields are optional; validation happens on demand.
- Clear, self-explanatory runtime errors with actionable steps.
- Compatible with existing environments: supports PROJECT_ID as an alias for WATSONX_PROJECT_ID.
- Works even if there is no `.env` file (reads from process env when available).

Public API:
    - settings: BaseSettings instance (import-safe).
    - validate_runtime(framework: Optional[str]) -> None
"""

from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Environment-backed configuration (Pydantic v2).

    Notes:
      - All fields are Optional to avoid import-time validation failures.
      - Use `validate_runtime(framework)` to enforce required vars just-in-time.
      - Provider and framework determine which vars are required.
    """

    # ── Core provider selection ────────────────────────────────────────────────
    # Example: "watsonx" or "openai". If unset, framework may still require vars.
    provider: Optional[str] = Field(default=None, alias="AGENTGEN_PROVIDER")

    # ── WatsonX (required when provider="watsonx" OR framework="watsonx_orchestrate")
    watsonx_api_key: Optional[str] = Field(default=None, alias="WATSONX_API_KEY")
    watsonx_url: Optional[str] = Field(default=None, alias="WATSONX_URL")

    # Prefer WATSONX_PROJECT_ID; accept PROJECT_ID for backward compatibility.
    watsonx_project_id: Optional[str] = Field(default=None, alias="WATSONX_PROJECT_ID")
    project_id: Optional[str] = Field(default=None, alias="PROJECT_ID")

    # Optional extras
    watsonx_space_id: Optional[str] = Field(default=None, alias="WATSONX_SPACE_ID")
    watsonx_region: Optional[str] = Field(default="us-south", alias="WATSONX_REGION")
    watsonx_model_id: Optional[str] = Field(
        default="meta-llama/llama-3-2-90b-vision-instruct", alias="WATSONX_CHAT_MODEL"
    )

    # ── OpenAI (optional; only if you use the OpenAI provider/fallback) ───────
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_model_name: Optional[str] = Field(default="gpt-4o-mini", alias="OPENAI_MODEL_NAME")

    # ── Backend / Generator runtime ───────────────────────────────────────────
    bee_backend_host: Optional[str] = Field(default="0.0.0.0", alias="BEE_BACKEND_HOST")
    bee_backend_port: Optional[int] = Field(default=8000, alias="BEE_BACKEND_PORT")
    generator_backend_url: Optional[str] = Field(default="local", alias="GENERATOR_BACKEND_URL")
    build_base_dir: Optional[str] = Field(default="build", alias="BUILD_BASE_DIR")

    # Pydantic Settings model config
    model_config = SettingsConfigDict(
        env_file=".env",          # Falls back to OS env if .env is missing
        env_file_encoding="utf-8",
        extra="ignore",           # Ignore extra variables
        case_sensitive=False,
        populate_by_name=True,    # Allow using field names as env aliases when needed
    )


# Import-safe instantiation (no validation here)
settings = Settings()


def _coalesce(*vals: Optional[str]) -> Optional[str]:
    """Return the first non-empty value in vals, else None."""
    for v in vals:
        if v:
            return v
    return None


def _requires_watsonx(provider: Optional[str], framework: Optional[str]) -> bool:
    """Determine whether WatsonX credentials are required."""
    prov = (provider or "").lower()
    fw = (framework or "").lower()
    return prov == "watsonx" or fw == "watsonx_orchestrate"


def required_for(provider: Optional[str], framework: Optional[str]) -> List[str]:
    """
    Return the list of env keys required for the given provider/framework.
    Extend here if additional providers/frameworks introduce new requirements.
    """
    if _requires_watsonx(provider, framework):
        return ["WATSONX_API_KEY", "WATSONX_URL", "WATSONX_PROJECT_ID"]
    return []


def validate_runtime(framework: Optional[str] = None) -> None:
    """
    Validate configuration just-in-time (safe to call from CLI entry points).

    - Normalizes aliases (PROJECT_ID ⇒ WATSONX_PROJECT_ID).
    - Computes required keys for the current provider/framework.
    - If anything is missing, prints a friendly guide and exits with code 2.
    """
    # Normalize alias for project id
    if not settings.watsonx_project_id:
        settings.watsonx_project_id = _coalesce(settings.watsonx_project_id, settings.project_id)

    missing: List[str] = []
    for key in required_for(settings.provider, framework):
        if key == "WATSONX_API_KEY" and not settings.watsonx_api_key:
            missing.append(key)
        elif key == "WATSONX_URL" and not settings.watsonx_url:
            missing.append(key)
        elif key == "WATSONX_PROJECT_ID" and not settings.watsonx_project_id:
            missing.append(key)

    if missing:
        _print_missing_and_exit(missing)


def _print_missing_and_exit(missing: List[str]) -> None:
    """Pretty, self-explanatory error output suitable for local dev and CI."""
    print("\n❌ Configuration incomplete.\n")
    print("The following environment variables are required but not set:")
    for m in missing:
        print(f"  • {m}")

    print("\nHow to fix:")
    print("  1) Create or edit a file named `.env` in the project root (same folder as `Makefile`).")
    print("     If `.env` does not exist, it will still read from your shell environment.")
    print("     You can use `.env.template` as a reference if present.\n")
    print("  2) For WatsonX, include the following keys:")
    print("       AGENTGEN_PROVIDER=watsonx")
    print("       WATSONX_API_KEY=<your-api-key>")
    print("       WATSONX_URL=https://us-south.ml.cloud.ibm.com")
    print("       # Either of these works for the project id:")
    print("       WATSONX_PROJECT_ID=<your-project-id>")
    print("       # or (legacy alias)")
    print("       PROJECT_ID=<your-project-id>\n")
    print("  3) Re-run your command, for example:")
    print("       make run PROMPT='Generate a customer service agent for healthcare' FRAMEWORK=watsonx_orchestrate\n")

    # Exit with a non-zero code appropriate for CI “configuration error”
    raise SystemExit(2)


__all__ = ["Settings", "settings", "validate_runtime"]
