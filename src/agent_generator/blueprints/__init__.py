"""Blueprint candidate engine (Batch 4).

Idea parsing, template families, deterministic scoring, and candidate generation. Models
re-export the canonical contracts (``BlueprintSpec``, ``BlueprintCandidate``, ``TaskSpec``)
so architecture-doc import paths keep working.
"""

from __future__ import annotations

from agent_generator.blueprints.batch_planner import plan_batch, plan_repair_batch
from agent_generator.blueprints.candidate_generator import base_slug, generate_candidates
from agent_generator.blueprints.idea_parser import ParsedIdea, parse_idea_request
from agent_generator.blueprints.models import (
    BlueprintCandidate,
    BlueprintResult,
    BlueprintSpec,
    BlueprintStack,
    BlueprintTask,
    TaskSpec,
)
from agent_generator.blueprints.scorer import score_candidate
from agent_generator.blueprints.templates import (
    FLAGSHIP_TEMPLATES,
    GENERIC,
    TemplateFamily,
    TemplateTask,
    detect_template,
)

__all__ = [
    "plan_batch",
    "plan_repair_batch",
    "base_slug",
    "generate_candidates",
    "ParsedIdea",
    "parse_idea_request",
    "score_candidate",
    "FLAGSHIP_TEMPLATES",
    "GENERIC",
    "TemplateFamily",
    "TemplateTask",
    "detect_template",
    "BlueprintCandidate",
    "BlueprintResult",
    "BlueprintSpec",
    "BlueprintStack",
    "BlueprintTask",
    "TaskSpec",
]
