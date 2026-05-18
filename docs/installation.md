# Install in 30 seconds

## The CLI

```bash
pip install agent-generator
```

That's the whole thing. Python 3.10 or newer.

Need OpenAI, CrewAI runtime, or LangGraph runtime too?

```bash
pip install "agent-generator[all]"
```

## The platform (web · desktop · mobile)

You only need this if you want the full team-ready experience — the
FastAPI backend, the SPA, the marketplace, the desktop installer.

```bash
git clone https://github.com/ruslanmv/agent-generator
cd agent-generator
make install
make start          # backend :8000 + SPA :5173
```

`make start` runs both dev servers and tails the logs. Hit Ctrl-C to stop.

Extra requirements when going beyond the CLI:

| For | You need |
|---|---|
| Backend + SPA | Node 20+ |
| Desktop installer | Rust 1.77+ and the Tauri prereqs |
| Android APK | JDK 17 and the Android SDK |

## Set your credentials

Create a `.env` in the project root:

```env
# Pick one provider
AGENTGEN_PROVIDER=watsonx          # or "openai"

# WatsonX
WATSONX_API_KEY=your-key
WATSONX_PROJECT_ID=your-project
WATSONX_URL=https://us-south.ml.cloud.ibm.com

# OpenAI (only if you switched the provider)
OPENAI_API_KEY=sk-...
```

Then either source it (`set -a && source .env && set +a`) or export the
variables yourself. The platform reads the same names from its own
Settings model, so a `.env` works for both.

## Did it work?

```bash
agent-generator "Test agent" -f crewai --dry-run
```

`--dry-run` skips the LLM call so you don't need credentials just to
prove the install. You should see a fake-but-valid CrewAI project printed
to stdout.

## Docker

```bash
docker build -t agent-generator .
docker run -e WATSONX_API_KEY=... -e WATSONX_PROJECT_ID=... \
           -p 8000:8000 agent-generator
```

Web UI on `http://localhost:8000`. The CLI is also inside the image —
`docker exec` if you want to drive it from a shell.

## Windows

Use WSL. PowerShell is unsupported.

```powershell
wsl --install
```

Then inside WSL: `python3 -m venv .venv && source .venv/bin/activate &&
pip install "agent-generator[all]"`.

## Upgrade

```bash
pip install --upgrade "agent-generator[all]"
```

## When something goes wrong

| You see | Try |
|---|---|
| `401 Unauthorized` (WatsonX) | Re-check `WATSONX_API_KEY` and `WATSONX_PROJECT_ID`. |
| `OPENAI_API_KEY is required` | `pip install "agent-generator[openai]"` and export the key. |
| CLI hangs | Network is slow or the prompt is huge — lower `--max-tokens`. |
| `ModuleNotFoundError` | The extra you need isn't installed: `pip install "agent-generator[<extra>]"`. |

---

**Next:** [Usage recipes](usage.md) · [Pick a framework](frameworks.md)
