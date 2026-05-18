# Usage

Most people use the CLI. Some teams prefer the web UI. The API is for
wiring it into your own tooling. All three call the same generator.

## CLI — the short version

```bash
agent-generator "<your sentence>" -f <framework> [-o <path>]
```

That's the only shape you need to remember.

## Recipes

### Generate a CrewAI research team

```bash
agent-generator "Research team with a researcher and a writer" \
  -f crewai -o research_team/
```

You get a full CrewAI project — `crew.py`, `agents.yaml`, `tasks.yaml`,
tool stubs, tests, `pyproject.toml`, README.

### Export a WatsonX Orchestrate agent

```bash
agent-generator "Customer support assistant that triages tickets" \
  -f watsonx_orchestrate -o support.yaml

orchestrate agents import -f support.yaml
```

### Build a LangGraph data pipeline on OpenAI

```bash
agent-generator "Pipeline that extracts, transforms, loads data" \
  -f langgraph -p openai --model gpt-4o -o pipeline.py
```

### Wrap any Python output as an MCP server

```bash
agent-generator "Research assistant" -f crewai --mcp -o assistant.py
python assistant.py          # FastAPI on :8080, POST /invoke
```

### Estimate cost before generating

```bash
agent-generator "Multi-step content workflow" -f crewai_flow --show-cost
```

### Try without credentials

```bash
agent-generator "Anything" -f react --dry-run
```

## All the CLI flags

| Flag | Default | What it does |
|---|---|---|
| `-f, --framework` | *(required)* | `crewai`, `crewai_flow`, `langgraph`, `react`, `watsonx_orchestrate` |
| `-p, --provider` | `watsonx` | `watsonx` or `openai` |
| `--model` | provider default | Override the model. |
| `--mcp / --no-mcp` | off | Add a FastAPI `/invoke` wrapper to Python output. |
| `-o, --output` | stdout | Write to a file or directory. |
| `--dry-run` | off | Skip the LLM call (fake spec, real renderer). |
| `--show-cost` | off | Print token + cost estimate before generating. |
| `--temperature` | 0.7 | Sampling temperature for the planning call. |
| `--max-tokens` | 4096 | Cap on the planning response. |

## Web UI

```bash
uvicorn agent_generator.wsgi:app --host 0.0.0.0 --port 8000 --reload
```

Open `http://localhost:8000` and you get:

1. A text area to describe the agent team.
2. A framework picker (or **Auto**).
3. An artifact-mode picker (code, YAML, or both).
4. A tool catalogue (six prebuilt templates).
5. A file tree + syntax-highlighted preview after generation.
6. A **Download ZIP** button.

The full platform (`make start`) adds auth, projects, runs, marketplace,
and audit on top of the same screens.

## REST API

| Path | Method | What it does |
|---|---|---|
| `/api/plan` | POST | Run the planner; get a `ProjectSpec` JSON. |
| `/api/build` | POST | Render files from a `ProjectSpec`. |
| `/api/generate` | POST | Plan + build in one call. |
| `/download/{id}` | GET | Download a generated bundle as ZIP. |
| `/health` | GET | Liveness probe. |

```bash
curl -X POST http://localhost:8000/api/generate \
  -H 'content-type: application/json' \
  -d '{"prompt": "Research team", "framework": "crewai", "provider": "watsonx"}'
```

## Docker

```bash
docker build -t agent-generator .
docker run -e WATSONX_API_KEY=... -e WATSONX_PROJECT_ID=... \
           -p 8000:8000 agent-generator
```

CLI inside the container:

```bash
docker run --rm -e WATSONX_API_KEY=... \
  agent-generator agent-generator "Say hi" -f react --dry-run
```

---

**Next:** [Pick a framework](frameworks.md) · [Architecture](architecture.md)
