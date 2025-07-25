# Usage Guide

This page covers common workflows for both the **CLI** and the **Flask Web UI**.  
For installation instructions see [Installation](installation.md).

---

## 1  Interactive Wizard (Zero‑Flag)

Simply running:

```bash
agent-generator
````

without any arguments launches the **guided wizard**:

```text
🪄  Agent Generator • Guided mode

Describe what you’d like to build:
> A research assistant that can search and read internal PDFs and summarise them.

Choose target framework (default = watsonx_orchestrate):
  1) watsonx_orchestrate
  2) crewai
  3) langraph
  4) beeai
  5) react
Select [1-5]: 1

⏳  Contacting backend orchestrator …

📂  Proposed project structure:

  build/
    watsonx_orchestrate/
      agents/research_assistant.yaml
      tool_sources/pdf_summariser/…
      mcp_servers/
        docling_gateway/

Generate this project? [Y/n]: y
🤖  Running multi-agent build …
✔  pdf_summariser scaffolded
✔  agent YAML written
🚀  Done. Created build/watsonx_orchestrate/
```

This flow:

1. **Prompts** for a free‑text use case
2. **Lets you pick** a framework
3. **Fetches a plan** from the BeeAI backend
4. **Previews** the proposed project tree
5. On **confirmation**, runs the multi‑agent builder to scaffold all code and YAML

---

## 2  Command‑line Interface (One‑Liners)

### 2.1 `create` Command

For power users, you can skip most prompts with `create`:

```bash
agent-generator create "Research assistant for PDFs" \
  --framework watsonx_orchestrate \
  --build
```

* **`create`** replaces the wizard input with your prompt
* **`--framework`** picks your target
* **`--build`** asks for final confirmation before building

### 2.2 `generate` Command

To generate code or YAML without scaffolding a full project:

```bash
agent-generator generate "Email summariser" \
  --framework watsonx_orchestrate \
  --output summariser.yaml
```

Or with Python frameworks:

```bash
agent-generator generate "Analyse tweets" \
  --framework crewai \
  --mcp \
  --output tweets_flow.py
```

#### Common flags

| Flag / Option        | Description                                        |
| -------------------- | -------------------------------------------------- |
| `-f, --framework` \* | Which generator to use (`crewai`, `langgraph`, …). |
| `-p, --provider`     | LLM back‑end (`watsonx` default, or `openai`).     |
| `--model`            | Override default model for the provider.           |
| `--temperature`      | Sampling randomness (0–2).                         |
| `--max-tokens`       | Response length cap.                               |
| `--mcp / --no-mcp`   | Wrap Python output in an MCP FastAPI server.       |
| `-o, --output PATH`  | Write result to file instead of stdout.            |
| `--dry-run`          | Build workflow + code skeleton but skip LLM call.  |
| `--show-cost`        | Print token counts & approximate USD cost.         |
| `--version`          | Show CLI version and exit.                         |

---

## 3  Flask Web UI

### 3.1 Run locally

```bash
FLASK_APP=agent_generator.web FLASK_ENV=development flask run
# visit http://localhost:5000
```

### 3.2 Workflow

1. **Fill in prompt** – describe your requirement
2. **Pick framework & provider** – drop‑downs
3. *(Optional)* toggle **MCP wrapper**
4. Click **Generate**
5. Download or copy‑paste the code/YAML
6. Mermaid diagram appears under the code for quick validation

![UI screenshot](images/ui-screenshot.png)

---

## 4  Docker Usage

```bash
docker build -t agent-generator .
docker run -e WATSONX_API_KEY=... -e WATSONX_PROJECT_ID=... \
           -p 8000:8000 agent-generator
# Web UI → http://localhost:8000
```

You can also exec into the container to run the CLI:

```bash
docker run --rm agent-generator \
  agent-generator "Say hi" -f react --dry-run
```

---

## 5  Serving Generated MCP Skills

Every Python framework (`crewai`, `crewai_flow`, `langraph`, `react`, `beeai`) can be generated with an **MCP wrapper**:

```bash
agent-generator "...data pipeline..." \
  -f langraph --mcp -o pipeline.py

python pipeline.py serve      # exposes POST /invoke on port 8080
```

Upload the script or Docker image to your MCP Gateway and import it as a custom skill in WatsonX Orchestrate.

---

## 6  Troubleshooting

| Symptom                        | Resolution                                                                          |
| ------------------------------ | ----------------------------------------------------------------------------------- |
| *CLI raises 401* (WatsonX)     | Verify `WATSONX_API_KEY`, `WATSONX_PROJECT_ID`, region URL.                         |
| *`ModuleNotFoundError: flask`* | `pip install "agent-generator[web]"`                                                |
| *Wizard not appearing*         | Run `agent-generator` with no args; ensure `invoke_without_command=True` is active. |
| *High cost estimate*           | Lower `--max-tokens` or pick a smaller model (e.g. `--model llama-3-8b`).           |
| *Gateway import fails*         | Ensure you used `--mcp` and port 8080 is exposed.                                   |

Still stuck? Open an issue on the [GitHub tracker](https://github.com/ruslanmv/agent-generator/issues).

Jump in: **[Installation ➜](installation.md)** · **[Frameworks ➜](frameworks.md)**
