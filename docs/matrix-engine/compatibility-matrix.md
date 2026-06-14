# Matrix ecosystem compatibility matrix

The guiding separation of concerns:

```
matrix-builder   does orchestration.
agent-generator  does generation.          <- this repo (the engine)
matrix-definitions provides rules.
MatrixHub        publishes trusted artifacts.
ruslanmv.com     explains the standard.
```

## Version state

| Component | Version (observed) | Notes |
|---|---|---|
| agent-generator (package) | `0.2.0` | The Matrix engine release: `AgentGenerator` SDK, the `mb` local-first CLI, batch planning, commit snapshots/diffs, tool-native handoffs (CLAUDE.md/AGENTS.md). Satisfies matrix-definitions `>=0.2.0` (verified `standards_metadata()["compatibility"]["ok"] == True`). Supersedes PyPI `0.1.2` |
| agent-generator engine API | `1` | `ENGINE_API_VERSION`; the six SDK methods are stable |
| shared contracts | `1.0` | `agent_generator.contracts.CONTRACTS_VERSION` |
| matrix-builder | `0.9.0-batch.9` | Adapter imports `agent_generator.engine.AgentGenerator`. To use the real engine it must depend on `agent-generator>=0.2.0` and set `AGENT_GENERATOR_MODE=sdk`; otherwise the adapter stays in `mock` |
| matrix-definitions | `2026.06.0` | Declares `compatibility.agent_generator >= 0.2.0` |

## The 0.2.0 milestone (reached in Batch 3)

matrix-definitions requires `agent_generator >= 0.2.0`. The bump was deliberately tied to the
standards loader, because `0.2.0` should mean "can load and verify a signed standards pack",
not merely "has an engine module". As of Batch 3 the engine is `0.2.0`, the bundled pack
`2026.06.0` is loaded and checksum-verified, and `engine.standards_metadata()["compatibility"]["ok"]`
is `True`. Matrix Builder can set `AGENT_GENERATOR_MODE=sdk`.

## SDK method contract (must not drift)

Matrix Builder's `services/api/app/integrations/agent_generator_adapter.py` probes for and
calls these exact methods in SDK mode. They are guarded by
`tests/contracts/test_matrix_builder_parity.py`.

| Engine method | Returns | Adapter call site |
|---|---|---|
| `parse_idea(payload)` | `IdeaIntent` | `parse_idea` |
| `generate_blueprint_candidates(payload)` | `list[BlueprintCandidate]` | `generate_blueprint_candidates` |
| `generate_controlled_blueprint(payload, candidate_id=None)` | `BlueprintResult` | `generate_controlled_blueprint` |
| `generate_matrix_bundle(blueprint, preferred_coder=...)` | `MatrixBundle` | `generate_matrix_bundle` |
| `generate_coder_prompt_pack(bundle_id, coder)` | `PromptResponse` | `generate_coder_prompt` |
| `validate_ai_coder_patch(bundle_id=...)` | `ValidationReport` | `validate_bundle` |

The adapter *probes the engine for* `generate_coder_prompt_pack` and `validate_ai_coder_patch`
(its own public method names are `generate_coder_prompt` / `validate_bundle`). The engine
exposes **both** names as aliases, so either can be called directly.

## Cross-repo contract tests

| Test | Guards | Skips when |
|---|---|---|
| `tests/contracts/test_matrix_builder_parity.py` | Enum wire-values + model field names match Matrix Builder | matrix-builder not checked out (`MATRIX_BUILDER_API_DIR` overrides) |
| `tests/contracts/test_matrix_definitions_schema.py` | Canonical projections validate against matrix-definitions JSON Schemas | never (schemas vendored; `MATRIX_DEFINITIONS_DIR` overrides) |
