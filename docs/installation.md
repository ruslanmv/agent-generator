# Installation Guide

*agent-generator* supports **Python ≥ 3.9** (3.11+ recommended) and ships with IBM WatsonX as the default LLM provider. Optional extras unlock OpenAI support, the Flask Web UI, and developer tooling.

---

## Windows (via WSL)

If you’re on Windows, we recommend using WSL (Windows Subsystem for Linux) to get a Linux‑like environment.

### Enable WSL

Open **PowerShell as Administrator** and run:

```powershell
wsl --install
````

When it finishes, reboot and launch your new Linux distro (e.g., Ubuntu).

### Create & activate a virtual environment

In your WSL terminal:

```bash
python3 -m venv venv
source venv/bin/activate
```

### Upgrade pip & install agent‑generator

```bash
pip install --upgrade pip --break-system-packages
pip install "agent-generator[dev,web,openai]" --break-system-packages
```

If you encounter PEP 668 “externally managed environment” errors, continue using `--break-system-packages`.

### Prepare the `.env` file

At the project root (next to `pyproject.toml`), create a file named `.env`:

```bash
WATSONX_API_KEY=your_watsonx_api_key
WATSONX_PROJECT_ID=your_watsonx_project_id
WATSONX_URL=https://us-south.ml.cloud.ibm.com
# Optional OpenAI fallback
# OPENAI_API_KEY=sk-...
# To run backend in‑process
# GENERATOR_BACKEND_URL=local
```

### Load environment variables

Still inside WSL, choose one:

```bash
# Method A: source all at once
set -a && source .env && set +a

# Method B: export manually
export $(sed 's/\r$//' .env | xargs)
```

Verify:

```bash
echo "$WATSONX_API_KEY"
echo "$WATSONX_PROJECT_ID"
```

---

## Basic Installation

To install the core package with WatsonX support only:

```bash
pip install agent-generator
```

This gives you:

* The CLI (`agent-generator …`)
* In‑process BeeAI backend (default mode)
* Core runtime dependencies
* The WatsonX provider (default model: `meta-llama/llama-3-3-70b-instruct`)

---

## Optional Extras

You can install extra dependencies for more features:

| Extra tag | Installs…                                        | When to use            |
| :-------- | :----------------------------------------------- | :--------------------- |
| `openai`  | `openai`, `tiktoken`                             | GPT models support     |
| `web`     | `flask`, `gunicorn`                              | Run the Web UI         |
| `dev`     | `pytest`, `ruff`, `mypy`, `mkdocs`, `pre-commit` | Contributing & testing |

```bash
# Core + Web UI
pip install "agent-generator[web]"

# Core + OpenAI
pip install "agent-generator[openai]"

# Install everything
pip install "agent-generator[dev,web,openai]"
```

---

## Environment Variables

Create a `.env` file in the project’s root or export these:

```env
# --- PROVIDER SELECTION ---
# Choose one: "watsonx" (default) or "openai"
AGENTGEN_PROVIDER=watsonx

# --- IBM WatsonX (if using watsonx) ---
WATSONX_API_KEY="your_watsonx_api_key"
WATSONX_PROJECT_ID="your_project_id"
WATSONX_URL="https://us-south.ml.cloud.ibm.com"

# --- OpenAI (if using openai) ---
# OPENAI_API_KEY="sk-your_openai_api_key"

# --- Backend mode ---
# Default is in‑process ("local"), but you can point at a remote server:
# GENERATOR_BACKEND_URL=local
# or
# GENERATOR_BACKEND_URL=http://localhost:8000

# --- Optional overrides ---
# AGENTGEN_MODEL="meta-llama/llama-3-70b-instruct"
# AGENTGEN_TEMPERATURE="0.7"
# AGENTGEN_MAX_TOKENS="4096"
```

> **Tip:** Use [direnv](https://direnv.net/) or similar to manage your `.env`.

---

## Verifying the Installation

Run a dry‑run to confirm the CLI and in‑process backend:

```bash
agent-generator "Say hello" --framework react --dry-run --show-cost
```

Expected output:

```
≈ prompt_tokens=7, completion_tokens=42, est. cost=$0.0001
# Auto-generated ReAct agent
import json
...
```

---

## Running the Web UI

The Flask‑based UI is an optional extra.

### Development server (hot‑reload)

```bash
FLASK_APP=agent_generator.web FLASK_ENV=development flask run
```

Visit `http://localhost:5000`.

### Production (Docker)

```bash
docker build -t agentgen .
docker run \
  -e WATSONX_API_KEY=... \
  -p 8000:8000 \
  agentgen
```

Visit `http://localhost:8000`.

---

## Upgrading

```bash
pip install --upgrade agent-generator
```

> If you installed extras, re‑specify them:

```bash
pip install --upgrade "agent-generator[web,openai]"
```

---

## Troubleshooting

| Issue                            | Solution                                                                                              |
| :------------------------------- | :---------------------------------------------------------------------------------------------------- |
| `401 Unauthorized (WatsonX)`     | Verify `WATSONX_API_KEY`, `WATSONX_PROJECT_ID` and `WATSONX_URL`.                                     |
| `ModuleNotFoundError: flask`     | Install the `web` extra: `pip install "agent-generator[web]"`.                                        |
| CLI hangs or times out           | Try `--max-tokens`, check your network, or switch provider: `--provider openai`.                      |
| Wizard not appearing (zero‑flag) | Ensure you’re running `agent-generator` without sub‑commands, and that `invoke_without_command=True`. |

Jump in: **[Installation ➜](installation.md)** · **[Usage ➜](usage.md)** · **[Frameworks ➜](frameworks.md)**
