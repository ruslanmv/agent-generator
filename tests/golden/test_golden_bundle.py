"""Batch 5 — golden snapshot of a fully compiled bundle.

Locks the exact rendered file plan for a flagship template so any unintended change to the
compiler, control files, scaffold, prompts, or standards lock is caught in review. The
snapshot is byte-stable because the engine is deterministic (pinned clock + pinned pack).

To refresh after an intentional change:  UPDATE_GOLDEN=1 pytest tests/golden -q
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from agent_generator.contracts import IdeaRequest
from agent_generator.engine import AgentGenerator

FIXED_NOW = datetime(2026, 6, 12, 14, 0, 0, tzinfo=timezone.utc)
GOLDEN = Path(__file__).parent / "github-repo-intelligence-agent.golden.json"
IDEA = IdeaRequest(idea="An AI agent that analyzes GitHub repositories for risks")


def _compile_snapshot() -> dict:
    engine = AgentGenerator(fixed_now=FIXED_NOW)
    compiled = engine.compile_bundle(engine.generate_controlled_blueprint(IDEA))
    return {
        "contract_hash": compiled.contract_hash,
        "immutable_files": list(compiled.immutable_files),
        "files": compiled.file_map(),
    }


def test_compiled_bundle_matches_golden() -> None:
    snapshot = _compile_snapshot()

    if os.environ.get("UPDATE_GOLDEN") == "1":
        GOLDEN.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n")
        return

    assert GOLDEN.exists(), "golden snapshot missing; run UPDATE_GOLDEN=1 pytest tests/golden"
    expected = json.loads(GOLDEN.read_text())

    assert snapshot["contract_hash"] == expected["contract_hash"]
    assert snapshot["immutable_files"] == expected["immutable_files"]
    # Compare the file set first for a clear diff, then exact content.
    assert set(snapshot["files"]) == set(expected["files"])
    for path, content in expected["files"].items():
        assert snapshot["files"][path] == content, f"content drift in {path}"
