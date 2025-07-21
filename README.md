# `agent‑generator`

*Transform natural‑language requirements into fully configured multi‑agent AI teams – no scripting, no complexity.*

[![PyPI](https://img.shields.io/pypi/v/agent-generator.svg)](https://pypi.org/project/agent-generator)
Repository    : [https://github.com/ruslanmv/agent-generator.git](https://github.com/ruslanmv/agent-generator.git)
Maintainer    : [ruslanmv.com](https://ruslanmv.com)

---

## Table of Contents

1. [Why `agent‑generator`](#why-agent-generator)
2. [Features](#features)
3. [Supported Frameworks & Providers](#supported-frameworks--providers)
4. [Installation](#installation)
5. [Quick Start](#quick-start)
6. [CLI Reference & Examples](#cli-reference--examples)
7. [Web UI (Flask)](#web-ui-flask)
8. [Configuration & Environment Variables](#configuration--environment-variables)
9. [Project Directory Structure](#project-directory-structure)
10. [Under the Hood](#under-the-hood)
11. [Extending the Package](#extending-the-package)
12. [Troubleshooting](#troubleshooting)
13. [Development Workflow](#development-workflow)
14. [Release & Publishing](#release--publishing)
15. [Roadmap](#roadmap)
16. [License](#license)

---

## Why `agent‑generator`

Building multi‑agent systems is powerful but verbose: each framework has its own boilerplate, configuration style, and deployment quirks.
`agent‑generator` lets you describe the **intent** (“I need a social‑media team that …”) and instantly produces:

* **Python code** (CrewAI, CrewAI‑Flow, LangGraph, ReAct)
* **WatsonX orchestrate YAML** (enterprise workflow)
* **MCP server packages** for every Python framework output so they can be **registered in an MCP Gateway** and later **imported into WatsonX Orchestrate** as first‑class skills
* **JSON specs** for audits, versioning or downstream tools
* **Diagrams** (Mermaid / Graphviz) so you can *see* the team at a glance

---

## Features

| Category                   | Highlights                                                                                            |
| -------------------------- | ----------------------------------------------------------------------------------------------------- |
| **Generator**              | Plain English → agent roles, tasks & workflow → framework‑specific code.                              |
| **Multiple Frameworks**    | CrewAI · CrewAI Flow · LangGraph · ReAct · WatsonX Orchestrate.                                       |
| **LLM Provider (default)** | **IBM WatsonX** (`meta‑llama‑3‑70b‑instruct`) – OpenAI available via optional extra.                  |
| **MCP Integration**        | Non‑Orchestrate outputs ship with a tiny MCP server wrapper so they can be mounted on an MCP Gateway. |
| **Flask Web UI**           | Form‑based input, DAG visualisation, code preview & download.                                         |
| **Token & Cost Report**    | Live estimate before you run the prompt.                                                              |
| **Well‑typed Models**      | Pydantic schemas for Agents, Tasks, Workflow – easy to extend.                                        |
| **Pluggable**              | Add providers or frameworks with a single class and registration line.                                |
| **CI / CD**                | GitHub Actions for lint + typecheck + tests, and automated PyPI publish.                              |
| **Container‑ready**        | Dockerfile with Gunicorn server for production deployment.                                            |

---

## Supported Frameworks & Providers

### Framework Matrix

| Framework (`--framework`) | Produces           | Deployment target                               | MCP Ready? |
| ------------------------- | ------------------ | ----------------------------------------------- | ---------- |
| `crewai`                  | `*.py`             | Stand‑alone Python or **MCP server**            | ✔          |
| `crewai_flow`             | `*.py`             | Event‑driven Python or **MCP server**           | ✔          |
| `langgraph`               | `*.py`             | LangChain Graph or **MCP server**               | ✔          |
| `react`                   | `*.py`             | Single‑file ReAct or **MCP server**             | ✔          |
| `watsonx_orchestrate`     | `orchestrate.yaml` | **WatsonX Orchestrate** native skill definition | n/a        |

### LLM Providers

| Provider (`--provider`) | Extra tag  | Default? | Default model               |
| ----------------------- | ---------- | -------- | --------------------------- |
| `watsonx`               | *none*     | **Yes**  | `meta‑llama‑3‑70b-instruct` |
| `openai`                | `[openai]` | No       | `gpt‑4o`                    |

If you omit `--provider`, **IBM WatsonX** is used automatically.

---

## Installation

```bash
# Core (WatsonX default)
pip install agent-generator

# Add OpenAI support
pip install "agent-generator[openai]"

# Development + tests + docs + Flask Web UI
pip install "agent-generator[dev,web]"
```

Requires **Python ≥ 3.9**.

---

## Quick Start

```bash
# 1 Set WatsonX keys (or put them in .env)
export WATSONX_API_KEY="..."
export WATSONX_PROJECT_ID="..."
export WATSONX_URL="https://us-south.ml.cloud.ibm.com"

# 2 Generate a CrewAI team and MCP server stub
agent-generator \
  "I need a research assistant that summarizes papers and answers questions" \
  --framework crewai \
  --output research_team.py

# 3 (Optionally) start the generated MCP server
python research_team.py serve  # exposes /invoke on localhost:8080
```

---

## CLI Reference & Examples

```text
agent-generator [OPTIONS] "<requirement sentence>"
```

| Flag / Option        | Default / Values                                                     | Purpose                                                                        |
| -------------------- | -------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| `-f, --framework` \* | `crewai`, `crewai_flow`, `langgraph`, `react`, `watsonx_orchestrate` | Code generator to use.                                                         |
| `-p, --provider`     | `watsonx` *(default)* \| `openai`                                    | LLM back‑end.                                                                  |
| `--model`            | Provider default                                                     | Override model name.                                                           |
| `--temperature`      | `0.7`                                                                | Sampling temperature.                                                          |
| `--max-tokens`       | `4096`                                                               | Response cap.                                                                  |
| `--format`           | `py` / `json` (auto)                                                 | Force output format.                                                           |
| `-o, --output`       | stdout                                                               | Write to file.                                                                 |
| `--mcp`              | flag                                                                 | Package output as an MCP server (default *on* for non‑Orchestrate frameworks). |
| `--dry-run`          | flag                                                                 | Plan only, no LLM call.                                                        |
| `--show-cost`        | flag                                                                 | Display token & cost estimate.                                                 |
| `--log-level`        | `info` (`debug`, `warning`)                                          | Verbosity.                                                                     |

*Example – generate LangGraph skill & MCP bundle ready for Gateway import:*

```bash
agent-generator \
  "Team to generate viral social media posts" \
  -f langgraph --mcp --output viral_team.py
```

---

## Web UI (Flask)

```bash
# Dev
FLASK_APP=agent_generator.web FLASK_ENV=development flask run

# Production
gunicorn agent_generator.wsgi:create_app -b 0.0.0.0:8000 --workers 4
```

*Pick provider & model → select framework → type requirements → preview DAG → download code or MCP package.*

---

## Configuration & Environment Variables

```env
# WatsonX (defaults)
WATSONX_API_KEY="..."
WATSONX_PROJECT_ID="..."
WATSONX_URL="https://us-south.ml.cloud.ibm.com"

# Optional OpenAI
OPENAI_API_KEY="sk-..."

# General
AGENTGEN_LOG_LEVEL="debug"
AGENTGEN_DEFAULT_MODEL="meta-llama-3-70b-instruct"
```

---

## Project Directory Structure

```txt
agent-generator/
├── .github/workflows/           # CI + release
├── docs/                        # MkDocs docs
├── examples/                    # Ready‑made demos
├── scripts/                     # Utility scripts
├── src/agent_generator/
│   ├── cli.py                   # Typer entry point
│   ├── config.py                # Default provider = watsonx
│   ├── models/                  # Agent, Task, Workflow
│   ├── providers/               # watsonx (default) + openai
│   ├── frameworks/              # crewai, crewai_flow, langgraph, react, watsonx_orchestrate
│   ├── utils/                   # parser, prompts, visualizer, logger
│   ├── web/                     # Flask UI
│   ├── data/                    # Prompt fragments
│   └── wsgi.py                  # Gunicorn entry
├── tests/                       # Pytest suite
├── Dockerfile                   # Prod container
├── pyproject.toml               # Build & deps
└── CHANGELOG.md
```

> **MCP note:** for every framework besides `watsonx_orchestrate`, the generator drops a tiny `if __name__ == "__main__": app.run()` block that turns the file into a RESTful MCP server ready to register on an MCP Gateway.

---

## Under the Hood

1. Typer CLI → `Settings` (WatsonX default).
2. NLP parser → preliminary spec.
3. Provider template → prompt → LLM call.
4. Framework generator → code / YAML + optional MCP wrapper.
5. Formatter & token cost calc.
6. Output file & progress bar.

---

## Extending the Package

*Follow the usual “add a provider” / “add a framework” steps — the MCP wrapper is mixed in automatically via `utils.mcp_scaffold`.*

---

## Troubleshooting

| Symptom                      | Fix                                                  |
| ---------------------------- | ---------------------------------------------------- |
| `401 Unauthorized` (WatsonX) | Check API key / project ID / URL.                    |
| `ModuleNotFoundError: flask` | `pip install "agent-generator[web]"`.                |
| Gateway can’t import skill   | Re‑generate with `--mcp`, ensure port isn’t blocked. |

---

## Development Workflow

```bash
git clone https://github.com/ruslanmv/agent-generator.git
cd agent-generator
pip install -e ".[dev,web,openai]"
pre-commit install
pytest -n auto -v
mkdocs serve
```

---

## Release & Publishing

*Tag → CI builds wheels → uploads to TestPyPI → manual promote or auto‑approve to PyPI.*

---

## Roadmap

* MCP Gateway UI helper to browse & deploy generated skills
* Azure OpenAI provider
* VS Code generation extension
* Real‑time collaborative flow editor

---

## License

MIT © Ruslan M. V., 2025‑present – *may your agents collaborate effectively!*
