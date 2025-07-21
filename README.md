# 🔧 agent‑generator

*From one plain‑English sentence to a production‑ready multi‑agent workflow.*

<p align="left">
  <a href="https://pypi.org/project/agent-generator/">
    <img alt="PyPI Version" src="https://img.shields.io/pypi/v/agent-generator.svg">
  </a>
  <a href="https://img.shields.io/pypi/pyversions/agent-generator">
    <img alt="Python 3.9+" src="https://img.shields.io/pypi/pyversions/agent-generator.svg">
  </a>
  <a href="https://github.com/ruslanmv/agent-generator/actions/workflows/ci.yml">
    <img alt="CI Status" src="https://github.com/ruslanmv/agent-generator/actions/workflows/ci.yml/badge.svg">
  </a>
  <a href="https://github.com/ruslanmv/agent-generator/blob/main/LICENSE">
    <img alt="MIT License" src="https://img.shields.io/badge/licence-MIT-blue.svg">
  </a>
</p>

---

## ✨ Why agent‑generator?

Designing multi‑agent systems is powerful yet verbose—boilerplate, framework quirks, deployment plumbing.  
`agent‑generator` turns intent (“*I need an AI team that …*”) into runnable artefacts:

| Output                             | Where it runs                             |
|------------------------------------|-------------------------------------------|
| **Python scripts** for CrewAI, CrewAI Flow, LangGraph, ReAct | Any Python 3.9+ environment |
| **YAML skill** for WatsonX Orchestrate | IBM WatsonX Orchestrate |
| **FastAPI MCP server** (wrapper)    | MCP Gateway / Kubernetes |
| **JSON spec + Mermaid/DOT**         | Docs, audits, architecture diagrams |

---

## 🚀 Features

| Category            | Details                                                                                       |
|---------------------|------------------------------------------------------------------------------------------------|
| **Multi‑framework** | CrewAI · CrewAI Flow · LangGraph · ReAct · WatsonX Orchestrate                                 |
| **Provider‑agnostic** | IBM WatsonX *(default)* · OpenAI *(extra)*                                                   |
| **MCP integration** | Python outputs include a FastAPI `/invoke` endpoint ready for MCP Gateway registration         |
| **Web UI (Flask)**  | Form‑based generator with live diagram preview & code download                                 |
| **Cost estimator**  | Token counts & USD approximation before you run the prompt                                    |
| **Pluggable**       | Add providers / frameworks via a single subclass & registry                                    |
| **Typed models**    | Pydantic schemas for Agents · Tasks · Workflow                                                 |
| **CI / CD**         | Ruff · Mypy · Pytest in GitHub Actions + automatic PyPI publish                                |
| **Docker‑ready**    | Alpine image with Gunicorn server                                                              |

---

## 📦 Installation

```bash
# Core (WatsonX only)
pip install agent-generator

# + OpenAI provider
pip install "agent-generator[openai]"

# + Flask Web UI and dev tools
pip install "agent-generator[dev,web]"
````

*Requires Python ≥ 3.9.*

---

## ⚡ Quick Start

```bash
# 1 Export WatsonX credentials (or put them in .env)
export WATSONX_API_KEY=...
export WATSONX_PROJECT_ID=...
export WATSONX_URL=https://us-south.ml.cloud.ibm.com

# 2 Generate a CrewAI team as an MCP‑ready Python script
agent-generator \
  "I need a research assistant that summarises papers" \
  --framework crewai --mcp -o research_team.py

# 3 Run the skill locally
python research_team.py                 # run once
python research_team.py serve           # FastAPI /invoke on :8080
```

---

## 🖥 CLI Reference

```text
agent-generator [OPTIONS] "requirement sentence"
```

| Option / Flag        | Default          | Description                                                      |
| -------------------- | ---------------- | ---------------------------------------------------------------- |
| `-f, --framework` \* | —                | crewai · crewai\_flow · langgraph · react · watsonx\_orchestrate |
| `-p, --provider`     | watsonx          | watsonx (default) \| openai                                      |
| `--model`            | provider default | Override LLM model                                               |
| `--mcp / --no-mcp`   | off              | Append FastAPI MCP wrapper (Python only)                         |
| `-o, --output PATH`  | stdout           | Write artefact to file                                           |
| `--dry-run`          |                  | Build spec & code skeleton, no LLM calls                         |
| `--show-cost`        |                  | Print token usage + USD estimate                                 |

*See the full [Usage guide](https://github.com/ruslanmv/agent-generator/blob/main/docs/usage.md) for examples.*

---

## 🌐 Web UI

```bash
FLASK_APP=agent_generator.web FLASK_ENV=development flask run
```

Navigate to **[http://localhost:5000](http://localhost:5000)** → fill the form → generate → download code/YAML.
Deployed via Docker:

```bash
docker build -t agentgen .
docker run -e WATSONX_API_KEY=... -p 8000:8000 agentgen
```

---

## 🛠 Extending

* **New provider** → subclass `BaseProvider`, register in `providers/__init__.py`.
* **New framework** → subclass `BaseFrameworkGenerator`, register in `frameworks/__init__.py`.
  The MCP wrapper is added automatically for any Python output.

---

## 🧑‍💻 Development

```bash
git clone https://github.com/ruslanmv/agent-generator.git
cd agent-generator
pip install -e ".[dev,web,openai]"
pre-commit install
make lint test
mkdocs serve        # live docs
```

---

## 🗺️ Roadmap

* Azure OpenAI provider
* MCP Gateway dashboard helper
* VS Code “Generate agent” command
* Real‑time collaborative flow editor

---

## 📄 License

**MIT** © 2025 Ruslan M. V. – contributions are welcome, PRs + issues encouraged!
