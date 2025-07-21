
# Installation

*agent‑generator* supports **Python ≥ 3.9** and ships with IBM WatsonX as the default LLM provider.  
Optional extras unlock OpenAI support, the Flask Web UI, and developer tooling.

---

## 1  Basic install (WatsonX only)

```bash
pip install agent-generator
````

This gives you:

* CLI (`agent-generator …`)
* Core runtime dependencies
* WatsonX provider (meta‑llama‑3‑70b‑instruct default)

---

## 2  Optional extras

| Extra tag | Installs …                                          | When to use it                |
| --------- | --------------------------------------------------- | ----------------------------- |
| `openai`  | `openai` SDK                                        | Generate code with GPT models |
| `web`     | `flask`, `gunicorn`                                 | Run the visual Web UI         |
| `dev`     | `pytest`, `ruff`, `mypy`, `mkdocs`, `pre‑commit`, … | Contributing / testing        |

```bash
# Core + Web UI
pip install "agent-generator[web]"

# Core + OpenAI
pip install "agent-generator[openai]"

# Everything (dev, web, openai)
pip install "agent-generator[dev,web,openai]"
```

---

## 3  Environment variables

Create a `.env` in the repo root (or export in your shell):

```env
# WatsonX (default provider)
WATSONX_API_KEY="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
WATSONX_PROJECT_ID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
WATSONX_URL="https://us-south.ml.cloud.ibm.com"

# Optional OpenAI
OPENAI_API_KEY="sk-…"

# Optional overrides
AGENTGEN_MODEL="meta-llama-3-70b-instruct"
AGENTGEN_TEMPERATURE="0.7"
AGENTGEN_MAX_TOKENS="4096"
```

> **Tip**  Add `.env` to your IDE’s environment or use **direnv** for automatic loading.

---

## 4  Verify the install

```bash
agent-generator "Say hello" --framework react --dry-run --show-cost
```

Expected output (truncated):

```
≈ prompt_tokens=7, completion_tokens=42, est. cost=$0.0001
# Auto‑generated ReAct agent
import json
...
```

---

## 5  Running the Web UI

```bash
# Dev server with hot‑reload
FLASK_APP=agent_generator.web FLASK_ENV=development flask run

# Production (Docker)
docker build -t agentgen .
docker run -e WATSONX_API_KEY=... -p 8000:8000 agentgen
```

Browse to [http://localhost:5000](http://localhost:5000) (dev) or [http://localhost:8000](http://localhost:8000) (Docker).

---

## 6  Upgrading

```bash
pip install --upgrade agent-generator
```

*(If extras were installed, append them again: `pip install --upgrade "agent-generator[web]"`)*

---

## Troubleshooting

| Issue                              | Solution                                                              |
| ---------------------------------- | --------------------------------------------------------------------- |
| `401 Unauthorized (WatsonX)`       | Check `WATSONX_API_KEY` and `WATSONX_PROJECT_ID`.                     |
| `ModuleNotFoundError: flask`       | `pip install "agent-generator[web]"`.                                 |
| CLI hangs / times out              | Lower `--max-tokens`; check network; try `--provider openai`.         |
| Mermaid diagram not rendering (UI) | Ensure internet access to CDN `unpkg.com`; or bundle Mermaid locally. |

Still stuck? File an issue on our [GitHub tracker](https://github.com/ruslanmv/agent-generator/issues).
