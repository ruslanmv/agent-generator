# `mb` — the local-first CLI

`mb` is the **local-first Matrix Builder**: the full *git-for-AI-build-contracts* loop on your
machine — offline, deterministic, zero infrastructure. It ships inside the engine package and
mirrors the server's workflow model in a `.mb/` folder, so a session replays identically anywhere.

> `mb` is the Git of Matrix Builder; the cloud product (`build.matrixhub.io`) and MatrixHub are the
> GitHub. Same workflow — single-player vs multiplayer.

## Install

```bash
pip install agent-generator     # provides both `agent-generator` and `mb`
mb --version                    # e.g. "mb (agent-generator) 0.1.3"
```

No server, no database, no API key is needed for the local loop.

## The loop

```bash
mb init "A GitHub repo intelligence agent" --quality standard   # idea → controlled blueprint
mb next "Add repo ingestion"                                    # plan the next scoped batch
mb prompt --coder claude-code                                   # contract-bound prompt for an AI coder
# … paste the prompt into Claude Code / Cursor / Codex; it edits only the allowed files …
mb check backend/app/api/routes.py                             # validate → an immutable Matrix Commit
mb timeline                                                     # the build history
```

What each step does:

| Command | Purpose |
|---|---|
| `mb init <idea> [--quality] [--title] [--force]` | Turn an idea into a controlled blueprint and scaffold `.mb/`. `--quality` ∈ `starter \| standard \| production \| enterprise`. |
| `mb next "<goal>"` | Plan the next batch — a scoped change that declares its **allowed files** and **acceptance commands**. |
| `mb prompt [--coder] [--batch] [--copy] [--file]` | Render the contract-bound prompt and emit tool-native helpers (`CLAUDE.md`, `AGENTS.md`). `--coder` ∈ `claude \| codex \| cursor \| gitpilot \| ibm-bob \| generic`. |
| `mb check [files…] [--repo DIR] [--watch]` | Validate a change set — **fail-closed**. Exit `0` approved · `1` needs-repair · `2` rejected. |
| `mb repair [--copy]` | Turn the last failing validation into a scoped repair prompt + a fix-issue batch. |
| `mb timeline` | Show every batch and Matrix Commit in order. |
| `mb login` / `mb sync` | Authenticate and push/pull local batches & commits to the cloud (upsert-by-id). |
| `mb mcp` | Expose the build loop as MCP tools. |

## What validation enforces

```text
$ mb check backend/app/api/routes.py        # a file inside the batch allowlist
MATRIX_STATUS: approved  score=100  ·  committed mc-454fa2735cd7

$ mb check MATRIX_BLUEPRINT.yaml             # an immutable contract file
MATRIX_STATUS: rejected  ·  RMD-002: forbidden contract file modified
```

A passing check produces a **Matrix Commit** — an immutable checkpoint carrying the prompt
snapshot, the standards lock, the file manifest, the diff from its parent, and the validation
result. That is the "git for AI" primitive.

## The `.mb/` workspace

```text
.mb/
  project.json                 # version + cursors (next batch / next commit)
  blueprint.json               # the controlled blueprint (deterministically rebuilt)
  batches/NN/
    batch.json                 # the batch plan + status
    prompts/<coder>.md         # the contract-bound prompt
    prompts/CLAUDE.md          # tool-native helper file(s)
    validation.json            # the last validation report
  commits/NNN/
    manifest.json              # the immutable commit manifest
```

This on-disk layout is a 1:1 mirror of the server's workflow tables (projects, versions, batches,
prompt versions, commits, validation runs).

## Local → cloud

```bash
mb login                       # store a self-issued session token (no external IdP)
mb sync                        # push local batches/commits, pull merged state
mb check --watch <files…>      # validate server-side and tail the live run-event stream
```

See also: [Quickstart](quickstart.md) · [Public engine API (SDK)](public-engine-api.md) ·
[Validation & repair](validation-and-repair.md) · [AI coder adapters](ai-coder-adapters.md).
