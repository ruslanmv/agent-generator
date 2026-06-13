# Matrix engine HTTP facade (Batch 9)

`agent_generator.http` is a thin, **stateless** FastAPI app over the SDK. Each endpoint is a
direct wrapper around an `AgentGenerator` method. Matrix Builder can call the engine over HTTP
when it doesn't want the in-process SDK; the engine holds no state, so Matrix Builder remains
the system of record for bundles and versions.

```bash
uvicorn agent_generator.http.app:app          # standalone
# or, inside another FastAPI app:
backend.mount("/engine", agent_generator.http.create_app())
```

FastAPI is the optional `web` extra (`pip install 'agent-generator[web]'`); importing
`agent_generator` itself never requires it.

## Endpoints

| Method | Path | Wraps | Body → Response |
|---|---|---|---|
| GET | `/health` | `status()` | — |
| GET | `/api/v1/standards/current` | `standards_metadata()` | pack metadata |
| POST | `/api/v1/ideas/parse` | `parse_idea` | `IdeaRequest` → `IdeaIntent` |
| POST | `/api/v1/blueprints/candidates` | `generate_blueprint_candidates` | `IdeaRequest` → candidates |
| POST | `/api/v1/blueprints` | `generate_controlled_blueprint` | `{idea_request, candidate_id?}` → `BlueprintResult` |
| POST | `/api/v1/blueprints/regenerate` | `regenerate` | `{base_blueprint, change_request, change_type, current_version}` → `RegenerationResult` |
| POST | `/api/v1/bundles` | `generate_matrix_bundle` | `{blueprint, preferred_coder}` → `MatrixBundle` |
| POST | `/api/v1/prompts` | `generate_coder_prompt_pack` | `{blueprint, coder, bundle_id}` → `PromptResponse` |
| POST | `/api/v1/validations` | `validate_ai_coder_patch` | `{blueprint?, request?, patch?}` → `ValidationReport` |
| POST | `/api/v1/exports` | `compile_bundle` | `{blueprint, version}` → `application/zip` |

`/api/v1/exports` streams a byte-deterministic ZIP and returns the bundle's contract hash in
the `X-Matrix-Contract-Hash` header. OpenAPI is served at `/openapi.json`.

## Versioning over the wire

`POST /api/v1/blueprints/regenerate` is the engine half of Matrix Builder's "Update
requirements" flow. Matrix Builder's `POST /bundles/{id}/versions` calls it, stores the
returned blueprint as a new version row, leaves the old one untouched, and applies the
version-conflict guard ("you're editing v1.0.0 but v1.2.0 is current"). The engine is the pure
function; Matrix Builder owns the version table.
