#!/usr/bin/env python3
"""Fast smoke check that the Matrix engine boundary is intact.

Runnable locally or in CI as a cheap gate before the full test suite. Verifies that the
public ``AgentGenerator`` facade imports, exposes the six methods Matrix Builder's adapter
depends on, and can complete one deterministic idea -> candidates -> blueprint -> bundle ->
prompt -> validate -> export round-trip.

Exit code 0 on success, 1 on any failure.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

# The exact method names Matrix Builder's agent_generator_adapter.py probes for in SDK mode.
REQUIRED_METHODS = (
    "parse_idea",
    "generate_blueprint_candidates",
    "generate_controlled_blueprint",
    "generate_matrix_bundle",
    "generate_coder_prompt_pack",
    "validate_ai_coder_patch",
)


def _fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def main() -> int:
    try:
        from agent_generator import AgentGenerator
        from agent_generator.contracts import IdeaRequest
    except Exception as exc:  # noqa: BLE001
        _fail(f"engine import failed: {exc}")

    engine = AgentGenerator()

    for method in REQUIRED_METHODS:
        if not callable(getattr(engine, method, None)):
            _fail(f"missing required SDK method: {method}")

    idea = IdeaRequest(idea="Build an AI app that analyzes GitHub repositories")
    candidates = engine.generate_blueprint_candidates(idea)
    if len(candidates) != 3:
        _fail(f"expected 3 candidates, got {len(candidates)}")

    blueprint = engine.generate_controlled_blueprint(idea)
    if not blueprint.tasks:
        _fail("blueprint produced no tasks (planner wiring broken)")

    bundle = engine.generate_matrix_bundle(blueprint)
    prompt = engine.generate_coder_prompt_pack(bundle.bundle_id, "claude-code", blueprint=blueprint)
    if "MATRIX_BLUEPRINT.yaml" not in prompt.contract_files:
        _fail("prompt missing contract files")

    report = engine.validate_ai_coder_patch(bundle_id=bundle.bundle_id)
    if report.status.value != "not-run":
        _fail(f"empty validation should be not-run, got {report.status}")

    with tempfile.TemporaryDirectory() as tmp:
        out = engine.export_zip(blueprint, Path(tmp) / "bundle.zip")
        if not out.exists() or out.stat().st_size == 0:
            _fail("export_zip produced no archive")

    print("OK: Matrix engine baseline check passed")
    print(f"  package_version={engine.info().package_version}")
    print(f"  frameworks={','.join(engine.info().frameworks)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
