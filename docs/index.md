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

## Also: the Matrix Builder engine

The same package is the deterministic engine behind **Matrix Builder** — *give AI coders a
contract, not a prompt*. It turns an idea into a **controlled bundle** (blueprint, locked
standards, scoped tasks, per-coder prompts), then validates what your AI coder produced and
records each accepted change as an immutable **Matrix Commit**.

- **`mb` — local-first CLI:** the full git-for-AI loop on your machine, offline and
  deterministic — `mb init → next → prompt → check → timeline`. See [mb — local-first CLI](matrix-engine/mb-cli.md).
- **`AgentGenerator` SDK:** `parse_idea`, `generate_blueprint_candidates`,
  `generate_controlled_blueprint`, `generate_matrix_bundle`, `generate_coder_prompt_pack`,
  `validate_ai_coder_patch`. See [Public engine API](matrix-engine/public-engine-api.md).
- **HTTP API:** `uvicorn agent_generator.http.app:app` (`/api/v1/...`). See [HTTP API](matrix-engine/http-api.md).
- Works with **Claude Code, Codex, Cursor, GitPilot, IBM Bob**, and any AI coder; publishes
  validated bundles to **MatrixHub** under the [Ruslan Magana Definitions](matrix-engine/ruslan-magana-definitions.md).

Start here: **[Matrix engine quickstart](matrix-engine/quickstart.md)**.

---

**Next:** [Install in 30 seconds](installation.md) · [Usage recipes](usage.md) · [Pick a framework](frameworks.md) · [Matrix engine](matrix-engine/quickstart.md)
