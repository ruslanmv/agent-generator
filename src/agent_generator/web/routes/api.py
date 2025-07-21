# ────────────────────────────────────────────────────────────────
#  src/agent_generator/web/routes/api.py
# ────────────────────────────────────────────────────────────────
"""
JSON API endpoints:

POST /api/generate
  { "prompt": "...", "framework": "crewai", "provider": "watsonx", "mcp": false }
→ { "code": "...python/yaml...", "diagram": "...mermaid..." }
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request
from pydantic import ValidationError

from agent_generator.config import Settings, get_settings
from agent_generator.frameworks import FRAMEWORKS
from agent_generator.utils.parser import parse_natural_language_to_workflow
from agent_generator.utils.visualizer import to_mermaid

api_bp = Blueprint("api", __name__)


@api_bp.post("/generate")
def generate():  # noqa: D401
    # ------------------------------------------------------------------
    # Parse request body
    # ------------------------------------------------------------------
    body = request.get_json(silent=True) or {}
    prompt = body.get("prompt", "").strip()
    framework_name = body.get("framework", "").strip()
    provider_name = body.get("provider") or get_settings().provider
    mcp = bool(body.get("mcp", False))

    if not prompt or framework_name not in FRAMEWORKS:
        return (
            jsonify({"error": "Missing prompt or unknown framework."}),
            400,
        )

    # ------------------------------------------------------------------
    # Resolve settings
    # ------------------------------------------------------------------
    try:
        settings = Settings(
            provider=provider_name,
            model=body.get("model") or get_settings().model,
            temperature=body.get("temperature") or get_settings().temperature,
            max_tokens=body.get("max_tokens") or get_settings().max_tokens,
        )
    except ValidationError as exc:
        return jsonify({"error": exc.errors()}), 400

    # ------------------------------------------------------------------
    # Build workflow spec
    # ------------------------------------------------------------------
    workflow = parse_natural_language_to_workflow(prompt)

    # ------------------------------------------------------------------
    # Render code
    # ------------------------------------------------------------------
    generator_cls = FRAMEWORKS[framework_name]
    generator = generator_cls()
    code = generator.generate_code(workflow, settings, mcp=mcp)

    # ------------------------------------------------------------------
    # Return JSON
    # ------------------------------------------------------------------
    return jsonify(
        {
            "code": code,
            "diagram": to_mermaid(workflow),
        }
    )
