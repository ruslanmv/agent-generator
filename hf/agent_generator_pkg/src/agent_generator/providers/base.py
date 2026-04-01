# ────────────────────────────────────────────────────────────────
#  src/agent_generator/providers/base.py
# ────────────────────────────────────────────────────────────────
"""
Abstract interface + shared helpers for every LLM provider.

Each concrete provider must implement:

* `generate(prompt: str, **kwargs) -> str`
* `estimate_cost(prompt_tokens: int, completion_tokens: int) -> float`

The tiny `tokenize()` helper is *good‑enough* for cost estimates; override
in subclasses for greater accuracy if needed.
"""
from __future__ import annotations

import math
import re
from abc import ABC, abstractmethod
from typing import ClassVar, Dict, Type

from agent_generator.config import Settings, get_settings

# Public registry populated via BaseProvider.__init_subclass__
PROVIDERS: Dict[str, Type[BaseProvider]] = {}


class BaseProvider(ABC):
    """Common behaviour & interface for all concrete providers."""

    #: human‑readable provider key (used in CLI flags)
    name: ClassVar[str] = "base"

    #: Per‑1K‑token pricing (prompt_cost, completion_cost) in USD
    PRICING_PER_1K: ClassVar[tuple[float, float]] = (0.0, 0.0)

    def __init_subclass__(cls, **kwargs) -> None:  # noqa: D401
        """
        Automatically register subclasses into the global PROVIDERS dict.
        Skip the abstract base itself (name=="base").
        """
        super().__init_subclass__(**kwargs)
        key = getattr(cls, "name", None)
        if not key or key == "base":
            return
        if key in PROVIDERS:
            raise RuntimeError(f"Duplicate provider registration: {key}")
        PROVIDERS[key] = cls

    def __init__(self, settings: Settings | None = None) -> None:
        """Store or retrieve the global Settings."""
        self.settings = settings or get_settings()

    # ------------------------------------------------------------------
    # Interface
    # ------------------------------------------------------------------
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Perform the LLM call and return the raw text completion.
        """
        ...

    # ------------------------------------------------------------------
    # Cost estimation
    # ------------------------------------------------------------------
    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """
        USD cost estimate based on 1K‑token pricing.

        Rounds up token counts to the next 1K block.
        """
        prompt_price, comp_price = self.PRICING_PER_1K
        return (
            math.ceil(prompt_tokens / 1000) * prompt_price
            + math.ceil(completion_tokens / 1000) * comp_price
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def tokenize(text: str) -> int:
        """
        Naïve whitespace‑based token count (approx. word count).
        """
        return len(re.findall(r"\S+", text))
