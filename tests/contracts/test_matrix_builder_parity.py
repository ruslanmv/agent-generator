"""Cross-repo parity test: engine contracts match Matrix Builder's API schemas.

In SDK mode Matrix Builder returns the engine's objects directly as its own Pydantic
response models, so the field names and enum wire-values must match exactly. This test
imports Matrix Builder's ``app.schemas`` when its source is resolvable and asserts parity.
It skips (rather than fails) when Matrix Builder is not checked out alongside this repo, so
agent-generator CI stays self-contained — but in the combined workspace it runs and guards
against silent drift.

Resolution order for the Matrix Builder API source root (the dir containing ``app/``):
1. ``MATRIX_BUILDER_API_DIR`` environment variable
2. sibling checkout ``../matrix-builder/services/api``
"""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import pytest

import agent_generator.contracts as agc


def _resolve_api_dir() -> Path | None:
    env = os.environ.get("MATRIX_BUILDER_API_DIR")
    candidates = [Path(env)] if env else []
    candidates.append(Path(__file__).resolve().parents[3] / "matrix-builder" / "services" / "api")
    for path in candidates:
        if (path / "app" / "schemas" / "common.py").exists():
            return path
    return None


_API_DIR = _resolve_api_dir()
if _API_DIR is None:
    pytest.skip("matrix-builder source not available", allow_module_level=True)

if str(_API_DIR) not in sys.path:
    sys.path.insert(0, str(_API_DIR))

mb_common = importlib.import_module("app.schemas.common")
mb_idea = importlib.import_module("app.schemas.idea")
mb_blueprint = importlib.import_module("app.schemas.blueprint")
mb_bundle = importlib.import_module("app.schemas.bundle")
mb_prompt = importlib.import_module("app.schemas.prompt")
mb_validation = importlib.import_module("app.schemas.validation")


def _values(enum_cls) -> set[str]:
    return {member.value for member in enum_cls}


@pytest.mark.parametrize(
    "name",
    ["BuildType", "Goal", "QualityLevel", "CoderId", "ValidationStatus", "BundleStatus"],
)
def test_enum_wire_values_match(name: str) -> None:
    ours = getattr(agc, name)
    theirs = getattr(mb_common, name)
    assert _values(ours) == _values(theirs), f"{name} enum drift"


def _fields(model) -> set[str]:
    return set(model.model_fields.keys())


@pytest.mark.parametrize(
    ("ours", "theirs"),
    [
        (agc.IdeaRequest, "mb_idea.IdeaRequest"),
        (agc.IdeaIntent, "mb_idea.IdeaIntent"),
        (agc.BlueprintCandidate, "mb_blueprint.BlueprintCandidate"),
        (agc.BlueprintResult, "mb_blueprint.BlueprintResult"),
        (agc.BlueprintStack, "mb_blueprint.BlueprintStack"),
        (agc.BlueprintTask, "mb_blueprint.BlueprintTask"),
        (agc.MatrixBundle, "mb_bundle.MatrixBundle"),
        (agc.PromptResponse, "mb_prompt.PromptResponse"),
        (agc.ValidationReport, "mb_validation.ValidationReport"),
    ],
)
def test_model_field_names_match(ours, theirs: str) -> None:
    module_name, attr = theirs.split(".")
    module = {
        "mb_idea": mb_idea,
        "mb_blueprint": mb_blueprint,
        "mb_bundle": mb_bundle,
        "mb_prompt": mb_prompt,
        "mb_validation": mb_validation,
    }[module_name]
    their_model = getattr(module, attr)
    assert _fields(ours) == _fields(their_model), f"field drift in {attr}"
