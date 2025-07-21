# ────────────────────────────────────────────────────────────────
# src/agent_generator/providers/__init__.py
# ────────────────────────────────────────────────────────────────
"""
LLM provider registry.

Importing this module ensures each provider subclass registers itself
into the PROVIDERS dict in base.py.
"""

from .base import BaseProvider, PROVIDERS
from .watsonx_provider import WatsonXProvider
from .openai_provider import OpenAIProvider

__all__ = [
    "BaseProvider",
    "WatsonXProvider",
    "OpenAIProvider",
    "PROVIDERS",
]
