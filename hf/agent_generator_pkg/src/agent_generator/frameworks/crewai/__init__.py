"""
CrewAI framework plug‑in.

Example
-------
    from agent_generator.frameworks import FRAMEWORKS
    py_src = FRAMEWORKS["crewai"]().generate_code(workflow, settings, mcp=True)
"""

from .generator import CrewAIGenerator  # noqa: F401

__all__ = ["CrewAIGenerator"]
