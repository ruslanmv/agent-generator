# ────────────────────────────────────────────────────────────────
#  src/agent_generator/providers/base.py
# ────────────────────────────────────────────────────────────────
"""
Abstract interface + shared helpers for every LLM provider.

Each concrete provider must implement:

* ``generate(prompt: str, **kw) -> str``
* ``estimate_cost(prompt_tokens: int, completion_tokens: int) -> float``

The tiny `tokenize()` helper is *good‑enough* for cost estimates; if you
need perfect accuracy, override it in the child class.
"""

from __future__ import annotations

import math
import re
from abc import ABC, abstractmethod
from typing import ClassVar

from agent_generator.config import Settings, get_settings


class BaseProvider(ABC):
    """Common behaviour for all concrete providers."""

    #: human‑readable provider name (e.g. ``"watsonx"``)
    name: ClassVar[str]

    #: Per‑1K‑token cost (prompt, completion).  **Override in subclass.**
    PRICING_PER_1K: ClassVar[tuple[float, float]] = (0.0, 0.0)

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    # ───────────────────────────────────────────────
    # Abstract interface
    # ───────────────────────────────────────────────

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:  # noqa: D401
        """Return the raw text completion from the LLM."""

    # ───────────────────────────────────────────────
    # Cost estimation
    # ───────────────────────────────────────────────

    def estimate_cost(
        self, prompt_tokens: int, completion_tokens: int
    ) -> float:  # noqa: D401
        """
        Rough USD cost for the request.

        Multiply the prompt‑token price and completion‑token price by
        1K‑token blocks (rounded *up*).
        """
        prompt_price, comp_price = self.PRICING_PER_1K
        return (
            math.ceil(prompt_tokens / 1000) * prompt_price
            + math.ceil(completion_tokens / 1000) * comp_price
        )

    # ───────────────────────────────────────────────
    # Helpers
    # ───────────────────────────────────────────────

    @staticmethod
    def tokenize(text: str) -> int:  # noqa: D401
        """Naïve whitespace tokeniser (≈ OpenAI / llama tokens ≈ 0.75 words)."""
        return len(re.findall(r"\S+", text))
