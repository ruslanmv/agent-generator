#!/usr/bin/env bash
# run_tests.sh — run our new Matrix+Planner tests in mock or live mode

set -euo pipefail

# ─── TOGGLE HERE ──────────────────────────────────────────────────────────────
# Set to 1 to run the live Matrix smoke test (requires MATRIX_URL + MATRIX_TOKEN),
# or 0 to skip it and use only the fake-client unit tests.
USE_LIVE_MATRIX_TESTS=0
# ──────────────────────────────────────────────────────────────────────────────

if [[ "$USE_LIVE_MATRIX_TESTS" -eq 1 ]]; then
  echo "🚀  LIVE mode: real Matrix integration tests enabled"
  export RUN_MATRIX_INTEGRATION=1
else
  echo "🧪  MOCK mode: skipping live Matrix tests"
  unset RUN_MATRIX_INTEGRATION 2>/dev/null || true
fi

echo ""
echo "👉  Running Matrix connector + planning agent tests…"
pytest tests/test_matrix_connection.py tests/test_planning_agent.py -q

echo ""
echo "🎉  All tests passed in $([[ "$USE_LIVE_MATRIX_TESTS" -eq 1 ]] && echo LIVE || echo MOCK) mode!"
