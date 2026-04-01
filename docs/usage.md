# Usage Guide

## CLI

### Basic Syntax

```bash
agent-generator "your requirement" --framework <framework> [options]
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `-f, --framework` | *(required)* | `crewai`, `crewai_flow`, `langgraph`, `react`, `watsonx_orchestrate` |
| `-p, --provider` | `watsonx` | `watsonx` or `openai` |
| `--model` | provider default | Override LLM model |
| `--mcp / --no-mcp` | off | Add MCP FastAPI wrapper |
| `-o, --output` | stdout | Write to file |
| `--dry-run` | off | No LLM call |
| `--show-cost` | off | Show token/cost estimate |
| `--temperature` | 0.7 | Sampling temperature |
| `--max-tokens` | 4096 | Max completion tokens |

### Examples

**Generate a CrewAI project:**

```bash
agent-generator \
  "Build a research team with a researcher and a writer" \
  --framework crewai \
  --output research_team.py
```

**Generate WatsonX Orchestrate YAML:**

```bash
agent-generator \
  "Customer support assistant that handles tickets" \
  --framework watsonx_orchestrate \
  --output support.yaml
```

**Use OpenAI instead of WatsonX:**

```bash
agent-generator \
  "Data analysis pipeline" \
  --framework langgraph \
  --provider openai \
  --model gpt-4o
```

**Dry run (no credentials needed):**

```bash
agent-generator "Test agent" --framework crewai --dry-run
```

**With MCP wrapper:**

```bash
agent-generator \
  "Research assistant" \
  --framework crewai --mcp \
  --output assistant.py
```

---

## Web UI

### Start the Server

```bash
# Development
uvicorn agent_generator.wsgi:app --host 0.0.0.0 --port 8000 --reload

# Production
uvicorn agent_generator.wsgi:app --host 0.0.0.0 --port 8000 --workers 4
```

### Using the Web UI

1. Open **http://localhost:8000**
2. Describe your agent team in the text area
3. Pick a framework (Auto, CrewAI, LangGraph, WatsonX)
4. Choose artifact mode (Code Only, YAML Only, Code + YAML)
5. Select tools from the catalog (optional)
6. Click **Generate**
7. Browse generated files in the file tree
8. Preview code with syntax highlighting
9. Download as ZIP
10. Iterate with follow-up prompts

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Home page |
| `/generate` | POST | Generate from form |
| `/edit` | POST | Edit existing project |
| `/download/{id}` | GET | Download ZIP |
| `/api/plan` | POST | Get ProjectSpec JSON |
| `/api/build` | POST | Build from ProjectSpec |
| `/api/generate` | POST | Combined plan + build |
| `/health` | GET | Health check |

### API Example

```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Build a research team",
    "framework": "crewai",
    "provider": "watsonx"
  }'
```

---

## Docker

```bash
docker build -t agent-generator .
docker run -e WATSONX_API_KEY=... -e WATSONX_PROJECT_ID=... \
           -p 8000:8000 agent-generator
```

CLI inside Docker:

```bash
docker run --rm -e WATSONX_API_KEY=... \
  agent-generator agent-generator "Say hi" -f react --dry-run
```

---

## MCP Server Wrapper

Python outputs can include a FastAPI MCP wrapper:

```bash
agent-generator "Data pipeline" -f langgraph --mcp -o pipeline.py
python pipeline.py   # Runs FastAPI on :8080 with POST /invoke
```

---

**Next:** [Frameworks](frameworks.md) | [Architecture](architecture.md)
