# ────────────────────────────────────────────────────────────────
#  src/agent_generator/web/routes/main.py
# ────────────────────────────────────────────────────────────────
"""
HTML routes – minimal UI rendered via Jinja2 templates.
"""

from __future__ import annotations

from flask import Blueprint, render_template, request

main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def index():  # noqa: D401
    return render_template("index.html")


@main_bp.post("/generate")
def generate_form():  # noqa: D401
    prompt = request.form.get("prompt") or ""
    framework = request.form.get("framework") or "crewai"
    provider = request.form.get("provider") or "watsonx"
    mcp = bool(request.form.get("mcp"))

    # Delegate to JSON API internally
    from flask import current_app

    with current_app.test_client() as client:
        resp = client.post(
            "/api/generate",
            json={
                "prompt": prompt,
                "framework": framework,
                "provider": provider,
                "mcp": mcp,
            },
        )
        if resp.status_code != 200:
            error = resp.json.get("error", "Generation failed")
            return render_template("index.html", error=error, form=request.form)

        data = resp.get_json()
        return render_template(
            "visualization.html",
            code=data["code"],
            diagram=data["diagram"],
            framework=framework,
        )
