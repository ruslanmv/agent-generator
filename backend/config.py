# backend/config.py
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field, ValidationError


class Settings(BaseSettings):
    """
    Runtime configuration (12‑factor).

    • watsonx.ai is the default LLM provider — you *must* supply:
        WATSONX_API_KEY, WATSONX_URL, PROJECT_ID
    • Provide OPENAI_API_KEY only if you want an OpenAI fallback.

    All values are read from a local .env file or the process environment.
    Nothing is hard‑coded here.
    """

    # ───── LLM (watsonx.ai) ─────

    watsonx_api_key: str = Field(..., env="WATSONX_API_KEY")
    watsonx_project_id: str = Field(..., env="WATSONX_PROJECT_ID")
    watsonx_url: str = Field(..., env="WATSONX_URL")
    # Corrected field name and env var to match error log
    #optional Watsonx fields (may be blank)
    watsonx_space_id: str | None = Field(None, env="WATSONX_SPACE_ID")
    watsonx_region:   str | None = Field("us-south", env="WATSONX_REGION")
    watsonx_model_id: str | None = Field("meta-llama/llama-3-2-90b-vision-instruct", env="WATSONX_CHAT_MODEL")

     # Optional OpenAI (fallback)

    openai_api_key:    str | None = Field(None, env="OPENAI_API_KEY")
    openai_model_name: str | None = Field("gpt-4o-mini", env="OPENAI_MODEL_NAME")
    # HTTP server
    host: str = Field("0.0.0.0", env="BEE_BACKEND_HOST")
    port: int = Field(8000, env="BEE_BACKEND_PORT")

    # Build artefacts
    build_base: Path = Field("build", env="BUILD_BASE_DIR")

    class Config:
        # Construct a path to the .env file in the project root
        env_file = Path(__file__).resolve().parent.parent / ".env"
        env_file_encoding = "utf-8"
        extra = 'ignore'  # Ignore extra variables from .env


try:
    settings = Settings()
except ValidationError as exc:
    # Fail fast with a clear message if mandatory secrets are missing.
    missing = ", ".join(e["loc"][0] for e in exc.errors() if e['type'] == 'missing')
    if missing:
        raise RuntimeError(
            f"Missing mandatory environment variables: {missing}. "
            "Create a .env file or export them before running the backend."
        ) from exc
    # If there are other errors, raise the original exception
    raise exc