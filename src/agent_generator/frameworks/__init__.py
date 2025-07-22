# ────────────────────────────────────────────────────────────────
#  src/agent_generator/frameworks/__init__.py
# ────────────────────────────────────────────────────────────────
"""
Framework generators registry.

Each import below registers its subclass in the FRAMEWORKS dict
via BaseFrameworkGenerator.__init_subclass__.
"""

from .base import FRAMEWORKS, BaseFrameworkGenerator
from .crewai import CrewAIGenerator
from .crewai_flow import CrewAIFlowGenerator
from .langgraph import LangGraphGenerator
from .react import ReActGenerator
from .watsonx_orchestrate import WatsonXOrchestrateGenerator

__all__ = [
    "BaseFrameworkGenerator",
    "FRAMEWORKS",
    "CrewAIGenerator",
    "CrewAIFlowGenerator",
    "LangGraphGenerator",
    "ReActGenerator",
    "WatsonXOrchestrateGenerator",
]
