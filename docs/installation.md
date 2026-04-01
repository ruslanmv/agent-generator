# Installation

Requires **Python 3.10+**.

## Basic Install

```bash
pip install agent-generator
```

This gives you the CLI, core libraries, and the WatsonX provider.

## Optional Extras

| Extra | What it adds | Install command |
|-------|-------------|-----------------|
| `openai` | OpenAI provider + tiktoken | `pip install "agent-generator[openai]"` |
| `crewai` | CrewAI runtime (for running generated code) | `pip install "agent-generator[crewai]"` |
| `langgraph` | LangGraph runtime | `pip install "agent-generator[langgraph]"` |
| `all` | All of the above | `pip install "agent-generator[all]"` |
| `dev` | pytest, ruff, mypy, mkdocs | `pip install "agent-generator[dev]"` |

## Environment Variables

Create a `.env` file in your project root:

```env
# Provider selection (default: watsonx)
AGENTGEN_PROVIDER=watsonx

# WatsonX credentials
WATSONX_API_KEY=your-api-key
WATSONX_PROJECT_ID=your-project-id
WATSONX_URL=https://us-south.ml.cloud.ibm.com

# OpenAI credentials (if using OpenAI)
# OPENAI_API_KEY=sk-your-key

# Optional overrides
# AGENTGEN_MODEL=meta-llama/llama-3-3-70b-instruct
# AGENTGEN_TEMPERATURE=0.7
# AGENTGEN_MAX_TOKENS=4096
```

Load them:

```bash
# Option A: source the file
set -a && source .env && set +a

# Option B: export manually
export WATSONX_API_KEY=your-key
export WATSONX_PROJECT_ID=your-project
```

## Verify Installation

```bash
# Dry run (no credentials needed)
agent-generator "Test agent" --framework crewai --dry-run

# Check version
agent-generator --version
```

## Windows (WSL)

On Windows, use WSL:

```powershell
wsl --install
```

Then inside WSL:

```bash
python3 -m venv venv
source venv/bin/activate
pip install "agent-generator[all]"
```

## Docker

```bash
docker build -t agent-generator .
docker run -e WATSONX_API_KEY=... -e WATSONX_PROJECT_ID=... \
           -p 8000:8000 agent-generator
```

Web UI at **http://localhost:8000**, CLI via `docker exec`.

## Upgrading

```bash
pip install --upgrade "agent-generator[all]"
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `401 Unauthorized` (WatsonX) | Check `WATSONX_API_KEY` and `WATSONX_PROJECT_ID` |
| `OPENAI_API_KEY is required` | Install the openai extra: `pip install "agent-generator[openai]"` |
| CLI hangs | Lower `--max-tokens` or check network |
| `ModuleNotFoundError` | Make sure you installed the right extra |

---

**Next:** [Usage](usage.md) | [Frameworks](frameworks.md) | [Architecture](architecture.md)
