# Architecture of agent‑generator

This document describes the overall architecture of **agent‑generator**, with a focus on the generative pipeline that transforms plain‑English prompts into fully configured agent code or YAML for various frameworks, and on the BeeAI multi‑agent backend used for planning and building.

---

## 1. High‑Level Overview

1. **User Input (CLI or Web UI)**  
   The user provides a natural‑language requirement, selects a framework, and optionally a provider, model, and other flags.
2. **Env Loader**  
   `.env` variables are loaded into the process environment.
3. **Pre‑flight Check**  
   Credentials for the chosen provider (WatsonX or OpenAI) are validated; helpful messages printed if missing.
4. **Settings Loader**  
   Pydantic reads environment variables and `.env` to build a `Settings` object, applying defaults and provider‑specific overrides.
5. **Parser**  
   The natural‑language prompt is parsed into a **Workflow** graph: a set of `Agent`, `Task`, and `Edge` objects.
6. **Prompt Renderer**  
   A Jinja template combines the workflow, settings, and framework instructions into a single text prompt for the LLM.
7. **LLM Provider**  
   The prompt is sent to the selected LLM (WatsonX REST API or OpenAI SDK). The raw completion is returned.
8. **Framework Generator**  
   Static Jinja templates consume the `Workflow` graph to produce code or YAML in the target framework’s syntax, optionally using the LLM response for detail.
9. **Output**  
   The generated code/YAML is printed with syntax highlighting or written to a file. Token and cost estimates are displayed if requested.

---

## 2. Component Breakdown

### 2.1 CLI / Web UI

- **`src/agent_generator/cli.py`**  
  Typer‑based CLI; zero‑flag wizard + `create` command.
- **`src/agent_generator/web/`**  
  Flask UI for browser‑based interaction.

### 2.2 Configuration & Environment

- **`src/agent_generator/config.py`**  
  Defines `Settings`; loads from `.env` or environment.
- **`.env` support**  
  Loaded at startup for local overrides.

### 2.3 Parser & Workflow Model

- **`src/agent_generator/utils/parser.py`**  
  Converts English into a structured `Workflow` (agents, tasks).

### 2.4 Prompt Rendering

- **`src/agent_generator/utils/prompts.py`**  
  Jinja templates to render the LLM prompt.

### 2.5 LLM Providers

- **`src/agent_generator/providers/`**  
  - WatsonX provider (REST API wrapper)  
  - OpenAI provider (SDK wrapper)

### 2.6 Framework Generators

- **`src/agent_generator/frameworks/<name>/generator.py`**  
  Implements:
  - `file_extension`: `py` or `yaml`  
  - `generate_code(workflow, settings, mcp)`  

Supported frameworks:  
WatsonX Orchestrate, CrewAI, LangGraph, ReAct, BeeAI.

---

## 3. Generative Pipeline Detail

```mermaid
flowchart TD
  UI[User Prompt] --> Parser
  Parser --> PromptRender
  PromptRender --> LLM
  LLM --> Workflow[Workflow Graph]
  Workflow --> Generator
  Generator --> Code[Generated Code/YAML]
````

* **Parser**: builds the workflow graph
* **PromptRender**: prepares LLM input
* **LLM**: returns completion
* **Generator**: stamps out code from templates

---

## 4. BeeAI Multi‑Agent Backend

The BeeAI backend can run **in‑process** (`GENERATOR_BACKEND_URL=local`) or as a standalone HTTP service.

### 4.1 Endpoints

* **`POST /plan`** → returns a build plan
* **`POST /build`** → executes build tasks, returns artefact tree

### 4.2 Agents & Flow

```text
┌──────────────────────────┐          ┌───────────────────────┐
│      REQUEST ROUTER      │  plan    │   PLANNING AGENT      │
│  (FastAPI or in‑proc)    │─────────►│ ("Architect")         │
└──────────────────────────┘          └────────┬──────────────┘
               ▲                               │ build_tasks
               │ /build                        ▼
               │                    ┌───────────────────────────┐
               └────────────────────┤  BUILDER MANAGER AGENT    │
                                    └────────┬──────────────────┘
                                             │ spawns
         ┌──────────────────────────┐        │
         │  PY_TOOL_BUILDER agent   │◄───────┘
         ├──────────────────────────┤
         │  MCP_TOOL_BUILDER agent  │◄─┐
         ├──────────────────────────┤  │
         │  YAML_AGENT_WRITER agent │◄─┤   (parallel)
         └──────────────────────────┘  │
                                       │
                               ┌───────▼────────┐
                               │  MERGER AGENT  │
                               └────────┬───────┘
                                        ▼
                           writes to build/<framework>/
```

* **Planning Agent**
  Uses GPT to decide which existing MCP gateways to reuse and which Python tools to scaffold.
* **Builder Manager**
  Fans out tasks (`python_tool`, `mcp_tool`, `yaml_agent`) via `asyncio.gather`.
* **Py-Tool Builder**
  Scaffolds minimal Python packages under `tool_sources/`.
* **MCP-Tool Builder**
  References or clones existing MCP gateways under `mcp_servers/`.
* **YAML Agent Writer**
  Writes the final agent YAML under `agents/`.
* **Merger Agent**
  Walks the `build/` directory returning a sorted artefact tree.

---

## 5. Post‑Build Artifact

Each build produces:

```
build/<framework>/
├── agents/
│   └── <agent>.yaml
├── tool_sources/
│   └── <tool_name>/src/<tool_name>/main.py
└── mcp_servers/
    └── <gateway_name>/.placeholder
```

This bundle can run as its own MCP server and be imported directly into WatsonX Orchestrate.

---

## 6. Extensibility

* **Add a Provider**: implement `BaseProvider`, register in `providers/`.
* **Add a Framework**: add generator module under `frameworks/` and templates.
* **Extend Planner**: update the `_ARCH_PROMPT` or switch models.

---

## 7. File Locations

```
src/agent_generator/
├── cli.py
├── config.py
├── orchestrator_proxy.py
├── wizard.py
├── frameworks/
│   └── <framework>/generator.py
├── providers/
│   └── *_provider.py
└── utils/
    ├── parser.py
    ├── prompts.py
    └── scaffold.py
```

Jump in: **[Installation ➜](installation.md)** · **[Usage ➜](usage.md)** · **[Frameworks ➜](frameworks.md)**

