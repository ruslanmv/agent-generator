# Validation, drift detection, and repair (Batch 8)

`agent_generator.control` is the **single validation authority** for the Matrix ecosystem.
Matrix Builder should retire its own drift adapter and call this — the engine and the UI can
then never disagree on approve/reject.

## Inputs — one shape, many sources

The validator reduces every form of AI-coder output to a `Submission`:

| Input | Engine arg | Detail available |
|---|---|---|
| Structured request | `request=ValidationRequest(...)` | changed paths + dependency changes |
| Repository directory | `repo_path=...` | full tree (content) |
| ZIP archive | `zip_path=...` | full tree (content) |
| Unified diff | `patch="..."` | changed paths + added lines |

```python
report = engine.validate_ai_coder_patch(bundle_id, repo_path="./out", blueprint=blueprint)
```

When a `blueprint` is supplied the **full contract** is enforced; without one, the universal
checks (forbidden files, secrets) still run (backward-compatible degraded mode).

## The check set

| Check | Rule | Severity | Triggers |
|---|---|---|---|
| Forbidden / immutable file edit | RMD-002 / RMD-001 | critical | a locked file changed, or an immutable file's content drifted |
| Outside allowlist | RMD-107 | high | a changed file is not under an allowed root |
| Required file missing | DOC-001 | medium | a required bundle file is absent (full tree) |
| Denied dependency | RMD-003 | critical | a denied package was added |
| Unapproved dependency | RMD-116 | high | a new dependency beyond the baseline, no approval |
| Secret introduced | SEC-001 | critical | an API key / token / private key in changed content |
| Architecture / route drift | RMD-115 | high | submitted blueprint's routes differ from the contract |

Forbidden-file semantics are tree-aware: for a request or patch, a forbidden path is a
genuine edit (RMD-002); for a full repo/ZIP, presence is expected, so only **content drift**
of an immutable file (RMD-001) or an **added** forbidden file is flagged.

## Result

```
status:   approved | needs-repair | rejected
score:    0..100   (critical −40, high −20, medium −10)
checks:   per-policy passed/failed/skipped summaries
repair_prompt: minimal, bounded (RMD-120) — fix exactly these, nothing else
```

Status mapping: any `critical` → `rejected`; any `high`/`medium` → `needs-repair`; otherwise
`approved` (and `matrixhub_publishable = True`). A clean exported bundle validates as
`approved` against its own blueprint; tampering a locked file, adding a denied dependency, or
committing a secret flips it to `rejected` with a targeted repair prompt.

## Determinism

Given the same submission and contract, the report is byte-stable — so the UI, golden tests,
and audit records agree run to run.
