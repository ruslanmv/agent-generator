# Architecture

## Pipeline Overview

```
User Prompt + Options
       |
       v
+-----------------------------+
|  1. Keyword Planner         |  No LLM, instant
|  Detect framework, tools,   |
|  roles, complexity           |
+-------------+---------------+
              |
              v
+-----------------------------+
|  2. LLM Planner             |  One LLM call
|  Few-shot prompt produces    |
|  structured ProjectSpec JSON |
+-------------+---------------+
              |
              v
+-----------------------------+
|  3. Spec Normalizer          |  No LLM
|  Validate references,        |
|  check capability matrix,    |
|  fix inconsistencies         |
+-------------+---------------+
              |
              v
+-----------------------------+
|  4. Template Renderer        |  No LLM, Jinja2
|  Render framework-specific   |
|  files from ProjectSpec      |
+-------------+---------------+
              |
              v
+-----------------------------+
|  5. Validation Pipeline      |  No LLM
|  AST parse, YAML check,     |
|  security scan, references   |
+-------------+---------------+
              |
              v
+-----------------------------+
|  6. Package & Output         |
|  ZIP bundle, file write,     |
|  or API response             |
+-----------------------------+
```

The LLM is used **once** (step 2). Everything else is deterministic.

## Module Map

```
src/agent_generator/
|
+-- domain/                    # Data contracts
|   +-- project_spec.py        # ProjectSpec (canonical schema)
|   +-- render_plan.py         # What files to generate
|   +-- capability_matrix.py   # Framework support matrix
|
+-- planners/                  # Planning layer
|   +-- keyword_planner.py     # Fast keyword scoring (no LLM)
|   +-- llm_planner.py         # LLM-powered spec generation
|   +-- spec_normalizer.py     # Post-LLM validation
|
+-- renderers/                 # Code generation (deterministic)
|   +-- base.py                # BaseRenderer ABC
|   +-- crewai_renderer.py     # CrewAI project (11 files)
|   +-- langgraph_renderer.py  # LangGraph project
|   +-- watsonx_renderer.py    # WatsonX YAML
|   +-- packaging.py           # ZIP bundler
|
+-- tools/                     # Tool template catalog
|   +-- registry.py            # ToolTemplate registry
|   +-- catalog/               # 6 Jinja2 tool templates
|
+-- validators/                # Quality gates
|   +-- spec_validator.py      # ProjectSpec validation
|   +-- python_validator.py    # AST + security checks
|   +-- yaml_validator.py      # YAML validation
|   +-- pipeline.py            # Orchestrates all validators
|
+-- frameworks/                # Legacy generators (still supported)
|   +-- base.py                # BaseFrameworkGenerator + registry
|   +-- crewai/                # CrewAI single-file generator
|   +-- langgraph/             # LangGraph single-file generator
|   +-- crewai_flow/           # CrewAI Flow generator
|   +-- react/                 # ReAct generator
|   +-- watsonx_orchestrate/   # WatsonX YAML generator
|
+-- providers/                 # LLM backends
|   +-- base.py                # BaseProvider + auto-registry
|   +-- watsonx_provider.py    # IBM WatsonX REST API
|   +-- openai_provider.py     # OpenAI SDK (optional)
|
+-- web/                       # Web interface
|   +-- routes/pages.py        # HTML routes (FastAPI)
|   +-- routes/api.py          # JSON API endpoints
|   +-- templates/             # Jinja2 HTML templates
|   +-- static/app.js          # Client-side JavaScript
|
+-- models/                    # Core data models
|   +-- agent.py               # Agent, Tool, LLMConfig
|   +-- task.py                # Task
|   +-- workflow.py            # Workflow, WorkflowEdge
|
+-- utils/                     # Utilities
|   +-- parser.py              # NL -> Workflow (heuristic)
|   +-- prompts.py             # LLM prompt templates
|   +-- visualizer.py          # Mermaid + Graphviz diagrams
|
+-- config.py                  # Settings (Pydantic-settings)
+-- cli.py                     # Typer CLI
+-- wsgi.py                    # ASGI entry point
```

## Key Design Decisions

**Spec-first generation:** The LLM produces a `ProjectSpec` JSON, not raw code. Renderers then produce deterministic output from the spec. Same spec = same output.

**Capability matrix:** Not all frameworks support all artifact modes. The matrix explicitly defines what's valid, rejecting unsupported combinations early.

**Auto-registration:** Providers and frameworks register themselves via `__init_subclass__()`. Adding a new one requires only subclassing -- no manual registration.

**Tool catalog:** Tools come from approved Jinja2 templates, not free-form LLM generation. This ensures generated tools are safe and functional.

**Validation pipeline:** Every artifact passes through syntax checking, security scanning, and reference validation before being returned to the user.

## Extending

### New Provider

```python
from agent_generator.providers.base import BaseProvider

class MyProvider(BaseProvider):
    name = "my_provider"
    PRICING_PER_1K = (0.001, 0.002)

    def generate(self, prompt: str, **kwargs) -> str:
        return call_my_api(prompt)
```

### New Framework

```python
from agent_generator.frameworks.base import BaseFrameworkGenerator

class MyFramework(BaseFrameworkGenerator):
    framework = "my_framework"
    file_extension = "py"

    def _emit_core_code(self, workflow, settings) -> str:
        return render_my_template(workflow)
```

### New Tool Template

Add a `.py.j2` file to `tools/catalog/` and register it in `tools/registry.py`.

---

**Next:** [Frameworks](frameworks.md) | [Installation](installation.md)
