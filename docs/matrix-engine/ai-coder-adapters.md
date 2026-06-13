# AI-coder prompt adapters (Batch 7)

Each supported AI coder receives a **contract-bound** prompt, not a shared template. The
per-coder shape is grounded in the matrix-definitions rule that governs it.

| Coder | `CoderId` | Rule | Handoff | Emphasis |
|---|---|---|---|---|
| Claude Code | `claude-code` | RMD-110 | `cli` | contract-first; plan → change → test |
| Codex / ChatGPT | `codex-chatgpt` | RMD-111 | `chat` | acceptance-criteria driven; unified diff |
| Cursor | `cursor` | RMD-108 | `workspace` | patch-scoped workspace edits |
| GitPilot | `gitpilot` | RMD-113 | `git` | repository-scoped; branch + one commit |
| IBM Bob | `ibm-bob` | RMD-112 | `enterprise` | enterprise-safe boundaries; audit note |
| Generic | `generic-ai-coder` | RMD-114 | `generic` | tool-agnostic, contract-first |

Unknown coders fall back to the generic adapter (RMD-109).

## Every prompt is the same contract, spoken differently

All prompts share a fixed skeleton so the contract is identical regardless of coder:

- **Worker, not architect** (RMD-101) — implement one task only.
- **Fetch the bundle** — `GET /api/v1/bundles/{id}/download`.
- **Read the contract first** — the MATRIX control files.
- **Task + allowed files** — edit only these (RMD-002, RMD-107).
- **Hard constraints** — no edits to locked files (RMD-103), no new deps (RMD-105),
  patch-scoped (RMD-108).
- **Validate before finishing** (RMD-119) — the acceptance commands.
- **Governing rules** — the RMD-1xx rules pinned by the bundle's standards lock.
- **Stop condition** (RMD-118) — `MATRIX_STATUS: approved | needs_repair | rejected`.

Only the *workflow* and *output format* sections differ per coder.

## API

```python
pack = engine.build_prompt_pack(blueprint, bundle_id="...")     # PromptPack (all coders)
resp = engine.generate_coder_prompt_pack(bundle_id, "gitpilot", blueprint=blueprint)  # one coder
resp.handoff_mode   # "git"
```

Prompts are deterministic and are also written into the bundle under `coder-prompts/`.
