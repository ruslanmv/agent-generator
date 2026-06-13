"""Idea parsing (Batch 4) — turn raw idea text into structured, deterministic intent.

The parser never uses an LLM: detection is keyword-based and reproducible. Its output is an
internal ``ParsedIdea`` enriched with the detected template family, build type, and signals;
the public contract ``IdeaIntent`` is projected from it by the engine.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from agent_generator.blueprints.templates import TemplateFamily, detect_template
from agent_generator.contracts.common import BuildType
from agent_generator.contracts.idea import IdeaRequest

_AGENT_SIGNALS = re.compile(
    r"\b(agent|assistant|bot|chatbot|copilot|crew|multi-agent|llm|rag)\b", re.IGNORECASE
)
_API_SIGNALS = re.compile(
    r"\b(api|endpoint|microservice|rest|graphql|webhook|backend service)\b", re.IGNORECASE
)
_UI_SIGNALS = re.compile(r"\b(page|dashboard|frontend|ui|website|web app|landing)\b", re.IGNORECASE)
_AUTH_SIGNALS = re.compile(
    r"\b(auth|authentication|login|sign[- ]?in|sign[- ]?up|account|user management)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ParsedIdea:
    """Structured, deterministic interpretation of a raw idea."""

    normalized_idea: str
    template: TemplateFamily
    matched_keywords: list[str] = field(default_factory=list)
    detected_build_type: BuildType = BuildType.APP
    build_type_overridden: bool = False
    wants_auth: bool = False
    signals: list[str] = field(default_factory=list)


def _normalize(value: str) -> str:
    return " ".join(value.strip().split())


def _detect_build_type(text: str, template: TemplateFamily) -> BuildType:
    if template.template_id != "generic":
        return template.build_type
    if _AGENT_SIGNALS.search(text):
        return BuildType.AGENT
    if _API_SIGNALS.search(text) and not _UI_SIGNALS.search(text):
        return BuildType.API
    return BuildType.APP


def parse_idea_request(request: IdeaRequest) -> ParsedIdea:
    """Parse an ``IdeaRequest`` into a ``ParsedIdea``.

    The user's explicit ``build_type`` wins; detection only refines the default (``app``),
    so an intentional choice is never silently overridden.
    """
    normalized = _normalize(request.idea)
    template, hits = detect_template(normalized)

    detected = _detect_build_type(normalized, template)
    overridden = request.build_type == BuildType.APP and detected != BuildType.APP
    effective = detected if overridden else request.build_type

    signals: list[str] = []
    if _AGENT_SIGNALS.search(normalized):
        signals.append("agent")
    if _API_SIGNALS.search(normalized):
        signals.append("api")
    if _UI_SIGNALS.search(normalized):
        signals.append("ui")
    wants_auth = bool(_AUTH_SIGNALS.search(normalized)) or request.constraints.requires_auth
    if wants_auth:
        signals.append("auth")

    return ParsedIdea(
        normalized_idea=normalized,
        template=template,
        matched_keywords=hits,
        detected_build_type=effective,
        build_type_overridden=overridden,
        wants_auth=wants_auth,
        signals=signals,
    )


__all__ = ["ParsedIdea", "parse_idea_request"]
