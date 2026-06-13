# Shared Matrix contracts (Batch 2)

`agent_generator.contracts` is the single source of truth for the data shapes exchanged
across the Matrix boundary. Import public contracts from the package root:

```python
from agent_generator.contracts import IdeaRequest, BlueprintResult, MatrixBundle, ...
```

## Two shapes, kept in agreement

Each contract carries the **Matrix Builder API shape** (what Matrix Builder returns to its
clients) and, where relevant, a `to_definitions_dict()` projection onto the **canonical
signed-standard shape** owned by matrix-definitions. Keeping both in one model is what lets
the cross-repo tests prove they never drift apart.

| Contract | API shape mirrors | Canonical projection validates against |
|---|---|---|
| `IdeaRequest` / `IdeaIntent` | `app.schemas.idea` | — |
| `BlueprintCandidate` | `app.schemas.blueprint` | `blueprint-candidate.schema.json` |
| `BlueprintResult` (`BlueprintSpec`) | `app.schemas.blueprint` | `matrix-blueprint.schema.json` |
| `MatrixBundle` / `BundleManifest` | `app.schemas.bundle` | — |
| `PromptResponse` / `PromptPack` | `app.schemas.prompt` | — |
| `ValidationReport` | `app.schemas.validation` | `validation-report.schema.json` |
| `StandardsLock` | — | `matrix-standards-lock.schema.json` |

## Enum wire values are the contract

Enums use `str`-mixed `Enum` (3.10-compatible) with the exact wire values Matrix Builder
uses. Note the API-vs-canonical status difference, handled by `API_TO_DEFINITIONS_STATUS`:

- API (`ValidationStatus`): `not-run`, `approved`, `needs-repair`, `rejected` (hyphens).
- Canonical (matrix-definitions): `draft`, `approved`, `needs_repair`, `rejected` (underscores).

## Back-compat with `ProjectSpec`

The engine reuses the proven keyword planner, which speaks the legacy `ProjectSpec`.
`agent_generator.contracts.projectspec_adapter` is the only bridge:

```python
from agent_generator.contracts.projectspec_adapter import (
    idea_to_project_spec,    # IdeaRequest  -> (ProjectSpec, warnings)
    project_spec_to_stack,   # ProjectSpec  -> BlueprintStack
    project_spec_to_tasks,   # ProjectSpec  -> list[BlueprintTask]  (TASK-NNN ids)
)
```

## Architecture-named import paths

For alignment with the architecture documents, the blueprint and artifact models are also
exposed at:

- `agent_generator.blueprints.models` → `BlueprintSpec`, `BlueprintCandidate`, `TaskSpec`, …
- `agent_generator.artifacts.models` → `ArtifactManifest`, `ArtifactEntry`

## Versioning

`agent_generator.contracts.CONTRACTS_VERSION` (currently `1.0`) tracks the shared shapes.
Bump it on any breaking change and re-sync the vendored schemas under
`tests/contracts/schemas/`.
