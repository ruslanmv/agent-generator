# ────────────────────────────────────────────────────────────────
#  src/agent_generator/frameworks/watsonx_orchestrate/__init__.py
# ────────────────────────────────────────────────────────────────
"""
WatsonX Orchestrate framework plug‑in.

Typical use
-----------
    from agent_generator.frameworks import FRAMEWORKS
    yaml_src = FRAMEWORKS["watsonx_orchestrate"]().generate_code(
        workflow, settings
    )
"""

from .generator import WatsonXOrchestrateGenerator  # noqa: F401

__all__ = ["WatsonXOrchestrateGenerator"]
