# Matrix engine quickstart

agent-generator is the deterministic engine behind **Matrix Builder**. It turns an idea into a
controlled contract an AI coder follows, then validates the result.

## Install

```bash
pip install agent-generator            # engine + CLI
pip install 'agent-generator[web]'     # + HTTP facade (FastAPI)
```

## Python SDK

```python
from agent_generator import AgentGenerator
from agent_generator.contracts import IdeaRequest

engine = AgentGenerator()                                   # deterministic, no credentials

idea = IdeaRequest(idea="An AI app that analyzes GitHub repositories")
candidates = engine.generate_blueprint_candidates(idea)     # 3 quality-tiered options
blueprint  = engine.generate_controlled_blueprint(idea)     # the locked contract

pack = engine.build_prompt_pack(blueprint, bundle_id="b1")  # one prompt per AI coder
engine.export_zip(blueprint, "dist/app.zip", release_evidence=True)  # signed release bundle

# After your AI coder runs, validate its output against the contract:
report = engine.validate_ai_coder_patch("b1", repo_path="dist/out", blueprint=blueprint)
print(report.status)        # approved | needs-repair | rejected
print(report.repair_prompt) # bounded fix instructions when not approved
```

## CLI

```bash
agent-generator matrix candidates --idea "An AI app that analyzes GitHub repositories"
agent-generator matrix generate   --idea "..." --out dist/app
agent-generator matrix export      --idea "..." --out dist/app.zip --release-evidence
agent-generator matrix validate    --idea "..." --repo dist/app    # exit 0/1/2
```

## HTTP

```bash
uvicorn agent_generator.http.app:app          # OpenAPI at /openapi.json
```

```
POST /api/v1/ideas/parse · /blueprints/candidates · /blueprints · /blueprints/regenerate
     /bundles · /prompts · /validations · /exports        GET /api/v1/standards/current
```

## Verify a bundle

Every bundle ships a `checksums.txt`; release bundles add provenance and a cosign bundle:

```bash
cd dist/out && sha256sum -c artifacts/checksums.txt
```

See also: [public-engine-api](public-engine-api.md), [validation-and-repair](validation-and-repair.md),
[ruslan-magana-definitions](ruslan-magana-definitions.md).
