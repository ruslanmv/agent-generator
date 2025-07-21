#!/usr/bin/env bash
# ────────────────────────────────────────────────────────────────
#  scripts/ci_helpers.sh
# ────────────────────────────────────────────────────────────────
#
#  Small Bash helpers used by GitHub Actions.
#
#  Usage:
#     ./scripts/ci_helpers.sh check-changelog
#     ./scripts/ci_helpers.sh list-todos
#
#  Add more sub‑commands as CI needs evolve.
# ----------------------------------------------------------------
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# ----------------------------------------------------------------
#  Helper: extract version from pyproject.toml
# ----------------------------------------------------------------
get_version() {
  grep -E '^[[:space:]]*version[[:space:]]*=' "$REPO_ROOT/pyproject.toml" \
    | head -n 1 \
    | sed -E 's/.*"([^"]+)".*/\1/'
}

# ----------------------------------------------------------------
#  1. Ensure CHANGELOG.md has an entry for the current version
# ----------------------------------------------------------------
check_changelog() {
  version="$(get_version)"
  if ! grep -q "## \\[${version}\\]" "$REPO_ROOT/CHANGELOG.md"; then
    echo "❌  CHANGELOG.md missing entry for version ${version}"
    exit 1
  fi
  echo "✓ CHANGELOG has entry for ${version}"
}

# ----------------------------------------------------------------
#  2. List TODO / FIXME comments (non‑fatal)
# ----------------------------------------------------------------
list_todos() {
  echo "🔍  TODO / FIXME scan:"
  grep -R --line-number --color=always -E "TODO|FIXME" \
    "$REPO_ROOT/src" || true
}

# ----------------------------------------------------------------
#  Dispatch
# ----------------------------------------------------------------
cmd="${1:-}"
case "$cmd" in
  check-changelog) check_changelog ;;
  list-todos)      list_todos ;;
  *)
    echo "Usage: $0 {check-changelog|list-todos}" >&2
    exit 2
    ;;
esac
