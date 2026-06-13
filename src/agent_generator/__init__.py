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
__version__: str = "1.1.0"

# ------------------------------------------------------------------ #
# Surface imports (lazy‑safe)
# ------------------------------------------------------------------ #
from agent_generator.config import Settings, get_settings  # noqa: E402
from agent_generator.frameworks import FRAMEWORKS  # noqa: E402
from agent_generator.providers import PROVIDERS  # noqa: E402


def __getattr__(name: str):  # noqa: D401 - PEP 562 lazy export
    """Lazily expose the engine facade.

    ``AgentGenerator`` lives in ``agent_generator.engine``. It is exported here so callers
    can ``from agent_generator import AgentGenerator``. Lazy import keeps package import
    cheap and avoids importing the planning/build stack unless the engine is used.
    """
    if name == "AgentGenerator":
        from agent_generator.engine import AgentGenerator

        return AgentGenerator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# Anything else you’d like to expose at package level goes here
__all__ = [
    "__version__",
    "AgentGenerator",
    "Settings",
    "get_settings",
    "PROVIDERS",
    "FRAMEWORKS",
]
