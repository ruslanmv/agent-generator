"""
OpenAI provider for agent-generator.
Requires the extra:
    pip install "agent-generator[openai]"
which pulls in `openai` (>= 1.30) and tiktoken.
"""

from __future__ import annotations

try:
    import openai  # noqa: F401
except ModuleNotFoundError as exc:  # pragma: no cover
    raise ImportError(
        "OpenAI support is not installed.\n"
        "Run  pip install agent-generator[openai]  to enable it."
    ) from exc
import openai as _oai
import tiktoken

from agent_generator.providers.base import BaseProvider


class OpenAIProvider(BaseProvider):
    """
    Thin wrapper around the official OpenAI SDK.
    """

    name = "openai"

    # ------- construction / config -------------------------------------------------
    def __init__(self, settings):  # noqa: D401
        self.settings = settings
        _oai.api_key = settings.openai_api_key
        # let users override via env if they want organisation etc.

        # Chat-completions client
        self._client = _oai.OpenAI()

    # ------- LLM call --------------------------------------------------------------
    def generate(self, prompt: str) -> str:
        """
        Calls /chat/completions with a single user message.
        Returns only the assistant message content.
        """
        resp = self._client.chat.completions.create(
            model=self.settings.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.settings.temperature,
            max_tokens=self.settings.max_tokens,
        )
        return resp.choices[0].message.content  # type: ignore[attr-defined]

    # ------- Helper utilities ------------------------------------------------------
    def tokenize(self, text: str) -> int:
        """
        Rough token estimate with tiktoken’s cl100k_base encoding (the default for GPT-4/3.5).
        """
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Naïve cost calculator using current published prices
        (as of 2025-07 — update if OpenAI changes).

        GPT-4o (most common) — $0.005 / 1K prompt tokens, $0.015 / 1K completion.
        """
        prompt_cost = 0.005 * prompt_tokens / 1000
        completion_cost = 0.015 * completion_tokens / 1000
        return prompt_cost + completion_cost
