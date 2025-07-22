# ────────────────────────────────────────────────────────────────
# src/agent_generator/providers/__init__.py
# ────────────────────────────────────────────────────────────────
"""
LLM provider registry.

Importing this module ensures each provider subclass registers itself
into the PROVIDERS dict in base.py.
"""

from .base import PROVIDERS, BaseProvider
from .openai_provider import OpenAIProvider
from .watsonx_provider import WatsonXProvider

__all__ = [
    "BaseProvider",
    "WatsonXProvider",
    "OpenAIProvider",
    "PROVIDERS",
]
