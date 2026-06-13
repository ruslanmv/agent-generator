# GitPilot — native Matrix integration

[GitPilot](https://github.com/ruslanmv/gitpilot) is a multi-agent coding assistant
(Explorer → Planner → Coder → Reviewer) with a Plan/Code/Auto loop, an MCP stack, and
workspace **rules** files. Because GitPilot loads project rules natively, Matrix integrates with
**zero extra wiring**: we emit the Matrix contract into the file GitPilot already reads.

## How it works

GitPilot loads workspace rules from (see `gitpilot/gitpilot/rules.py`):

- `<workspace>/.gitpilotrules` — single workspace rules file
- `<workspace>/.gitpilot/rules/*.md` — rules directory

The engine's GitPilot adapter (`coder_adapters/__init__.py`) sets
`helper_filename=".gitpilotrules"`, so `coder_handoff(..., coder="gitpilot")` emits the Matrix
contract — read the control files, edit only the allowlist, run the acceptance commands, end with
`MATRIX_STATUS` — straight into GitPilot's native rules path. The Explorer reads it, the Planner
plans inside it, the Coder respects the allowlist, and the Reviewer validates against it.

## Natural workflow

```bash
# 1) Plan a batch and drop the contract where GitPilot reads it
mb init "A GitHub repo intelligence agent"
mb next "Add a POST /repos/analyze endpoint with a test"
mb prompt --coder gitpilot          # writes .gitpilotrules into the repo

# 2) Run GitPilot in the same repo — it follows the contract natively
gitpilot                            # Plan mode shows a dry-run inside the allowlist; approve to Code

# 3) Validate the result against the same contract (single authority)
mb check --changed backend/app/api/repos.py backend/tests/test_repos_api.py
#   exit 0 approved · 1 needs-repair · 2 rejected
mb repair --copy                    # if not approved, hand the bounded repair prompt back to GitPilot
```

`mb sync` then pushes the batch/commit to the Matrix Builder server so the run appears in the web
Build Timeline (Track L2). GitPilot's Plan-mode dry-run mirrors Matrix's contract-first ethos, so
the two compose cleanly.

## Deeper integration (already present / roadmap)

- GitPilot ships a **MatrixLab sandbox** backend (`gitpilot/gitpilot/matrixlab_admin_api.py`,
  `/api/matrixlab/*`) and an Agent-Matrix repair path — GitPilot can run inside a Matrix-managed
  sandbox.
- **Roadmap (MCP-01):** the Matrix MCP server will expose `plan_batch / prompt / check / repair /
  commit / publish` as tools; GitPilot's MCP stack can then call Matrix directly, turning the
  contract into a live self-repair loop the agents drive themselves.

## Native MCP path

- **Today:** `mb prompt --coder gitpilot` writes `.gitpilotrules`, which GitPilot reads as
  workspace rules. Static, but already native.
- **Next (shipped in MCP-01):** GitPilot can call Matrix tools **live** through the MCP server
  (`mb mcp serve --transport stdio`) instead of only reading a file. The tool loop:
  1. `matrix_plan_batch` — plan the next bounded batch.
  2. `matrix_prompt` — emit the prompt + `.gitpilotrules` (GitPilot reads it automatically).
  3. GitPilot codes inside the allowlist.
  4. `matrix_check` — validate (`passed` / `needs_repair` / `rejected`).
  5. `matrix_repair` — bounded repair prompt, if not passed → back to step 3.
  6. `matrix_commit` — record Matrix Commit #NNN once passed.

  See `docs/mcp-01.md` for the MCP config and full tool reference.

## Verification

`tests/coder_adapters/test_helper_files.py` asserts the GitPilot handoff emits `.gitpilotrules`
with the contract; a local `mb prompt --coder gitpilot` writes it to the working tree.
