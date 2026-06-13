# Controlled blueprint compiler + regeneration (Batch 5)

Batch 5 turns a selected blueprint into a complete, deterministic, hash-locked file plan, and
adds versioned regeneration — the engine capability behind Matrix Builder's "Update
requirements" page.

## The compiler

`engine.compile_bundle(blueprint, *, version, preferred_coder)` returns a `CompiledBundle`:
the full set of files a Matrix Bundle ZIP is built from.

```
CompiledBundle
├── MATRIX_BLUEPRINT.yaml          control · immutable
├── MATRIX_STANDARDS.lock          control · immutable
├── MATRIX_TASKS.md                control
├── MATRIX_ALLOWED_CHANGES.md      control
├── MATRIX_ACCEPTANCE_CRITERIA.md  control
├── MATRIX_VALIDATION.md           control
├── README.md, docs/*.md           doc
├── .env.example, .gitignore, …    config
├── backend/…, frontend/…, worker/ scaffold  (stack-aware, runnable health route + test)
├── coder-prompts/*.md             prompt
└── artifacts/manifest.json        manifest  (every file + digest + contract hash)
```

Every file carries a `sha256:` content digest. The compiler is deterministic: the same
blueprint, pack, and pinned clock produce a byte-identical bundle.

## Hash-locking (the blueprint contract)

The two immutable files — `MATRIX_BLUEPRINT.yaml` and `MATRIX_STANDARDS.lock` — are hashed
into a single order-independent **contract hash** (`agent_generator.control.contract`). It is
recorded in `artifacts/manifest.json`. The validator (Batch 8) recomputes it to detect any
post-approval tampering with the locked contract surface (rule RMD-001).

## Versioned regeneration

`engine.regenerate(base_blueprint, change_request, change_type, *, current_version)` produces
a **new** blueprint version without mutating the base — a pure function. The caller persists
the old version unchanged and stores the new one.

| `change_type` | Semver bump | Example |
|---|---|---|
| `small-update` | patch (1.0.0 → 1.0.1) | "Tweak the report wording" |
| `add-feature` | minor (1.0.0 → 1.1.0) | "Add authentication and a dashboard" |
| `change-architecture` | major (1.0.0 → 2.0.0) | "Switch the database to MongoDB" |

Change detection is deterministic regex analysis (no LLM): it derives new tasks, pages,
routes, and stack adjustments, and a human-readable `change_summary`. For example,
"Add authentication, a user dashboard, and protected API routes" yields:

```
1.0.0 → v1.1.0
change_summary: [Add authentication, Add dashboard page, Add protected API routes, Update prompt pack]
new tasks: 5 (was 3) · stack.auth: session · pages += /dashboard, /login
routes += POST /api/v1/auth/login, POST /api/v1/auth/logout
```

The returned `RegenerationResult` carries `blueprint`, `version`, `previous_version`,
`change_type`, and `change_summary` — everything Matrix Builder's "Update requirements" page
and `bundle_versions` table need. `ChangeType` wire values match the UI's three buttons.

## Golden snapshots

`tests/golden/` pins the exact rendered file plan for the GitHub flagship template, so any
unintended change to the compiler, control files, scaffold, prompts, or standards lock is
caught in review. Refresh intentionally with:

```bash
UPDATE_GOLDEN=1 pytest tests/golden -q
```

## Export

`export_zip` now builds the archive from the compiler's file map (sorted paths, fixed
timestamps) — byte-deterministic, which is what makes version diffs and golden tests
trustworthy. `generate_matrix_bundle`'s file list and `manifest_digest` are the compiler's
real files and contract hash. Batch 6 adds SBOM and signatures on top of this plan.
