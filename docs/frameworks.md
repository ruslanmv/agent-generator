# Pick a framework

Not sure which one to choose? Use this table.

| If you want… | Pick | Output | Best for |
|---|---|---|---|
| Multiple cooperating roles, prod-grade scaffolding | **CrewAI** | Python + YAML | Most teams. Familiar Python project layout. |
| Explicit state and graph control | **LangGraph** | Python | Pipelines, long-running flows, conditional routing. |
| To deploy inside IBM watsonx Orchestrate | **WatsonX Orchestrate** | YAML | Enterprise IBM stacks. |
| Event-driven mini-crews | **CrewAI Flow** | Python | Multi-step pipelines with branching. |
| A single-file reasoning loop | **ReAct** | Python | Tool-calling agents, demos, embedded use. |

## CrewAI

Generates a complete project:

```
project/
  config/
    agents.yaml     # role, goal, backstory
    tasks.yaml      # description, expected_output, agent
  src/
    crew.py         # @CrewBase with @agent, @task, @crew
    main.py
    tools/          # tools picked from the catalogue
  tests/test_smoke.py
  pyproject.toml    # crewai>=1.12
  README.md  .env.example  .gitignore
```

```bash
agent-generator "Research team with a researcher and a writer" \
  -f crewai -o team/
```

Modes: `code_only`, `yaml_only`, `code_and_yaml`.

## LangGraph

A single `graph.py` with:

- `TypedDict` state schema
- one node function per task
- edges from task dependencies
- a `START` entry point
- `graph.compile()` + `app.invoke()`

```bash
agent-generator "Extract, transform, load pipeline" \
  -f langgraph -o pipeline.py
```

Mode: `code_only`.

## WatsonX Orchestrate

Emits the ADK YAML:

```yaml
spec_version: v1
kind: native
name: agent-name
description: What the agent does
instructions: |
  Detailed instructions from task goals
llm: watsonx/meta-llama/llama-3-3-70b-instruct
tools: [tool_name]
knowledge_base: []
```

```bash
agent-generator "Customer support assistant" \
  -f watsonx_orchestrate -o support.yaml
orchestrate agents import -f support.yaml
```

Mode: `yaml_only`.

## CrewAI Flow

Single Python file with:

- `FlowState` (Pydantic) for shared state
- `WorkflowFlow(Flow[FlowState])`
- `@start()` and `@listen()` decorators
- Each step spawns a mini-Crew

```bash
agent-generator "Content pipeline: research, write, edit" \
  -f crewai_flow -o content.py
```

Mode: `code_only`.

## ReAct

Single file with:

- Tool registry via `@register_tool`
- `think()` / `act()` functions
- `react_loop()` with a `MAX_ITERATIONS` guard
- Per-task runners; built-in `search` and `calculate`

```bash
agent-generator "Code review bot" -f react -o reviewer.py
```

Mode: `code_only`.

## Capability matrix

| Feature | CrewAI | LangGraph | WatsonX | Flow | ReAct |
|---|---|---|---|---|---|
| Code output | ✓ | ✓ |  | ✓ | ✓ |
| YAML output | ✓ |  | ✓ |  |  |
| Code + YAML | ✓ |  |  |  |  |
| Tool templates | ✓ | ✓ |  | ✓ | ✓ |
| MCP wrapper | ✓ | ✓ |  | ✓ | ✓ |

---

**Next:** [Architecture](architecture.md) · [Platform overview](platform.md)
