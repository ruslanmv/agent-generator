# Production Readiness

## Current maturity

Release candidate / pre-production.

## Architecture

```
Prompt -> PlanningService -> ProjectSpec -> BuildService -> ArtifactBundle
```

All entry points (CLI, Web UI, API) use the same production pipeline.

## Required release gates

- CI green on Python 3.10, 3.11, 3.12
- pytest passing (51+ tests)
- Package build passing
- Security validation enabled (AST-based scanning)
- No generated artifact errors

## Supported frameworks

| Framework | Maturity | Output |
|-----------|----------|--------|
| CrewAI | Beta | Python + YAML |
| LangGraph | Beta | Python |
| WatsonX Orchestrate | Stable | YAML |
| CrewAI Flow | Beta | Python |
| ReAct | Beta | Python |

## Known limitations

- LLM planning enrichment is not enabled by default
- Some generators use legacy compatibility code internally
- LangGraph is the recommended primary target for production use

## Security guarantees

- AST-based scanning blocks eval(), exec(), os.system(), subprocess calls
- HTTP timeout warnings on requests without timeout parameter
- No unsafe code patterns in generated output
