"""Deterministic candidate scoring (Batch 4).

Scores are 0..1 and fully reproducible: template keyword fit, requested-quality match, and
preferred-stack overlap. Each score comes with a human-readable rationale so the UI can show
*why* a candidate is recommended rather than a bare number.
"""

from __future__ import annotations

from agent_generator.blueprints.idea_parser import ParsedIdea
from agent_generator.contracts.common import QualityLevel
from agent_generator.contracts.idea import IdeaRequest


def score_candidate(
    parsed: ParsedIdea,
    request: IdeaRequest,
    level: QualityLevel,
    stack: list[str],
) -> tuple[float, str]:
    """Return ``(score, rationale)`` for one quality-level candidate."""
    reasons: list[str] = []

    # Template fit: how strongly the idea matched a flagship template.
    if parsed.template.template_id != "generic":
        fit = min(1.0, len(parsed.matched_keywords) / 3)
        reasons.append(
            f"Matches the {parsed.template.name} template "
            f"({', '.join(parsed.matched_keywords[:3])})."
        )
    else:
        fit = 0.5
        reasons.append("Built from your idea with the generic controlled template.")

    # Quality match: candidates at the requested level score higher.
    requested = request.quality_level
    if level == requested or (
        requested == QualityLevel.ENTERPRISE and level == QualityLevel.PRODUCTION
    ):
        quality = 1.0
        reasons.append(f"Matches your requested {requested.value} quality level.")
    elif level == QualityLevel.STANDARD:
        quality = 0.75
        reasons.append("Standard level: the recommended default balance.")
    else:
        quality = 0.5

    # Constraint fit: overlap with the user's preferred stack, penalty for forbidden items.
    preferred = {s.lower() for s in request.constraints.preferred_stack}
    forbidden = {s.lower() for s in request.constraints.forbidden_stack}
    stack_lower = {s.lower() for s in stack}
    constraint = 1.0
    if preferred:
        overlap = len(preferred & stack_lower) / len(preferred)
        constraint = 0.5 + 0.5 * overlap
        if overlap:
            reasons.append("Includes parts of your preferred stack.")
    if forbidden & stack_lower:
        constraint *= 0.4
        reasons.append("Warning: overlaps your forbidden stack; review before selecting.")

    score = round(0.5 * fit + 0.3 * quality + 0.2 * constraint, 3)
    return score, " ".join(reasons)


__all__ = ["score_candidate"]
