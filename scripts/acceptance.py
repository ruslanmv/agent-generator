#!/usr/bin/env python3
"""Matrix Engine v1.0.0 acceptance script.

The full product promise, exercised through the public SDK with no credentials and no
network: idea -> 3 candidates -> controlled blueprint -> prompt pack -> release bundle ->
validate -> dry-run publish. Exit 0 on success.

    python scripts/acceptance.py
"""

from __future__ import annotations

import sys
import tempfile
import zipfile
from pathlib import Path

from agent_generator import AgentGenerator
from agent_generator.contracts import CoderId, Goal, IdeaRequest, QualityLevel


def run() -> int:
    engine = AgentGenerator()

    idea = IdeaRequest(
        idea="Build an AI app that analyzes GitHub repositories",
        goal=Goal.PORTFOLIO,
        quality_level=QualityLevel.STANDARD,
    )

    # 1) idea -> three candidates
    candidates = engine.generate_blueprint_candidates(idea)
    assert len(candidates) == 3, candidates
    recommended = next(c for c in candidates if c.recommended)

    # 2) controlled blueprint
    blueprint = engine.generate_controlled_blueprint(idea, candidate_id=recommended.candidate_id)
    assert blueprint.tasks, "blueprint has tasks"
    assert blueprint.slug == "github-repo-intelligence-agent", blueprint.slug

    # 3) prompt pack (every coder, contract-bound)
    pack = engine.build_prompt_pack(blueprint, bundle_id="acc")
    assert {p.coder for p in pack.prompts} == set(CoderId)
    claude = next(p for p in pack.prompts if p.coder == CoderId.CLAUDE_CODE)
    assert "MATRIX_STATUS" in claude.content and "RMD-110" in claude.content

    with tempfile.TemporaryDirectory() as d:
        # 4) release bundle (provenance + signature)
        zip_path = engine.export_zip(blueprint, Path(d) / "app.zip", release_evidence=True)
        repo = Path(d) / "repo"
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(repo)

        # 5) validate the clean output against its own contract -> approved
        report = engine.validate_ai_coder_patch("acc", repo_path=repo, blueprint=blueprint)
        assert report.status.value == "approved", [v.message for v in report.violations]
        assert report.matrixhub_publishable is True

        # 6) dry-run publish accepted
        pub = engine.prepare_matrixhub_publication(blueprint, validation_report=report)
        assert pub.accepted and pub.status == "accepted-dry-run", pub

        # 7) negative: tampering the locked contract is rejected with a repair prompt
        (repo / "MATRIX_BLUEPRINT.yaml").write_text("name: hacked\n")
        bad = engine.validate_ai_coder_patch("acc", repo_path=repo, blueprint=blueprint)
        assert bad.status.value == "rejected", bad.status
        assert bad.repair_prompt and "RMD-120" in bad.repair_prompt

    print("ACCEPTANCE OK")
    print(f"  engine={engine.info().package_version}")
    print(f"  blueprint={blueprint.slug} tasks={len(blueprint.tasks)}")
    print("  validation(clean)=approved  publish(dry-run)=accepted  validation(tampered)=rejected")
    return 0


if __name__ == "__main__":
    sys.exit(run())
