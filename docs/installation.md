
# Installation Guide

*agent-generator* supports **Python ≥ 3.9** and ships with IBM WatsonX as the default LLM provider. Optional extras unlock OpenAI support, the Flask Web UI, and developer tooling.


## Windows (via WSL)

If you’re on Windows, we recommend using WSL (Windows Subsystem for Linux) to get a Linux-like environment.

**Enable WSL**
    Open PowerShell **as Administrator** and run:

```powershell
wsl --install
```

    When it finishes, reboot your PC and launch your new Linux distro (e.g., Ubuntu).

**Create & activate a virtual environment**
    In your WSL terminal:

```bash
python3 -m venv venv
source venv/bin/activate
```

**Upgrade pip & install agent-generator**

```bash
pip install --upgrade pip --break-system-packages
pip install "agent-generator[dev,web,openai]" --break-system-packages
```

If you encounter PEP 668 “externally managed environment” errors inside the `venv`, continue using the `--break-system-packages` flag.

**Prepare the `.env` file**

At the project root (next to `Makefile`, `pyproject.toml`, etc.), create a file named `.env`:

```bash
WATSONX_API_KEY=your_watsonx_key
WATSONX_PROJECT_ID=your_watsonx_project_id
WATSONX_URL=https://us-south.ml.cloud.ibm.com
# (Optional) Uncomment for OpenAI
# OPENAI_API_KEY=sk-...
```

**Load environment variables into your shell**

Still inside WSL, choose one method:

```bash
# Method A: Source all at once
set -a && source .env && set +a
# Method B: Strip Windows carriage returns and export
export $(cat .env | tr -d '\r' | xargs)
```
Verify that the variables were loaded correctly:

```bash
echo "$WATSONX_API_KEY"
echo "$WATSONX_PROJECT_ID"
```

**Run the generator**
    To generate an agent using the default WatsonX provider:

```bash
agent-generator \
    "I need a research assistant that summarises papers" \
    --framework watsonx_orchestrate \
    --output research_assistant.yaml
```

    Or, to use the OpenAI provider:

```bash
export OPENAI_API_KEY=sk-...
agent-generator \
    "I need a research assistant that summarises papers" \
    --framework crewai \
    --provider openai \
    --output research_assistant.py
```

## Basic Installation

To install the core package with WatsonX support only, run:

```bash
pip install agent-generator
```

This gives you:

* The CLI (`agent-generator …`)
* Core runtime dependencies
* The WatsonX provider (default model: `meta-llama/llama-3-3-70b-instruct`)

-----

## Optional Extras

You can install extra dependencies for more features.

| Extra tag | Installs… | When to use it |
| :--- | :--- | :--- |
| `openai` | `openai`, `tiktoken` | Generate code with GPT models |
| `web` | `flask`, `gunicorn` | Run the visual Web UI |
| `dev` | `pytest`, `ruff`, `mypy`, `mkdocs`, `pre-commit` | Contributing or running tests |

**Examples:**

```bash
# Core + Web UI
pip install "agent-generator[web]"

# Core + OpenAI
pip install "agent-generator[openai]"

# Install everything
pip install "agent-generator[dev,web,openai]"
```

-----

## Environment Variables

Create a `.env` file in the project's root directory or export these variables in your shell.

```env
# --- PROVIDER SELECTION ---
# Choose one: "watsonx" (default) or "openai"
AGENTGEN_PROVIDER=watsonx

# --- IBM WatsonX Configuration (if provider is "watsonx") ---
WATSONX_API_KEY="your_watsonx_api_key_here"
WATSONX_PROJECT_ID="your_watsonx_project_id_here"
WATSONX_URL="https://us-south.ml.cloud.ibm.com"

# --- OpenAI Configuration (if provider is "openai") ---
# OPENAI_API_KEY="sk-your_openai_api_key_here"

# --- OPTIONAL OVERRIDES ---
# AGENTGEN_MODEL="meta-llama/llama-3-70b-instruct"
# AGENTGEN_TEMPERATURE="0.7"
# AGENTGEN_MAX_TOKENS="4096"
```

> **Tip:** Add `.env` to your IDE’s environment or use a tool like [direnv](https://direnv.net/) for automatic loading.

-----

## Verifying the Installation

Run a dry run to check if the CLI is working correctly.

```bash
agent-generator "Say hello" --framework react --dry-run --show-cost
```

You should see output similar to this:

```
≈ prompt_tokens=7, completion_tokens=42, est. cost=$0.0001
# Auto-generated ReAct agent
import json
...
```

## Running the Web UI

You can run the web interface using either the Flask development server or Docker.

**Development Server (with hot-reload):**

```bash
FLASK_APP=agent_generator.web FLASK_ENV=development flask run
```

Access the UI at `http://localhost:5000`.

**Production (via Docker):**

```bash
docker build -t agentgen .
docker run -e WATSONX_API_KEY=... -p 8000:8000 agentgen
```

Access the UI at `http://localhost:8000`.


## Upgrading

To upgrade the package to the latest version:

```bash
pip install --upgrade agent-generator
```

> If you installed any optional extras, you must re-specify them during the upgrade:
>
> ```bash
> pip install --upgrade "agent-generator[web,openai]"
> ```


## Troubleshooting

| Issue | Solution |
| :--- | :--- |
| `401 Unauthorized (WatsonX)` | Check that `WATSONX_API_KEY` and `WATSONX_PROJECT_ID` are correct and exported. |
| `ModuleNotFoundError: flask` | You need the `web` extra. Run `pip install "agent-generator[web]"`. |
| CLI hangs or times out | Lower the value of `--max-tokens`, check your network connection, or try a different provider like `--provider openai`. |
| Mermaid diagram not rendering (UI) | Ensure your browser has internet access to the CDN at `unpkg.com`. |


Jump in: **[Installation ➜](installation.md)** · **[Usage ➜](usage.md)** · **[Frameworks ➜](frameworks.md)**