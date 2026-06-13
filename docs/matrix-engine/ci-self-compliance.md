# CI self-compliance (Batch 0)

The engine enforces the Ruslan Magana Definitions on generated projects, so it must satisfy
them itself. This documents the GHA rules as they apply to this repository.

## GHA-003 — workflow changes require human review ✅ done

`.github/CODEOWNERS` maps `/.github/workflows/`, the engine surface, the contracts package,
and packaging metadata to `@ruslanmv`. With branch protection requiring CODEOWNER review,
no workflow or contract change can merge unreviewed.

## GHA-002 — pin all actions to full commit SHAs ⏳ tooling delivered

Today every `uses:` in `.github/workflows/` is pinned to a mutable tag (e.g. `@v4`). The
audit found **89 references across 12 workflows** (28 distinct actions).

Remediation is automated and reproducible via `scripts/pin_github_actions.py`:

```bash
# CI gate — lists unpinned refs, exits non-zero if any (no network needed):
python scripts/pin_github_actions.py --check

# Apply — resolves each tag to its commit SHA and rewrites the workflows:
GITHUB_TOKEN=*** python scripts/pin_github_actions.py --apply
```

`--apply` needs an authenticated GitHub token to resolve SHAs without hitting the
unauthenticated rate limit, so the actual pinning is performed in an authenticated run
(local with a token, or a CI job) rather than committed blind with hand-typed SHAs. The
script preserves the original tag as a trailing comment, e.g.:

```yaml
- uses: actions/checkout@<40-char-sha>  # v4
```

### Recommended CI wiring

Add a job that runs `python scripts/pin_github_actions.py --check` on pull requests so the
gate fails if anyone introduces an unpinned action.

## GHA-001 — least-privilege `GITHUB_TOKEN`

Set explicit minimal `permissions:` at the workflow or job level. Tracked alongside the
pinning work; the container/release workflows already request only what they need
(`id-token: write` for attestations, `packages: write` for image push).

## Branch protection notes

Recommended settings for `master` / `main` (configure in repo settings; not expressible in
the repo tree):

- Require pull requests; require approval from CODEOWNERS.
- Require status checks: `Python CI`, the engine baseline check, and
  `pin_github_actions.py --check`.
- Require branches to be up to date before merging.
- Restrict force-pushes and deletions.
- Require signed commits (recommended for the release/standards surface).
