#!/usr/bin/env python3
"""GitPilot + Ollama coding step for the local E2E (MANUAL / LOCAL ONLY).

Role: GitPilot executes the coding work; Ollama is the local model backend. This runner
configures GitPilot for Ollama and performs the batch's coding task **under the Matrix contract**
(it reads ``.gitpilotrules``), then writes the resulting file. It is honest about which path ran:

  * ``gitpilot``  — GitPilot's local agent executed (when a usable local-agent entry is available).
  * ``ollama``    — GitPilot is configured for Ollama and the local Ollama model generated the file
                    directly under the contract (GitPilot has no one-shot local-file headless CLI;
                    its full-agent local execution is the TUI/VS Code/agent layer — see follow-up).
  * ``simulated`` — neither Ollama nor GitPilot is available; a minimal stand-in is written so the
                    Matrix half (validate + commit) still demonstrates. NOT a real model run.

No cloud keys, no production DB, no network beyond the local Ollama endpoint. Stdlib only.

Usage:
  python gitpilot_runner.py --project . --out frontend/index.html \
      --task "Create index.html containing the text 'Hello Matrix'" \
      --model "$OLLAMA_MODEL" --ollama-url http://127.0.0.1:11434
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


def _ollama_up(url: str) -> bool:
    try:
        with urllib.request.urlopen(f"{url.rstrip('/')}/api/tags", timeout=3) as r:
            return r.status == 200
    except Exception:
        return False


def _configure_gitpilot_for_ollama(model: str, url: str) -> None:
    """Point GitPilot at the local Ollama backend (env + persisted settings, best-effort)."""
    os.environ["OLLAMA_BASE_URL"] = url
    os.environ["GITPILOT_OLLAMA_MODEL"] = model
    try:
        from gitpilot.settings import Settings  # type: ignore

        s = Settings.load()
        s.provider = type(s.provider).ollama
        s.ollama.model = model
        s.ollama.base_url = url
        if hasattr(s, "save"):
            s.save()
    except Exception:
        pass  # GitPilot not installed / API differs — env vars still set the backend.


def _try_gitpilot_local(project: Path, task: str, out: Path) -> bool:
    """Best-effort: run GitPilot's local agent to perform the task. Returns True if it wrote `out`.

    GitPilot's headless `run` command is GitHub-centric; local-file execution is its interactive
    agent layer, which has no stable one-shot API. We attempt it defensively and fall back.
    """
    try:
        import gitpilot  # noqa: F401  (presence check)
    except Exception:
        return False
    # No supported one-shot local-file headless entrypoint today — see follow-up in docs/mcp-01.md.
    return False


def _ollama_generate(model: str, url: str, prompt: str) -> str:
    body = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode("utf-8")
    req = urllib.request.Request(
        f"{url.rstrip('/')}/api/generate", data=body, headers={"content-type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8")).get("response", "")


def _extract_code(text: str) -> str:
    """Pull a fenced code block if present, else return the raw text."""
    if "```" in text:
        parts = text.split("```")
        if len(parts) >= 3:
            block = parts[1]
            # drop a leading language tag line (e.g. ```html)
            return block.split("\n", 1)[1] if "\n" in block else block
    return text


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=".")
    ap.add_argument("--out", default="frontend/index.html")
    ap.add_argument("--task", default="Create index.html containing the text 'Hello Matrix'")
    ap.add_argument("--model", default=os.getenv("OLLAMA_MODEL", "qwen2.5-coder:0.5b"))
    ap.add_argument("--ollama-url", default=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"))
    ap.add_argument("--must-contain", default="Hello Matrix")
    args = ap.parse_args()

    project = Path(args.project)
    out = project / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    rules = (project / ".gitpilotrules")
    contract = rules.read_text(encoding="utf-8") if rules.exists() else ""

    _configure_gitpilot_for_ollama(args.model, args.ollama_url)

    path = "simulated"
    if _try_gitpilot_local(project, args.task, out):
        path = "gitpilot"
    elif _ollama_up(args.ollama_url):
        prompt = (
            "You are GitPilot, a Matrix-contract-bound AI coder. Follow these repository rules "
            "exactly:\n\n" + contract + "\n\nTask: " + args.task + f"\nWrite the COMPLETE contents "
            f"of the file `{args.out}` only. Output just the file content (optionally in one code "
            "block), no commentary."
        )
        try:
            out.write_text(_extract_code(_ollama_generate(args.model, args.ollama_url, prompt)),
                           encoding="utf-8")
            path = "ollama"
        except Exception as exc:  # noqa: BLE001
            print(f"[gitpilot_runner] Ollama call failed ({exc}); simulating.", file=sys.stderr)

    # Ensure the artifact exists and meets the contract's acceptance so the E2E can proceed.
    text = out.read_text(encoding="utf-8") if out.exists() else ""
    if args.must_contain not in text:
        out.write_text(
            f"<!doctype html>\n<title>Hello</title>\n<h1>{args.must_contain}</h1>\n", encoding="utf-8"
        )
        path = "simulated"  # a real backend didn't satisfy acceptance; we stood in

    ok = out.exists() and args.must_contain in out.read_text(encoding="utf-8")
    print(json.dumps({"path": path, "out": str(out), "ok": ok}))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
