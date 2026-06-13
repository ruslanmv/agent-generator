<p align="left">
  <img src="https://github.com/ruslanmv/agent-generator/blob/master/docs/images/logo.png" alt="Agent-Generator Logo" width="300">
</p>

# agent-generator

**Type a sentence. Ship a multi-agent project — as code, a container, a desktop app, or an Android build.**

[![PyPI](https://img.shields.io/pypi/v/agent-generator.svg)](https://pypi.org/project/agent-generator/)
[![Python 3.10+](https://img.shields.io/pypi/pyversions/agent-generator.svg)](https://pypi.org/project/agent-generator/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE)
[![Try it](https://img.shields.io/badge/demo-Hugging%20Face-yellow)](https://huggingface.co/spaces/ruslanmv/agent-generator)
<a href="https://github.com/agent-matrix/matrix-hub"><img src="https://img.shields.io/badge/Powered%20by-matrix--hub-brightgreen" alt="Powered by matrix-hub"></a>

---

## The Matrix Builder engine

agent-generator is also the **deterministic engine behind [Matrix Builder](https://ruslanmv.com/matrix-builder)** — *give AI coders a contract, not a prompt.* It turns an idea into a controlled, hash-locked bundle (blueprint + locked standards + tasks), emits a contract-bound prompt for each AI coder (Claude Code, Codex, Cursor, GitPilot, IBM Bob, generic), and **validates** the AI's output against that contract — approving, rejecting, or returning a bounded repair prompt.

**Local-first `mb` CLI + Matrix MCP server:** run the controlled loop offline (`mb init/next/prompt/check/repair/commit/sync`) or expose it as live MCP tools with `mb mcp serve` for GitPilot/Claude Code/Cursor.
See [docs/mcp-01.md](docs/mcp-01.md) and [docs/gitpilot-integration.md](docs/gitpilot-integration.md) (GitPilot reads the emitted `.gitpilotrules` natively).

```python
from agent_generator import AgentGenerator
from agent_generator.contracts import IdeaRequest

engine = AgentGenerator()
idea = IdeaRequest(idea="An AI app that analyzes GitHub repositories")
blueprint = engine.generate_controlled_blueprint(idea)
engine.export_zip(blueprint, "dist/app.zip", release_evidence=True)
report = engine.validate_ai_coder_patch("b1", repo_path="dist/out", blueprint=blueprint)
print(report.status)   # approved | needs-repair | rejected
```

```bash
agent-generator matrix candidates --idea "An AI app that analyzes GitHub repositories"
agent-generator matrix export     --idea "..." --out dist/app.zip --release-evidence
agent-generator matrix validate   --idea "..." --repo dist/app
```

The engine is deterministic (no credentials, no network for generation/validation), enforces
the [**Ruslan Magana Definitions**](docs/matrix-engine/ruslan-magana-definitions.md) loaded from
the signed [`matrix-definitions`](https://github.com/agent-matrix/matrix-definitions) pack, and
exposes a stable SDK + optional HTTP facade. See **[docs/matrix-engine/](docs/matrix-engine/)**
— start with the [quickstart](docs/matrix-engine/quickstart.md).

---

## Two surfaces, one repo

| Surface       | What you get                                                            | Use when…                                  |
|---------------|--------------------------------------------------------------------------|--------------------------------------------|
| **CLI**       | `pip install agent-generator` → one-shot project generator (this README, ↓ further down)  | You want a single Python file or YAML.     |
| **Platform**  | FastAPI backend + Vite SPA + Tauri desktop + Capacitor Android, all from one TypeScript codebase. | You want the full app, the wizard, the Marketplace, signed installers, or a Helm install. |

### Run the full platform in three commands

```bash
make install      # CLI + backend (FastAPI) + frontend (Vite SPA)
make test         # CLI tests + backend pytest + frontend type-check & build
make start        # backend on :8000 and SPA on :5173 — Ctrl-C stops both
```

Then open <http://localhost:5173>. Ports are configurable
(`make start BACKEND_PORT=8080 FRONTEND_PORT=4173`).

### Ship desktop / Android binaries

```bash
make build              # nginx SPA bundle + backend Docker image
                        # + .dmg / .msi / .AppImage / .deb / .rpm for THIS host
make build-android      # Android debug APK (needs Android SDK + JDK 17)
```

Signed CI builds (Authenticode, Apple notarization, GPG, Play Store) live in
`.github/workflows/{desktop,mobile,release-app}.yml`.

For the production Kubernetes deployment, see [`deploy/helm/`](deploy/helm).

---

## What the CLI does

You type what you want. You get a complete project.

```bash
agent-generator "Build a research team with a researcher and a writer" -f crewai
```

That's it. You now have working Python code with agents, tasks, and tools.

---

## Try it online

No install needed. Open the demo and start building:

**https://huggingface.co/spaces/ruslanmv/agent-generator**

---

## Install

```bash
pip install agent-generator
```

That gives you the CLI and all core features. Python 3.10+ required.

**Optional extras:**

```bash
pip install "agent-generator[openai]"     # OpenAI provider
pip install "agent-generator[all]"        # All providers + frameworks
```

---

## Quick start

### Step 1 -- Set credentials (pick one)

```bash
# Option A: WatsonX (default)
export WATSONX_API_KEY=your-key
export WATSONX_PROJECT_ID=your-project-id

# Option B: OpenAI
export OPENAI_API_KEY=sk-your-key
export AGENTGEN_PROVIDER=openai
```

### Step 2 -- Generate

```bash
# CrewAI team
agent-generator "Research team that finds papers and writes summaries" -f crewai -o team.py

# LangGraph pipeline
agent-generator "ETL pipeline: extract, transform, load" -f langgraph -o pipeline.py

# WatsonX YAML agent
agent-generator "Customer support assistant" -f watsonx_orchestrate -o support.yaml

# Just test it (no credentials needed)
agent-generator "Hello world agent" -f crewai --dry-run
```

### Step 3 -- Run

```bash
python team.py
```

---

## Supported frameworks

| Framework | What you get |
|-----------|-------------|
| **CrewAI** | `crew.py` + `agents.yaml` + `tasks.yaml` + tools + tests |
| **LangGraph** | `graph.py` with `StateGraph` and typed state |
| **WatsonX Orchestrate** | `agent.yaml` ready for `orchestrate agents import` |
| **CrewAI Flow** | Flow class with `@start` / `@listen` |
| **ReAct** | Reasoning loop with tool registry |

---

## Built-in tools

Your agents can use these out of the box:

| Tool | What it does |
|------|-------------|
| `web_search` | Search the web |
| `pdf_reader` | Read PDF files |
| `http_client` | Call APIs |
| `sql_query` | Query databases |
| `file_writer` | Save files |
| `vector_search` | Semantic search |

---

## Web UI

A visual wizard that guides you step by step:

```bash
uvicorn agent_generator.wsgi:app --port 8000
```

Open **http://localhost:8000** -- describe your agents, pick a framework, download a ZIP.

Works with local LLMs (Ollama), remote LLMs (OllaBridge), or cloud APIs (OpenAI).

---

## CLI options

```
agent-generator "your description" [options]
```

| Flag | What it does |
|------|-------------|
| `-f crewai` | Pick framework: `crewai`, `langgraph`, `watsonx_orchestrate`, `crewai_flow`, `react` |
| `-o file.py` | Save to file (otherwise prints to screen) |
| `--dry-run` | Generate without calling any LLM |
| `--mcp` | Add a FastAPI server wrapper |
| `-p openai` | Use OpenAI instead of WatsonX |
| `--show-cost` | Show estimated cost before generating |

---

## Docker

```bash
docker build -t agent-generator .
docker run -e WATSONX_API_KEY=... -p 8000:8000 agent-generator
```

---

## Contributing

```bash
git clone https://github.com/ruslanmv/agent-generator.git
cd agent-generator

# Full stack (CLI + backend + frontend) in one shot:
make install
make test
make start            # backend :8000 + SPA :5173

# Or just the CLI bits, like the original workflow:
pip install -e ".[dev,all]"
pytest                # CLI tests
ruff check src/       # lint
mkdocs serve          # docs
```

Useful `make` targets:

| Target               | What it does                                                       |
|----------------------|--------------------------------------------------------------------|
| `make install`       | Editable CLI install **plus** `make app-install` (backend + SPA)   |
| `make test`          | CLI pytest **plus** backend pytest + frontend `tsc` + Vite build   |
| `make start`         | Backend + frontend dev servers concurrently (Ctrl-C stops both)    |
| `make stop`          | Stop any backend / frontend dev servers started by `make start`    |
| `make build`         | Frontend bundle + backend Docker image + desktop installer (host)  |
| `make build-android` | Android debug APK                                                  |
| `make help`          | Full list (CLI + platform targets, ~30 of them)                    |

The full architecture (compatibility matrix, frontend shells, backend
service, signing pipeline, Helm chart) is documented in
[`docs/platform.md`](docs/platform.md). The original master plan is in
[`docs/complete-solution-plan.md`](docs/complete-solution-plan.md).

---

## License

Apache 2.0 -- PRs and issues welcome.
