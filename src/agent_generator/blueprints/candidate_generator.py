"""Blueprint candidate generation (Batch 4).

Produces exactly three quality-tiered candidates (starter / standard / production) for a
parsed idea, using the detected template family for stacks, slugs, sizes, and summaries, and
the deterministic scorer for recommendation rationale. The output is the shared contract
``BlueprintCandidate`` — the shape Matrix Builder renders as candidate cards.
"""

from __future__ import annotations

from agent_generator.blueprints.idea_parser import ParsedIdea, parse_idea_request
from agent_generator.blueprints.scorer import score_candidate
from agent_generator.contracts.blueprint import BlueprintCandidate
from agent_generator.contracts.common import QualityLevel
from agent_generator.contracts.idea import IdeaRequest
from agent_generator.runtime import EngineRuntime

_LEVEL_META: dict[QualityLevel, dict[str, str]] = {
    QualityLevel.STARTER: {
        "title": "Starter controlled blueprint",
        "effort": "a weekend",
        "difficulty": "easy",
        "profile": "starter",
    },
    QualityLevel.STANDARD: {
        "title": "Standard Matrix Bundle",
        "effort": "about one week",
        "difficulty": "medium",
        "profile": "standard",
    },
    QualityLevel.PRODUCTION: {
        "title": "Production-ready controlled blueprint",
        "effort": "about three weeks",
        "difficulty": "hard",
        "profile": "production",
    },
}

_LEVEL_ACTIONS: dict[QualityLevel, list[str]] = {
    QualityLevel.STARTER: [
        "create_control_files",
        "create_starter_scaffold",
        "create_prompt_pack",
    ],
    QualityLevel.STANDARD: [
        "create_control_files",
        "create_prompt_pack",
        "create_validation_plan",
    ],
    QualityLevel.PRODUCTION: [
        "create_signed_bundle",
        "create_prompt_pack",
        "create_release_evidence",
    ],
}

_LEVEL_CHECKS: dict[QualityLevel, list[str]] = {
    QualityLevel.STARTER: ["required_files_present", "control_files_unchanged"],
    QualityLevel.STANDARD: [
        "required_files_present",
        "forbidden_changes_absent",
        "dependency_drift_absent",
    ],
    QualityLevel.PRODUCTION: [
        "sbom_present",
        "attestation_present",
        "policy_validation_passes",
    ],
}

_SLUG_SUFFIX: dict[QualityLevel, str] = {
    QualityLevel.STARTER: "-starter",
    QualityLevel.STANDARD: "",
    QualityLevel.PRODUCTION: "-production",
}


def base_slug(parsed: ParsedIdea, runtime: EngineRuntime) -> str:
    """The candidate slug root: the template slug, or one derived from the idea."""
    if parsed.template.slug:
        return parsed.template.slug
    return runtime.slugify(parsed.normalized_idea)


def _summary_for(parsed: ParsedIdea, level: QualityLevel) -> str:
    if parsed.template.template_id != "generic":
        prefix = {
            QualityLevel.STARTER: "Small controlled build of",
            QualityLevel.STANDARD: "Recommended controlled build of",
            QualityLevel.PRODUCTION: "Hardened, release-ready build of",
        }[level]
        return f"{prefix} {parsed.template.name}: {parsed.template.summary}"
    prefix = {
        QualityLevel.STARTER: "Small controlled build package for",
        QualityLevel.STANDARD: "Recommended controlled app blueprint for",
        QualityLevel.PRODUCTION: "Hardened Matrix Bundle with release evidence for",
    }[level]
    return f"{prefix}: {parsed.normalized_idea[:120]}"


def _recommended_level(requested: QualityLevel) -> QualityLevel:
    if requested == QualityLevel.STARTER:
        return QualityLevel.STARTER
    if requested in {QualityLevel.PRODUCTION, QualityLevel.ENTERPRISE}:
        return QualityLevel.PRODUCTION
    return QualityLevel.STANDARD


def generate_candidates(
    request: IdeaRequest,
    runtime: EngineRuntime,
    *,
    parsed: ParsedIdea | None = None,
) -> list[BlueprintCandidate]:
    """Generate the three quality-tiered candidates for an idea."""
    parsed = parsed or parse_idea_request(request)
    slug_root = base_slug(parsed, runtime)
    recommended = _recommended_level(request.quality_level)

    candidates: list[BlueprintCandidate] = []
    for level in (QualityLevel.STARTER, QualityLevel.STANDARD, QualityLevel.PRODUCTION):
        meta = _LEVEL_META[level]
        stack = parsed.template.stack_for(level)
        score, rationale = score_candidate(parsed, request, level, stack)
        candidates.append(
            BlueprintCandidate(
                candidate_id=runtime.stable_id(
                    "cand", parsed.normalized_idea, parsed.template.template_id, level.value
                ),
                title=meta["title"],
                slug=f"{slug_root}{_SLUG_SUFFIX[level]}",
                summary=_summary_for(parsed, level),
                quality_level=level,
                stack=stack,
                recommended=level == recommended,
                estimated_files=parsed.template.files_for(level),
                estimated_effort=meta["effort"],
                difficulty=meta["difficulty"],
                standards_profile=meta["profile"],
                rationale=f"{rationale} (fit score {score:.2f})",
                generator_actions=list(_LEVEL_ACTIONS[level]),
                validation_checks=list(_LEVEL_CHECKS[level]),
            )
        )
    return candidates


__all__ = ["generate_candidates", "base_slug"]
