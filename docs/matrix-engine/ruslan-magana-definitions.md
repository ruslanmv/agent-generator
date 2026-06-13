# Ruslan Magana Definitions (RMD)

The **Ruslan Magana Definitions** are the public, named standard that explains *how* and *why*
the Matrix engine constrains AI coders. They are authored in
[`matrix-definitions`](https://github.com/agent-matrix/matrix-definitions) and **enforced** by
this engine. agent-generator never authors them — it loads, pins, cites, and enforces them.

> The core promise: **AI coders are workers, not architects.**

## What an RMD rule is

Each rule has a permanent id (`RMD-001`, `RMD-110`, …), a title, a severity, and an automated
check. The engine pins the applicable rules into every bundle's `MATRIX_STANDARDS.lock`, cites
them in the AI-coder prompts, and enforces them during validation.

## The rules the engine relies on

**Control principles (RMD-001–006)**

| Rule | Principle | Enforced by |
|---|---|---|
| RMD-001 | Blueprint/lock is immutable after approval | hash-lock + contract-hash check |
| RMD-002 | AI coder edits only allowed files | forbidden/allowlist check |
| RMD-003 | No new dependencies/services without an exception | dependency policy |
| RMD-004 | Failed validation must create a repair prompt | validator → repair prompt |
| RMD-005 | New dependencies require approval | dependency policy |
| RMD-006 | Diff validation is required | submission validation |

**Per-coder prompt rules (RMD-108–114)** — each AI coder gets a prompt shaped by its rule:
Claude Code (RMD-110, contract-first), Codex/ChatGPT (RMD-111, acceptance-driven), Cursor
(RMD-108, patch-scoped), GitPilot (RMD-113, repository-scoped), IBM Bob (RMD-112,
enterprise-safe), generic (RMD-114). Unsupported coders use the generic adapter (RMD-109).

**Process rules (RMD-115–120)** — architecture-drift detection before approval (RMD-115),
dependency-change approval records (RMD-116), small sequenced tasks (RMD-117), prompt stop
conditions (RMD-118, the `MATRIX_STATUS` line), mandatory validation commands (RMD-119), and
minimal bounded repair prompts (RMD-120).

## How the engine makes them real

```
matrix-definitions (authors RMD)
        │  signed pack
        ▼
agent-generator standards loader  ──►  MATRIX_STANDARDS.lock  (pins the applicable rule ids)
        │
        ├─►  prompt adapters     cite the rules the coder must obey
        └─►  validator           enforces the rules; rejects/repairs on violation
```

A generated bundle therefore *carries its own law*: the locked rules, the prompts that cite
them, and a validator that checks them. That is what turns "best practices" from advice into an
enforced contract — and what makes the Ruslan Magana Definitions a credible public standard
rather than an internal prompt collection.
