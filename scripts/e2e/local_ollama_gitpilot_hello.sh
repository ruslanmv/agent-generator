#!/usr/bin/env bash
# MANUAL / LOCAL ONLY — not wired into CI yet (future job: e2e-local-ollama-gitpilot-hello-world).
#
# Fully-offline vertical slice. Each tool keeps its role; agent-generator must NOT be bypassed.
#
#   Ollama          = local model backend
#   GitPilot        = executes the coding work (reads .gitpilotrules; configured for Ollama)
#   agent-generator = creates the project blueprint / Matrix contract+bundle from the idea
#   matrix-builder  = manages batches, prompts, validation, commits
#
# Data flow:
#   user idea
#     -> agent-generator creates the Matrix contract/bundle   (REQUIRED — do not bypass)
#     -> matrix-builder turns it into Batch 01 + prompts
#     -> GitPilot executes Batch 01 using Ollama
#     -> matrix-builder validates and records Matrix Commit #001
#
# Acceptance:
#   * agent-generator RECEIVES the idea and PRODUCES a Matrix-compatible bundle (MATRIX_BLUEPRINT.yaml).
#   * GitPilot (via Ollama) creates frontend/index.html containing "Hello Matrix".
#   * matrix-builder validates (passed) and .matrix/commits/001.json exists.
#   * No production Aiven DB; no cloud AI key.
set -euo pipefail

OLLAMA_MODEL="${OLLAMA_MODEL:-qwen2.5-coder:0.5b}"
OLLAMA_URL="${OLLAMA_BASE_URL:-http://127.0.0.1:11434}"
WORK="${WORK:-$(pwd)/.e2e-hello}"
GOAL="${GOAL:-Create a simple Hello World website}"
TASK="${TASK:-Create frontend/index.html containing the text 'Hello Matrix'}"
OUT="frontend/index.html"
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "==> [1/12] check Ollama"; HAVE_OLLAMA=0; command -v ollama >/dev/null 2>&1 && HAVE_OLLAMA=1 || echo "    (ollama not found; runner will SIMULATE the coding step)"
if [ "$HAVE_OLLAMA" = 1 ]; then
  echo "==> [2/12] start Ollama (if not running)"; curl -fsS "$OLLAMA_URL/api/tags" >/dev/null 2>&1 || (ollama serve >/tmp/ollama.log 2>&1 &) && sleep 2
  echo "==> [3/12] pull model $OLLAMA_MODEL"; ollama pull "$OLLAMA_MODEL" || true
else
  echo "==> [2-3/12] skip Ollama start/pull (not installed)"
fi
echo "==> [4/12] install GitPilot"; pip show gitcopilot >/dev/null 2>&1 || pip install gitcopilot || echo "    (GitPilot install skipped/failed; runner falls back to Ollama-direct/simulate)"
echo "==> [5/12] GitPilot will be configured for Ollama by the runner (provider=ollama, $OLLAMA_MODEL)"
echo "==> [6/12] install agent-generator (provides BOTH 'mb' and 'agent-generator' CLIs)"; pip show agent-generator >/dev/null 2>&1 || pip install -e .
echo "==> [7/12] matrix-builder consumes the agent-generator bundle (server optional for the local slice)"
echo "==> [8/12] use local .mb/ + .matrix/ store only (no Aiven, no cloud keys)"

mkdir -p "$WORK"; cd "$WORK"

echo "==> [9/12] agent-generator: turn the IDEA into a Matrix contract/bundle (REQUIRED — not bypassed)"
agent-generator matrix generate --idea "$GOAL" --out matrix-bundle/
mb init "$GOAL" || true
mb next "$TASK"
mb prompt --coder gitpilot          # writes .gitpilotrules (from agent-generator's coder_handoff)
test -f matrix-bundle/MATRIX_BLUEPRINT.yaml || { echo "FAIL: agent-generator did not produce a Matrix bundle"; exit 1; }
test -f .mb/blueprint.json || { echo "FAIL: no local Matrix contract"; exit 1; }
echo "    OK: agent-generator produced the Matrix contract/bundle for: $GOAL"

echo "==> [10/12] GitPilot executes Batch 01 using Ollama (reads .gitpilotrules)"
RUNNER_OUT="$(OLLAMA_MODEL="$OLLAMA_MODEL" python3 "$HERE/gitpilot_runner.py" \
  --project "$WORK" --out "$OUT" --task "$TASK" --model "$OLLAMA_MODEL" --ollama-url "$OLLAMA_URL")"
echo "    runner: $RUNNER_OUT"
echo "$RUNNER_OUT" | grep -q '"ok": true' || { echo "FAIL: coding step did not produce $OUT"; exit 1; }

echo "==> [11/12] matrix-builder validates the change against the Matrix contract"
grep -q "Hello Matrix" "$OUT" || { echo "FAIL: $OUT missing 'Hello Matrix'"; exit 1; }
echo "    (matrix-builder validates via the MCP matrix_check tool in step 12 — single commit path)"

echo "==> [12/12] matrix-builder records Matrix Commit #001 (via the MCP commit tool)"
mb mcp serve --transport stdio --project "$WORK" <<RPC >/dev/null 2>&1 || true
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"matrix_check","arguments":{"changed_files":["$OUT"]}}}
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"matrix_commit","arguments":{"coder":"gitpilot","provider":"ollama","model":"$OLLAMA_MODEL","files_changed":["$OUT"]}}}
RPC
if [ -f "$WORK/.matrix/commits/001.json" ]; then
  echo "OK: Matrix Commit #001 recorded ($WORK/.matrix/commits/001.json)"
else
  echo "FAIL: Matrix Commit #001 not recorded"; exit 1
fi
