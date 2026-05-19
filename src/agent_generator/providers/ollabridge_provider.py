"""OllaBridge / Ollama provider.

OllaBridge (https://huggingface.co/spaces/ruslanmv/ollabridge) is an
OpenAI-compatible gateway that fronts Ollama servers — local or
hosted. The same client also talks to a vanilla Ollama daemon at
http://localhost:11434/v1, so this provider doubles as the Ollama
provider when `provider="ollama"` is selected.

Auth modes:

* **Anonymous** — the public OllaBridge Space serves a free tier
  (qwen2.5:1.5b) without a key. Leave `ollabridge_token` empty.
* **Pairing token** — the OllaBridge dashboard hands out a one-shot
  pairing code (e.g. ``UKBZ-8303``). The backend's
  ``/api/ollabridge/pair`` endpoint exchanges that code for a bearer
  token; persist it as ``OLLABRIDGE_TOKEN`` and the SDK sends it on
  every call.
* **Raw API key** — any OpenAI-compatible deployment also accepts
  ``OLLABRIDGE_TOKEN`` straight as a bearer token.

No external SDK is required; the standard ``requests`` library (a core
dependency) handles everything.
"""

from __future__ import annotations

import math
from typing import Any, ClassVar

import requests

from agent_generator.providers.base import BaseProvider

DEFAULT_URL = "https://ruslanmv-ollabridge.hf.space"
DEFAULT_MODEL = "qwen2.5:1.5b"


class OllaBridgeProvider(BaseProvider):
    """Bridge to any OpenAI-compatible Ollama gateway (OllaBridge or local Ollama)."""

    name: ClassVar[str] = "ollabridge"
    PRICING_PER_1K: ClassVar[tuple[float, float]] = (0.0, 0.0)  # free tier

    def __init__(self, settings: Any) -> None:
        self.settings = settings
        self._base_url = (getattr(settings, "ollabridge_url", None) or DEFAULT_URL).rstrip("/")
        self._model = (
            getattr(settings, "ollabridge_model", None)
            or getattr(settings, "model", None)
            or DEFAULT_MODEL
        )
        self._token = getattr(settings, "ollabridge_token", None)
        # Allow either /v1 or bare-host base URLs.
        if not self._base_url.endswith("/v1"):
            self._base_url = f"{self._base_url}/v1"
        self._timeout = 120.0

    # ── HTTP helpers ────────────────────────────────────────────
    def _headers(self) -> dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self._token:
            h["Authorization"] = f"Bearer {self._token}"
        return h

    # ── BaseProvider contract ───────────────────────────────────
    def generate(self, prompt: str) -> str:
        payload = {
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": getattr(self.settings, "temperature", 0.7),
            "max_tokens": getattr(self.settings, "max_tokens", 4096),
        }
        resp = requests.post(
            f"{self._base_url}/chat/completions",
            headers=self._headers(),
            json=payload,
            timeout=self._timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"] or ""

    def tokenize(self, text: str) -> int:
        # OllaBridge / Ollama don't expose a tokenizer; estimate using
        # the conventional ~4 chars / token heuristic.
        return max(1, math.ceil(len(text) / 4))

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        return 0.0  # Free tier; paired commercial tiers configure their own pricing externally.

    # ── Discovery + health helpers (used by the Settings page) ──
    def list_models(self) -> list[str]:
        try:
            resp = requests.get(
                f"{self._base_url}/models",
                headers=self._headers(),
                timeout=10.0,
            )
            resp.raise_for_status()
            return [m.get("id", "") for m in resp.json().get("data", []) if m.get("id")]
        except requests.RequestException:
            return []

    def available(self) -> bool:
        try:
            resp = requests.get(
                f"{self._base_url}/models",
                headers=self._headers(),
                timeout=5.0,
            )
            return resp.status_code == 200
        except requests.RequestException:
            return False


class OllamaProvider(OllaBridgeProvider):
    """Local-Ollama variant — defaults to http://localhost:11434."""

    name: ClassVar[str] = "ollama"

    def __init__(self, settings: Any) -> None:
        # Honour OLLAMA_URL / OLLAMA_MODEL when present; fall back to
        # the local daemon's defaults. Reuse the OllaBridge transport.
        ollama_url = getattr(settings, "ollama_url", None) or "http://localhost:11434"
        # Patch settings into a shadow object so the parent class picks
        # up the local URL without mutating the user's Settings model.
        shadow = type("ShadowSettings", (), {})()
        for attr in dir(settings):
            if attr.startswith("_"):
                continue
            try:
                setattr(shadow, attr, getattr(settings, attr))
            except Exception:  # noqa: BLE001
                pass
        shadow.ollabridge_url = ollama_url
        shadow.ollabridge_model = (
            getattr(settings, "ollama_model", None)
            or getattr(settings, "model", None)
            or "qwen2.5:1.5b"
        )
        shadow.ollabridge_token = getattr(settings, "ollama_token", None)
        super().__init__(shadow)
