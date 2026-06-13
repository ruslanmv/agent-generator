"""Canary (positive): the three flagship templates generate and validate clean."""

from __future__ import annotations

import zipfile
from datetime import datetime, timezone

import pytest

from agent_generator.contracts import IdeaRequest, ValidationStatus
from agent_generator.engine import AgentGenerator

FIXED_NOW = datetime(2026, 6, 12, 14, 0, 0, tzinfo=timezone.utc)

FLAGSHIPS = {
    "github-repo-intelligence-agent": "An AI agent that analyzes GitHub repositories for risks",
    "document-qa-agent": "A document Q&A assistant that answers questions from uploaded PDFs",
    "developer-portfolio-reviewer": "A developer portfolio reviewer that gives feedback on projects and resume",
}


@pytest.fixture()
def engine() -> AgentGenerator:
    return AgentGenerator(fixed_now=FIXED_NOW)


@pytest.mark.parametrize(("slug", "idea_text"), list(FLAGSHIPS.items()))
def test_flagship_generates_and_validates(
    engine: AgentGenerator, slug: str, idea_text: str, tmp_path
) -> None:
    idea = IdeaRequest(idea=idea_text)
    blueprint = engine.generate_controlled_blueprint(idea)
    assert blueprint.slug == slug
    assert blueprint.tasks

    # Export, extract, and validate the bundle against its own blueprint -> approved.
    zip_path = engine.export_zip(blueprint, tmp_path / f"{slug}.zip")
    repo = tmp_path / slug
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(repo)
    report = engine.validate_ai_coder_patch(slug, repo_path=repo, blueprint=blueprint)
    assert report.status == ValidationStatus.APPROVED, [v.message for v in report.violations]
    assert report.matrixhub_publishable is True


@pytest.mark.parametrize(("slug", "idea_text"), list(FLAGSHIPS.items()))
def test_flagship_prompt_pack_is_complete(
    engine: AgentGenerator, slug: str, idea_text: str
) -> None:
    blueprint = engine.generate_controlled_blueprint(IdeaRequest(idea=idea_text))
    pack = engine.build_prompt_pack(blueprint, bundle_id="b")
    assert len(pack.prompts) == 6
    for prompt in pack.prompts:
        assert "MATRIX_STATUS" in prompt.content
