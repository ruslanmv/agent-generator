# MCP-01 — Matrix MCP server

## What it is
A Model Context Protocol (MCP) server that exposes Matrix Builder's controlled build loop as
**live tools** any MCP-capable AI coder (GitPilot, Claude Code, Cursor, …) can call:

`matrix_plan_batch` → `matrix_prompt` → *(coder writes code)* → `matrix_check` →
`matrix_repair` *(if not passed)* → `matrix_commit` → `matrix_publish`.

It is implemented in `agent_generator/mcp_server.py` and started with `mb mcp serve`. It **reuses**
the same engine (`AgentGenerator`: plan / coder_handoff / validate / repair) and the same `.mb/`
store as the `mb` CLI — no business logic is duplicated.

## Why it exists
Until now, integration meant writing static helper files (`.gitpilotrules`, `CLAUDE.md`, …) the
coder reads once. MCP turns that into a **live control loop the agent drives itself**: plan a
bounded batch, get the contract-bound prompt, implement, ask Matrix to validate, self-repair until
`approved`, then record a Matrix Commit — never leaving the contract.

## How GitPilot uses `.gitpilotrules`
GitPilot natively loads workspace rules from `<ws>/.gitpilotrules` (and `.gitpilot/rules/*.md`).
`matrix_prompt` with `coder="gitpilot"` writes the Matrix contract into `.gitpilotrules` (never
`MATRIX_INSTRUCTIONS.md`) and the response says so explicitly (`rules_path: ".gitpilotrules"`). So
GitPilot's Explorer/Planner/Coder/Reviewer honor the allowlist + acceptance + `MATRIX_STATUS`
automatically — both when reading the file *and* when calling the tools.

## Start the server
```bash
mb mcp serve --transport stdio --project .
```
`stdio` is the default (best fit for Claude Code / Cursor / GitPilot MCP clients). HTTP/SSE is a
later addition; MCP-01 ships stdio only. The command fails clearly if dependencies are missing.

## MCP config
```json
{
  "mcpServers": {
    "matrix-builder": {
      "command": "mb",
      "args": ["mcp", "serve", "--transport", "stdio", "--project", "."]
    }
  }
}
```

## Tools (input → output)
| Tool | Purpose | Key output |
|---|---|---|
| `matrix_plan_batch` | create/preview the next bounded batch | `batch_id`, `batch_number`, `next_tool` |
| `matrix_prompt` | emit the coder prompt + helper files | `prompt`, `helper_files`, `rules_path` |
| `matrix_check` | validate changes against the contract | `status` (passed/needs_repair/rejected), `exit_code`, `issues` |
| `matrix_repair` | bounded repair prompt for the coder | `repair_prompt`, `allowed_files` |
| `matrix_commit` | record a Matrix Commit after a pass | `matrix_commit_id`, `commit_path` |
| `matrix_publish` | prepare a release (dry-run by default) | `dry_run`, `message` |

`matrix_check` exit codes: **0 passed · 1 needs repair · 2 rejected** — same authority as `mb check`.
`matrix_commit` writes the canonical `.mb/commits/NNN/manifest.json` **and** an MCP-facing flat
record at `.matrix/commits/NNN.json` (coder/provider/model/batch/status/files_changed).

## Example integration shape (GitPilot / Claude Code / Cursor)
1. Coder calls `matrix_plan_batch(goal="Add a /health endpoint")`.
2. Coder calls `matrix_prompt(coder="gitpilot")` → `.gitpilotrules` lands in the repo.
3. The coder implements inside the allowlist.
4. Coder calls `matrix_check(changed_files=[...])` → `passed` | `needs_repair` | `rejected`.
5. If not passed → `matrix_repair` → back to step 3.
6. If passed → `matrix_commit(provider=..., model=...)`.

## Limitations (MCP-01)
- stdio transport only (HTTP/SSE later).
- `matrix_publish` is dry-run only; real MatrixHub publishing is gated behind `dry_run=false`
  and not enabled yet.
- Local-first: operates on `.mb/`/`.matrix/`; no production Aiven DB and no cloud LLM keys.

## Is agent-generator used in MCP-01?
**Not yet, as an explicit E2E participant.** MCP-01 itself focuses on matrix-builder's workflow
(GitPilot, the MCP server, `.gitpilotrules`, and the check/repair/commit tools). agent-generator is
*prepared* for, but not the subject of, MCP-01 — it becomes a required participant in the full E2E.

## Next step — the full local E2E (agent-generator is required, not bypassed)
A fully-offline vertical slice where each tool keeps its role:

```
Ollama          → GitPilot → agent-generator → matrix-builder → Hello World → validation → Commit #001
local backend     codes       creates the       manages batches,
                              Matrix contract    prompts, validation,
                              /bundle            commits
```

Data flow (do **not** bypass agent-generator):

```
user idea
  → agent-generator creates the Matrix contract/bundle   (REQUIRED)
  → matrix-builder turns it into Batch 01 + prompts
  → GitPilot executes Batch 01 using Ollama
  → matrix-builder validates and records Matrix Commit #001
```

Roles: **agent-generator** = blueprint / Matrix contract+bundle from the idea · **matrix-builder**
= batches, prompts, validation, commits · **GitPilot** = the coding work · **Ollama** = local model.

**Acceptance criterion (added):** the E2E must prove that agent-generator *receives* the idea
"Create a simple Hello World website" and *produces* a Matrix-compatible contract/bundle
(`MATRIX_BLUEPRINT.yaml` etc.) that matrix-builder can consume — alongside: GitPilot creates
`index.html` containing "Hello Matrix", validation passes, `.matrix/commits/001.json` exists, and
no production Aiven DB / cloud key is used.

### What runs today
- **Deterministic, in CI now:** `tests/test_e2e_matrix_contract.py` proves the Matrix half —
  agent-generator produces the bundle from the idea, matrix-builder validates a Hello-World
  change (`frontend/index.html`, inside the allowlist) and records Matrix Commit #001 — with no
  Ollama, no GitPilot, no secrets.
- **Manual/local script:** `scripts/e2e/local_ollama_gitpilot_hello.sh` runs the real CLIs
  (`agent-generator matrix generate`, `mb`, `mb mcp serve`). The coding step is
  `scripts/e2e/gitpilot_runner.py`, which configures GitPilot for Ollama and reports the path it
  took: `gitpilot` / `ollama` / `simulated`.

### Honest status of the GitPilot+Ollama coding step
GitPilot's only headless CLI (`gitpilot run`) is GitHub-centric (needs `--repo` + a token); local
workspace coding is its interactive/agent layer with no one-shot local-file API. So today the
runner configures GitPilot for Ollama and, when Ollama is up, uses the **local Ollama model under
the Matrix contract** to write the file; when Ollama is absent it **simulates** (clearly labelled,
never a false pass). **Follow-up:** wire GitPilot's local agent for true headless execution.

> Single commit path: drive validate+commit through the MCP tools (`matrix_check` → `matrix_commit`).
> Do not also run `mb check` in the same flow — its L1 auto-commit would consume the commit number.

Draft: `scripts/e2e/local_ollama_gitpilot_hello.sh` (manual/local; future CI job
`e2e-local-ollama-gitpilot-hello-world`). The deterministic half above is the CI-ready slice.

## Follow-ups
- DATA-01 (S3 object storage + signed URLs), OBS-01 (OTel export + 20-conn-cap alerts).
- matrix-definitions anomaly: `packs/history/2026.07.0` exists while current/VERSION is `2026.06.0`
  — reconcile (does not block MCP-01).
