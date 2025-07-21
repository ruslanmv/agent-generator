# ────────────────────────────────────────────────────────────────
#  src/agent_generator/providers/openai_provider.py
# ────────────────────────────────────────────────────────────────
"""
*Stub* OpenAI provider.

We ship only a placeholder so the core package stays slim.  Installing
the optional extra ``agent-generator[openai]`` replaces this stub with
a working implementation (see extras/ directory in future versions).
"""

from __future__ import annotations

from agent_generator.providers.base import BaseProvider


class OpenAIProvider(BaseProvider):  # noqa: D101
    name = "openai"

    def __init__(self, *a, **kw):  # noqa: D401
        raise ImportError(
            "OpenAI support is not installed.\n"
            "Run  pip install 'agent-generator[openai]'  to enable it."
        )

    # The following methods will never be reached, but exist so that
    # static type checkers recognise the interface.
    def generate(self, prompt: str, **kwargs) -> str:  # noqa: D401
        raise NotImplementedError

    def estimate_cost(
        self, prompt_tokens: int, completion_tokens: int
    ) -> float:  # noqa: D401,N802
        raise NotImplementedError
