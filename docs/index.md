# agent-generator

**Describe an AI team in plain English. Get a runnable project.**

![logo](images/logo.png)

You write one sentence. agent-generator picks a framework, wires the
agents, generates the code, validates it, and hands you a ZIP you can
unpack and run.

## What you can build

- **CrewAI** projects — Python + YAML, ready for `crewai run`
- **LangGraph** state machines — typed graphs with one node per task
- **WatsonX Orchestrate** YAML — import straight into Orchestrate
- **CrewAI Flow** pipelines — event-driven mini-crews
- **ReAct** loops — single-file reasoning + tool agents

Run on **WatsonX** out of the box, or switch to **OpenAI** with one flag.

## 60-second tour

```bash
pip install agent-generator
agent-generator "Build a research team with a researcher and a writer" \
  -f crewai -o team/
cd team && crewai run
```

That's it. No prompt engineering, no wiring tools by hand, no copy-pasting
boilerplate. The LLM is called **once** to produce a structured plan; the
rest is template rendering, so the same prompt always yields the same code.

## Why it's safe to ship

| Concern | How we handle it |
|---|---|
| **Hallucinated code** | Templates render from a validated `ProjectSpec`, not from raw LLM output. |
| **Unsafe patterns** | AST scanner blocks `eval`, `exec`, `os.system`, bare `subprocess`. |
| **Drift between runs** | Same prompt + same spec = byte-identical output. |
| **Secrets in code** | Generated `.env.example` only; real secrets live in the platform's vault. |
| **Audit trail** | Every generation is logged; the platform stores the spec and the diff. |

## Two ways to use it

| | CLI | Platform |
|---|---|---|
| **Install** | `pip install agent-generator` | `make install` from a clone |
| **Output** | Files to disk | Web · Desktop · Android |
| **Best for** | Scripts, CI, one-offs | Teams, enterprises, marketplaces |

The CLI is the original tool. The platform adds a FastAPI backend, a SPA,
desktop installers (Tauri), an Android app (Capacitor), audit logs, a
project marketplace, and Helm charts. Same generator under the hood.

---

**Next:** [Install in 30 seconds](installation.md) · [Usage recipes](usage.md) · [Pick a framework](frameworks.md)
