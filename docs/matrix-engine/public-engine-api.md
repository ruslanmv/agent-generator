# Public engine API (Batch 1)

`agent_generator.engine.AgentGenerator` is the stable SDK that Matrix Builder imports. It is
also exported at the package root:

```python
from agent_generator import AgentGenerator        # convenience
from agent_generator.engine import AgentGenerator  # the path Matrix Builder uses
```

## Construction

```python
engine = AgentGenerator()                       # deterministic, no credentials, no network
engine = AgentGenerator(mode="llm")             # allow LLM planning when a provider is set
engine = AgentGenerator(fixed_now=some_datetime) # pin time for snapshot/golden tests
```

The engine is deterministic by default: ids are content-addressed (`EngineRuntime.stable_id`)
and time can be pinned, so the same input yields byte-identical candidates and exports.

## The six SDK methods (cross-repo contract)

These names and return shapes are consumed by Matrix Builder's adapter in SDK mode. Do not
change them without a coordinated update there (guarded by the parity contract test).

```python
intent     = engine.parse_idea(idea_request)                       # -> IdeaIntent
candidates = engine.generate_blueprint_candidates(idea_request)    # -> list[BlueprintCandidate]
blueprint  = engine.generate_controlled_blueprint(idea_request,    # -> BlueprintResult
                                                  candidate_id=None)
bundle     = engine.generate_matrix_bundle(blueprint,              # -> MatrixBundle
                                           preferred_coder="claude-code")
prompt     = engine.generate_coder_prompt_pack(bundle.bundle_id,   # -> PromptResponse
                                              "claude-code")
report     = engine.validate_ai_coder_patch(bundle_id=bundle.bundle_id)  # -> ValidationReport
```

`parse_idea` and the other entry points accept the engine's own `IdeaRequest`, a plain
`dict`, or any structurally-compatible object (e.g. Matrix Builder's `IdeaRequest`) — the
last is coerced via Pydantic `from_attributes`.

## Additive helpers

```python
pack   = engine.build_prompt_pack(blueprint)            # -> PromptPack (all coders)
repair = engine.generate_repair_prompt(report)          # -> str | None
zip_   = engine.export_zip(blueprint, "out/app.zip")    # -> Path (deterministic archive)
status = engine.status()                                # adapter-shaped status dict
info   = engine.info()                                  # EngineInfo: version, frameworks, capabilities
```

## What is real vs. stubbed in this batch

- **Real:** idea normalization, three quality-tiered candidates, controlled-blueprint tasks
  derived from the **keyword planner**, deterministic Matrix Bundle metadata, controlled
  prompt rendering, a minimal-but-real forbidden-file validation check, and a
  byte-deterministic ZIP export.
- **Deepened later:** signed `MATRIX_STANDARDS.lock` (Batch 3), full controlled compiler
  (Batch 5), SBOM/attestation in exports (Batch 6/10), per-coder adapters (Batch 7), full
  drift detection (Batch 8). None of these change the method signatures above.

## Validation behavior

`validate_ai_coder_patch` returns `not-run` when given no changed files. Supply a
`ValidationRequest` (or any object with `changed_files`) and it performs a real
filesystem-policy check: modifying a forbidden contract file (`MATRIX_BLUEPRINT.yaml`,
`MATRIX_STANDARDS.lock`, `.github/workflows/`) yields a `rejected` report plus a
task-scoped repair prompt; otherwise `approved`.
