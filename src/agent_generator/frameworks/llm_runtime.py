"""Shared runtime snippet injected into generated single-file agents.

The generators embed :data:`LLM_HELPER_SNIPPET` verbatim so the produced agent can
call any OpenAI-compatible chat endpoint — a local OllaBridge gateway, a bare Ollama
daemon, or OpenAI — with **zero extra dependencies** (standard library only).

The helper is configured entirely from the environment and fails soft (returns an empty
string) so generated code keeps working offline and never crashes when no model is
reachable. Callers fall back to their deterministic behaviour on an empty reply.
"""

from __future__ import annotations

# NOTE: emitted into generated files as-is. Keep it at column 0 (module-level
# statements) and free of Jinja-significant tokens ({{ }} / {% %} / {# #}).
LLM_HELPER_SNIPPET = '''
# ─────────────────────────────────────────────────────────
# LLM client — OpenAI-compatible (OllaBridge / Ollama / OpenAI)
# ─────────────────────────────────────────────────────────
import os as _os
import json as _json
import urllib.request as _urlreq


def _llm(prompt: str, system: str | None = None) -> str:
    """Call an OpenAI-compatible chat endpoint; return the reply text.

    Configured from the environment so the same agent runs against a local
    OllaBridge gateway, a bare Ollama daemon, or OpenAI:

        OLLABRIDGE_URL   / OPENAI_API_BASE     base URL (default: public OllaBridge)
        OLLABRIDGE_MODEL / OPENAI_MODEL_NAME   model id (default: qwen2.5:1.5b)
        OLLABRIDGE_TOKEN / OPENAI_API_KEY      bearer token (optional)

    Returns "" on any failure so callers can fall back to offline behaviour.
    """
    base = (
        _os.getenv("OLLABRIDGE_URL")
        or _os.getenv("OPENAI_API_BASE")
        or "https://ruslanmv-ollabridge.hf.space"
    ).rstrip("/")
    if not base.endswith("/v1"):
        base += "/v1"
    model = (
        _os.getenv("OLLABRIDGE_MODEL") or _os.getenv("OPENAI_MODEL_NAME") or "qwen2.5:1.5b"
    )
    if model.startswith("openai/"):
        model = model.split("/", 1)[1]
    token = _os.getenv("OLLABRIDGE_TOKEN") or _os.getenv("OPENAI_API_KEY")
    messages = [{"role": "system", "content": system}] if system else []
    messages.append({"role": "user", "content": prompt})
    payload = _json.dumps(
        {"model": model, "messages": messages, "temperature": 0.2, "stream": False}
    ).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = _urlreq.Request(base + "/chat/completions", data=payload, headers=headers)
    try:
        with _urlreq.urlopen(req, timeout=120) as resp:
            data = _json.loads(resp.read().decode("utf-8"))
        return (data["choices"][0]["message"]["content"] or "").strip()
    except Exception:
        return ""
'''.strip("\n")
