"""
Unified inference client supporting Ollama, OllaBridge, and OpenAI-compatible endpoints.

Provider hierarchy:
  1. OllaBridge (remote, OpenAI-compatible /v1 API)
  2. Ollama (local, OpenAI-compatible /v1 API at :11434)
  3. OpenAI / any OpenAI-compatible server

All three expose the same /v1/chat/completions and /v1/models interface.
"""

from __future__ import annotations

import json
import os
import re
import threading
from typing import Optional

import requests

# ── Defaults ────────────────────────────────────────────────────────

PROVIDER_DEFAULTS = {
    "ollama": {
        "base_url": "http://localhost:11434",
        "model": "qwen2.5:1.5b",
        "api_key": "",
    },
    "ollabridge": {
        "base_url": "http://localhost:8000",
        "model": "qwen2.5:1.5b",
        "api_key": "",
    },
    "openai": {
        "base_url": "https://api.openai.com",
        "model": "gpt-4o",
        "api_key": "",
    },
}


class InferenceSettings:
    """Thread-safe mutable settings for the inference provider."""

    def __init__(self):
        self._lock = threading.Lock()
        # Determine initial provider
        self.provider: str = os.environ.get("LLM_PROVIDER", "ollama")
        defaults = PROVIDER_DEFAULTS.get(self.provider, PROVIDER_DEFAULTS["ollama"])

        self.base_url: str = os.environ.get(
            "OLLABRIDGE_BASE_URL",
            os.environ.get("OLLAMA_BASE_URL", defaults["base_url"]),
        )
        self.model: str = os.environ.get(
            "OLLABRIDGE_MODEL",
            os.environ.get("OLLAMA_MODEL", defaults["model"]),
        )
        self.api_key: str = os.environ.get(
            "OLLABRIDGE_API_KEY",
            os.environ.get("OPENAI_API_KEY", defaults["api_key"]),
        )
        self.temperature: float = float(os.environ.get("LLM_TEMPERATURE", "0.7"))
        self.max_tokens: int = int(os.environ.get("LLM_MAX_TOKENS", "4096"))
        # OllaBridge pairing
        self.pair_token: str = ""
        self.device_id: str = ""
        self.auth_mode: str = "local"  # "local" | "api_key" | "pairing"

    def update(self, **kwargs) -> dict:
        """Update settings. Returns the new state."""
        with self._lock:
            for key in (
                "provider",
                "base_url",
                "model",
                "api_key",
                "temperature",
                "max_tokens",
                "pair_token",
                "device_id",
                "auth_mode",
            ):
                if key in kwargs and kwargs[key] is not None:
                    val = kwargs[key]
                    if key == "temperature":
                        val = max(0.0, min(2.0, float(val)))
                    elif key == "max_tokens":
                        val = max(1, int(val))
                    setattr(self, key, val)
            # If provider changed, apply defaults for empty fields
            if "provider" in kwargs:
                defaults = PROVIDER_DEFAULTS.get(self.provider, {})
                if not self.base_url or self.base_url in [
                    d["base_url"] for d in PROVIDER_DEFAULTS.values()
                ]:
                    self.base_url = defaults.get("base_url", self.base_url)
                if not self.model or self.model in [d["model"] for d in PROVIDER_DEFAULTS.values()]:
                    self.model = defaults.get("model", self.model)
        return self.to_dict()

    def to_dict(self) -> dict:
        return {
            "provider": self.provider,
            "base_url": self.base_url,
            "model": self.model,
            "api_key": "***" if self.api_key else "",
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "auth_mode": self.auth_mode,
            "paired": bool(self.pair_token),
            "device_id": self.device_id,
        }


class InferenceClient:
    """Unified client for Ollama / OllaBridge / OpenAI-compatible endpoints."""

    def __init__(self, settings: InferenceSettings):
        self.settings = settings

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        # Use pair_token if in pairing mode, otherwise api_key
        token = ""
        if self.settings.auth_mode == "pairing" and self.settings.pair_token:
            token = self.settings.pair_token
        elif self.settings.api_key:
            token = self.settings.api_key
        if token:
            h["Authorization"] = f"Bearer {token}"
        return h

    def _api_base(self) -> str:
        base = self.settings.base_url.rstrip("/")
        # Ollama native API is at /v1, OllaBridge too
        if not base.endswith("/v1"):
            return f"{base}/v1"
        return base

    @property
    def available(self) -> bool:
        """Check if the endpoint is reachable."""
        try:
            resp = requests.get(
                f"{self._api_base()}/models",
                headers=self._headers(),
                timeout=3,
            )
            return resp.status_code == 200
        except Exception:
            return False

    def list_models(self) -> list[str]:
        """Get available models."""
        try:
            resp = requests.get(
                f"{self._api_base()}/models",
                headers=self._headers(),
                timeout=5,
            )
            if resp.status_code == 200:
                data = resp.json()
                return [m.get("id", "") for m in data.get("data", [])]
        except Exception:
            pass
        return []

    def generate(
        self,
        prompt: str,
        system: str = "",
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """Generate a chat completion."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.settings.model,
            "messages": messages,
            "temperature": (temperature if temperature is not None else self.settings.temperature),
            "max_tokens": (max_tokens if max_tokens is not None else self.settings.max_tokens),
        }

        resp = requests.post(
            f"{self._api_base()}/chat/completions",
            headers=self._headers(),
            json=payload,
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    def generate_plan(self, prompt: str) -> Optional[dict]:
        """Use the LLM to generate a structured project plan."""
        system_prompt = (
            "You are an expert AI systems architect. Given a user request, produce a JSON project plan.\n\n"
            "Output ONLY valid JSON with this structure:\n"
            '{\n  "name": "project-slug",\n  "description": "One-line description",\n'
            '  "framework": "crewai",\n'
            '  "agents": [{"id": "agent_id", "role": "Role Name", "goal": "What they do", '
            '"backstory": "Background", "tools": ["tool_id"]}],\n'
            '  "tasks": [{"id": "task_id", "description": "What to do", "agent_id": "agent_id", '
            '"expected_output": "What it produces", "depends_on": []}],\n'
            '  "tools": [{"id": "tool_id", "template": "web_search"}]\n}\n\n'
            "Available frameworks: crewai, langgraph, watsonx_orchestrate, crewai_flow, react\n"
            "Available tools: web_search, pdf_reader, http_client, sql_query, vector_search, file_writer\n"
            "Use snake_case for IDs. Create distinct agents with clear roles."
        )
        try:
            raw = self.generate(prompt, system=system_prompt, temperature=0.3)
            match = re.search(r"```(?:json)?\s*\n?(.*?)```", raw, re.DOTALL)
            if match:
                raw = match.group(1)
            else:
                match = re.search(r"\{.*\}", raw, re.DOTALL)
                if match:
                    raw = match.group(0)
            return json.loads(raw.strip())
        except Exception:
            return None


# ── Singletons ──────────────────────────────────────────────────────

_settings: Optional[InferenceSettings] = None
_client: Optional[InferenceClient] = None


def get_inference_settings() -> InferenceSettings:
    global _settings
    if _settings is None:
        _settings = InferenceSettings()
    return _settings


def get_inference_client() -> InferenceClient:
    global _client
    if _client is None:
        _client = InferenceClient(get_inference_settings())
    return _client
