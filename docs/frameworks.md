# Supported Frameworks

## CrewAI

**Versions:** crewai 1.12+

**Artifact modes:** `code_only`, `yaml_only`, `code_and_yaml`

**What it generates (code_and_yaml mode):**

```
project/
  config/
    agents.yaml     # Agent role, goal, backstory
    tasks.yaml      # Task description, expected_output, agent
  src/
    crew.py         # @CrewBase class with @agent, @task, @crew
    main.py         # Entry point
    tools/          # Tool implementations from catalog
  tests/
    test_smoke.py   # Basic import/instantiation test
  pyproject.toml    # With crewai==1.12.2 dependency
  README.md
  .env.example
  .gitignore
```

**CLI example:**

```bash
agent-generator "Research team with researcher and writer" \
  --framework crewai --output team.py
```

---

## LangGraph

**Versions:** langgraph 1.1+

**Artifact modes:** `code_only`

**What it generates:**

- `StateGraph` with `TypedDict` state schema
- One node function per task
- Edges from task dependencies
- `START` constant for entry point
- `graph.compile()` and `app.invoke()` pattern

**CLI example:**

```bash
agent-generator "Data pipeline: extract, transform, load" \
  --framework langgraph --output pipeline.py
```

---

## WatsonX Orchestrate

**Versions:** ADK spec_version v1

**Artifact modes:** `yaml_only`

**What it generates:**

```yaml
spec_version: v1
kind: native
name: agent-name
description: What the agent does
instructions: |
  Detailed instructions from task goals
llm: watsonx/meta-llama/llama-3-3-70b-instruct
tools:
  - tool_name
knowledge_base: []
```

**CLI example:**

```bash
agent-generator "Customer support assistant" \
  --framework watsonx_orchestrate --output support.yaml
```

**Import:**

```bash
orchestrate agents import -f support.yaml
```

---

## CrewAI Flow

**Versions:** crewai 1.12+ (Flow API)

**Artifact modes:** `code_only`

**What it generates:**

- `FlowState` Pydantic model for shared state
- `WorkflowFlow(Flow[FlowState])` class
- `@start()` decorator for entry step
- `@listen()` decorators for subsequent steps
- Each step creates a mini-Crew for its task

**CLI example:**

```bash
agent-generator "Content pipeline: research, write, edit" \
  --framework crewai_flow --output content.py
```

---

## ReAct

**Artifact modes:** `code_only`

**What it generates:**

- Tool registry with `@register_tool` decorator
- `think()` and `act()` functions
- `react_loop()` with `MAX_ITERATIONS` guard
- Per-task runner functions
- Built-in `search` and `calculate` tools

**CLI example:**

```bash
agent-generator "Code review bot" \
  --framework react --output reviewer.py
```

---

## Capability Matrix

| Feature | CrewAI | LangGraph | WatsonX | CrewAI Flow | ReAct |
|---------|--------|-----------|---------|-------------|-------|
| Code output | Yes | Yes | No | Yes | Yes |
| YAML output | Yes | No | Yes | No | No |
| Code + YAML | Yes | No | No | No | No |
| Tool templates | Yes | Yes | No | Yes | Yes |
| MCP wrapper | Yes | Yes | No | Yes | Yes |

---

**Next:** [Architecture](architecture.md) | [Installation](installation.md)
