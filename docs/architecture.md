# How it works

One LLM call. Everything else is deterministic. That's the whole idea.

## The pipeline

```
Your prompt
    │
    ▼
1. Keyword planner    ← no LLM. Detects framework, tools, roles, complexity.
    │
    ▼
2. LLM planner        ← one LLM call. Produces a ProjectSpec JSON.
    │
    ▼
3. Spec normaliser    ← no LLM. Validates references, fixes inconsistencies.
    │
    ▼
4. Template renderer  ← no LLM. Jinja2 → files.
    │
    ▼
5. Validation         ← no LLM. AST + YAML + security + reference checks.
    │
    ▼
6. Output             ← ZIP, file, or API response.
```

Same prompt → same `ProjectSpec` → same files. Re-runs are byte-identical.

## Why a spec, not raw code

The LLM hands back a structured `ProjectSpec` — agents, tasks, tools,
LLM config, framework, artifact mode. Renderers turn that spec into
files through templates. No raw code ever crosses the LLM boundary.

That's how we keep three things true at once:

1. **Reproducibility.** Same spec, same output.
2. **Safety.** No model-emitted code reaches your disk.
3. **Auditability.** The spec is small, human-readable, and stored.

## What lives where

```
src/agent_generator/
├── domain/         data contracts (ProjectSpec, RenderPlan, capability matrix)
├── planners/       keyword planner · LLM planner · spec normaliser
├── renderers/      per-framework renderers + the ZIP packager
├── tools/          tool template catalogue (Jinja2)
├── validators/     AST · YAML · security · spec · reference checks
├── frameworks/     legacy single-file generators (still supported)
├── providers/      WatsonX · OpenAI (auto-registered subclasses)
├── web/            FastAPI routes + templates + static
├── models/         core domain models (Agent, Task, Workflow)
├── utils/          parser, prompt templates, visualiser
├── config.py       Pydantic-settings
├── cli.py          Typer CLI
└── wsgi.py         ASGI entrypoint
```

## Decisions that matter

**Spec-first.** Every entry point — CLI, web, API — funnels through
`PlanningService → ProjectSpec → BuildService → ArtifactBundle`. One
production pipeline, three faces.

**Capability matrix.** Not every framework supports every artifact mode.
The matrix in `domain/capability_matrix.py` rejects bad combinations
early instead of letting the LLM guess.

**Auto-registration.** Providers and frameworks register themselves via
`__init_subclass__`. Adding a new one means subclassing — no manual
plumbing.

**Tool catalogue, not free-form tools.** Tools come from approved
templates in `tools/catalog/`. That's how generated agents end up with
working, safe tools every time.

## Extending it

### Add a provider

```python
from agent_generator.providers.base import BaseProvider

class MyProvider(BaseProvider):
    name = "my_provider"
    PRICING_PER_1K = (0.001, 0.002)

    def generate(self, prompt: str, **kwargs) -> str:
        return call_my_api(prompt)
```

### Add a framework

```python
from agent_generator.frameworks.base import BaseFrameworkGenerator

class MyFramework(BaseFrameworkGenerator):
    framework = "my_framework"
    file_extension = "py"

    def _emit_core_code(self, workflow, settings) -> str:
        return render_my_template(workflow)
```

### Add a tool template

Drop a `.py.j2` into `tools/catalog/` and register it in
`tools/registry.py`. The wizard, the planner, and the renderers all
pick it up.

---

**Next:** [Platform overview](platform.md) · [Production readiness](production-readiness.md)
