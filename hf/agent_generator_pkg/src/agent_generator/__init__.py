# ────────────────────────────────────────────────────────────────
#  src/agent_generator/__init__.py
# ────────────────────────────────────────────────────────────────
"""
🎉 **agent‑generator**

This package turns plain‑English requirements into ready‑to‑run multi‑agent
teams for CrewAI, LangGraph, ReAct, or watsonx Orchestrate.

Public surface
--------------
* `__version__`           – semantic‑version string
* `get_settings()`        – singleton accessor to global Settings
* `Settings`              – Pydantic config model (sub‑module import)
* `FRAMEWORKS`            – mapping name → framework generator class
* `PROVIDERS`             – mapping name → LLM provider class
"""

from __future__ import annotations

# ------------------------------------------------------------------ #
# Version
# ------------------------------------------------------------------ #
__version__: str = "0.2.1"

# ------------------------------------------------------------------ #
# Surface imports (lazy‑safe)
# ------------------------------------------------------------------ #
from agent_generator.config import Settings, get_settings  # noqa: E402
from agent_generator.frameworks import FRAMEWORKS  # noqa: E402
from agent_generator.providers import PROVIDERS  # noqa: E402

# Anything else you’d like to expose at package level goes here
__all__ = [
    "__version__",
    "Settings",
    "get_settings",
    "PROVIDERS",
    "FRAMEWORKS",
]
