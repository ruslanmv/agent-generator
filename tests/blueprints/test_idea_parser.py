"""Batch 4 — idea parser: template detection, build-type refinement, signals."""

from __future__ import annotations

from agent_generator.blueprints import parse_idea_request
from agent_generator.contracts import BuildType, IdeaConstraints, IdeaRequest


def _parse(idea: str, **kwargs):
    return parse_idea_request(IdeaRequest(idea=idea, **kwargs))


def test_detects_github_repo_intelligence() -> None:
    parsed = _parse("An AI agent that analyzes GitHub repositories and finds risky commits")
    assert parsed.template.template_id == "github-repo-intelligence-agent"
    assert parsed.matched_keywords


def test_detects_document_qa() -> None:
    parsed = _parse("A document Q&A assistant that answers questions from uploaded PDFs")
    assert parsed.template.template_id == "document-qa-agent"


def test_detects_portfolio_reviewer() -> None:
    parsed = _parse("A developer portfolio reviewer that gives feedback on my projects and resume")
    assert parsed.template.template_id == "developer-portfolio-reviewer"


def test_generic_fallback_for_unrelated_idea() -> None:
    parsed = _parse("A recipe planner for weekly family meals")
    assert parsed.template.template_id == "generic"
    assert parsed.matched_keywords == []


def test_single_weak_keyword_stays_generic() -> None:
    # One keyword hit is below MIN_KEYWORD_HITS; don't over-claim a template.
    parsed = _parse("A simple review tool for code style")
    assert parsed.template.template_id == "generic"


def test_build_type_refined_only_from_default() -> None:
    # Default APP + agent-shaped idea -> refined to AGENT.
    parsed = _parse("An AI assistant chatbot for my docs site")
    assert parsed.detected_build_type == BuildType.AGENT
    assert parsed.build_type_overridden is True

    # Explicit choice is never overridden.
    explicit = _parse("An AI assistant chatbot for my docs site", build_type=BuildType.API)
    assert explicit.detected_build_type == BuildType.API
    assert explicit.build_type_overridden is False


def test_api_detection_without_ui_signals() -> None:
    parsed = _parse("A REST API microservice that exposes a webhook endpoint")
    assert parsed.detected_build_type == BuildType.API


def test_auth_signal_detection() -> None:
    parsed = _parse("A recipe planner with user login and accounts")
    assert parsed.wants_auth is True

    via_constraints = parse_idea_request(
        IdeaRequest(
            idea="A recipe planner for weekly meals",
            constraints=IdeaConstraints(requires_auth=True),
        )
    )
    assert via_constraints.wants_auth is True
