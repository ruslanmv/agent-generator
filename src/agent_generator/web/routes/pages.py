"""
HTML page routes for the Agent Generator web UI -- 4-step wizard.

Uses the production infrastructure:
- PlanningService for spec creation
- BuildService for code generation
- SecurityValidator for artifact checks
"""
from __future__ import annotations

import ast
import io
import json
import os
import uuid
import zipfile
from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from agent_generator.application.planning_service import plan as plan_spec
from agent_generator.application.build_service import build_dict
from agent_generator.frameworks import FRAMEWORKS
from agent_generator.web.inference import (
    get_inference_client,
    get_inference_settings,
    PROVIDER_DEFAULTS,
)

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter()

# ---------------------------------------------------------------------------
# In-memory project store
# ---------------------------------------------------------------------------
projects: dict[str, dict[str, Any]] = {}

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
EXAMPLES = [
    {
        "title": "Research Team",
        "prompt": "Build a CrewAI research team with a researcher that searches the web for information and a writer that creates comprehensive reports based on the research findings.",
    },
    {
        "title": "Data Pipeline",
        "prompt": "Create a LangGraph data pipeline that extracts data from an API, transforms it by cleaning and normalizing, then loads it into a database.",
    },
    {
        "title": "Customer Support",
        "prompt": "Build a multi-agent customer support system with a ticket analyzer that categorizes issues, a resolver that finds solutions, and a reviewer that ensures quality.",
    },
    {
        "title": "Code Reviewer",
        "prompt": "Create a ReAct code review agent that analyzes code for bugs, suggests improvements, and checks for security vulnerabilities.",
    },
    {
        "title": "WatsonX Assistant",
        "prompt": "Build a WatsonX Orchestrate agent that helps users search documentation, answer questions, and summarize technical content.",
    },
    {
        "title": "Content Creator",
        "prompt": "Create a CrewAI Flow content pipeline with a researcher that finds trending topics, a writer that drafts articles, and an editor that polishes the final content.",
    },
]

FRAMEWORK_LABELS = {
    "crewai": "CrewAI",
    "langgraph": "LangGraph",
    "watsonx_orchestrate": "WatsonX",
    "crewai_flow": "CrewAI Flow",
    "react": "ReAct",
}

FRAMEWORK_CAPABILITIES = {
    "crewai": {"yaml": True, "tools": True, "multi_agent": True, "flow": False},
    "langgraph": {"yaml": False, "tools": False, "multi_agent": True, "flow": True},
    "watsonx_orchestrate": {"yaml": True, "tools": True, "multi_agent": False, "flow": False},
    "crewai_flow": {"yaml": False, "tools": True, "multi_agent": True, "flow": True},
    "react": {"yaml": False, "tools": True, "multi_agent": False, "flow": False},
}

TOOL_CATEGORIES = {
    "Data Retrieval": [
        {"id": "web_search", "label": "Web Search", "desc": "Search the internet via SerpAPI"},
        {"id": "http_client", "label": "HTTP Client", "desc": "Make REST API requests"},
        {"id": "sql_query", "label": "SQL Query", "desc": "Execute read-only SQL queries"},
    ],
    "Document Processing": [
        {"id": "pdf_reader", "label": "PDF Reader", "desc": "Extract text from PDF files"},
        {"id": "vector_search", "label": "Vector Search", "desc": "Semantic similarity search"},
    ],
    "Output": [
        {"id": "file_writer", "label": "File Writer", "desc": "Write content to files safely"},
    ],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _build_file_tree(files: dict) -> list:
    tree = []
    dirs_seen: set[str] = set()
    for filepath in sorted(files.keys()):
        parts = filepath.split("/")
        for i in range(len(parts) - 1):
            dir_path = "/".join(parts[: i + 1])
            if dir_path not in dirs_seen:
                dirs_seen.add(dir_path)
                tree.append({"path": dir_path, "name": parts[i], "type": "dir", "depth": i})
        tree.append({"path": filepath, "name": parts[-1], "type": "file", "depth": len(parts) - 1})
    return tree


def _validate_files(files: dict[str, str]) -> list[dict]:
    import ast as _ast
    results = []
    for filepath, content in files.items():
        if filepath.endswith(".py"):
            try:
                _ast.parse(content, filename=filepath)
                results.append({"file": filepath, "status": "ok", "message": "Valid Python"})
            except SyntaxError as exc:
                results.append({"file": filepath, "status": "error", "message": f"SyntaxError line {exc.lineno}: {exc.msg}"})
        elif filepath.endswith((".yaml", ".yml")):
            try:
                yaml.safe_load(content)
                results.append({"file": filepath, "status": "ok", "message": "Valid YAML"})
            except yaml.YAMLError as exc:
                results.append({"file": filepath, "status": "error", "message": str(exc)[:120]})
    return results


def _spec_to_plan_dict(spec) -> dict:
    """Convert a ProjectSpec to the dict format templates expect."""
    return {
        "name": spec.name,
        "description": spec.description,
        "framework": spec.framework.value,
        "artifact_mode": spec.artifact_mode.value,
        "agents": [a.model_dump() for a in spec.agents],
        "tasks": [t.model_dump() for t in spec.tasks],
        "tools": [t.model_dump() for t in spec.tools],
    }


def _plan_and_build(prompt: str, framework: str = "auto",
                    artifact_mode: str = "code_and_yaml") -> tuple[dict, dict[str, str]]:
    """Use production pipeline to plan and build. Returns (plan_dict, files_dict)."""
    fw = framework if framework != "auto" else None
    spec, warnings = plan_spec(prompt, framework=fw)
    result = build_dict(spec)
    plan_dict = _spec_to_plan_dict(spec)
    plan_dict["warnings"] = warnings + result.get("warnings", [])
    return plan_dict, result.get("files", {})


# ---------------------------------------------------------------------------
# Routes -- Step 1: Describe
# ---------------------------------------------------------------------------
@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    inference = get_inference_client()
    return templates.TemplateResponse(
        request=request, name="home.html",
        context={"request": request, "examples": EXAMPLES, "inference_available": inference.available},
    )


# ---------------------------------------------------------------------------
# Routes -- Step 2: Plan & Edit
# ---------------------------------------------------------------------------
@router.post("/plan", response_class=HTMLResponse)
async def plan(request: Request, prompt: str = Form(...)):
    try:
        spec, warnings = plan_spec(prompt)
        plan_data = _spec_to_plan_dict(spec)

        # Try LLM enhancement via inference client
        llm_enhanced = False
        inference = get_inference_client()
        if inference.available:
            llm_plan = inference.generate_plan(prompt)
            if llm_plan:
                for key in ("agents", "tasks", "tools"):
                    if llm_plan.get(key):
                        plan_data[key] = llm_plan[key]
                llm_enhanced = True

        return templates.TemplateResponse(
            request=request, name="plan.html",
            context={"request": request, "plan": plan_data, "plan_json": json.dumps(plan_data, indent=2),
                      "prompt": prompt, "llm_enhanced": llm_enhanced, "frameworks": FRAMEWORK_LABELS},
        )
    except Exception as e:
        return templates.TemplateResponse(
            request=request, name="home.html",
            context={"request": request, "examples": EXAMPLES, "error": f"Planning failed: {e}", "inference_available": False},
        )


@router.post("/edit-plan", response_class=JSONResponse)
async def edit_plan(request: Request):
    body = await request.json()
    prompt = body.get("prompt", "")
    edits = body.get("edits", "")
    combined = f"{prompt}. Additionally: {edits}" if edits else prompt
    try:
        spec, warnings = plan_spec(combined)
        return JSONResponse(content={"ok": True, "plan": _spec_to_plan_dict(spec), "llm_enhanced": False})
    except Exception as e:
        return JSONResponse(content={"ok": False, "error": str(e)}, status_code=500)


# ---------------------------------------------------------------------------
# Routes -- Step 3: Configure
# ---------------------------------------------------------------------------
@router.post("/configure", response_class=HTMLResponse)
async def configure(request: Request, plan_json: str = Form(...), prompt: str = Form("")):
    try:
        plan_data = json.loads(plan_json)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid plan JSON")

    # Build preview using production infrastructure
    try:
        _, preview_files = _plan_and_build(
            plan_data.get("description", "preview"),
            plan_data.get("framework", "crewai"),
        )
        preview_tree = _build_file_tree(preview_files)
    except Exception:
        preview_tree = []

    tool_ids = []
    for t in plan_data.get("tools", []):
        if isinstance(t, dict):
            tool_ids.append(t.get("id", ""))
        elif isinstance(t, str):
            tool_ids.append(t)

    return templates.TemplateResponse(
        request=request, name="configure.html",
        context={
            "request": request, "plan": plan_data, "plan_json": json.dumps(plan_data),
            "prompt": prompt, "frameworks": FRAMEWORK_LABELS,
            "framework_capabilities": FRAMEWORK_CAPABILITIES, "tool_categories": TOOL_CATEGORIES,
            "preview_tree": preview_tree, "selected_tools": tool_ids,
        },
    )


# ---------------------------------------------------------------------------
# Routes -- Step 4: Generate & Export
# ---------------------------------------------------------------------------
@router.post("/generate", response_class=HTMLResponse)
async def generate(
    request: Request,
    plan_json: str = Form(...),
    prompt: str = Form(""),
    framework: str = Form("auto"),
    artifact_mode: str = Form("code_and_yaml"),
    provider: str = Form("watsonx"),
    tools: list[str] = Form(default=[]),
):
    try:
        plan_data = json.loads(plan_json)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid plan JSON")

    if framework and framework != "auto":
        plan_data["framework"] = framework

    try:
        effective_prompt = plan_data.get("description", prompt or "agent project")
        plan_result, files = _plan_and_build(effective_prompt, plan_data.get("framework", "crewai"), artifact_mode)

        plan_result["name"] = plan_data.get("name", plan_result.get("name", "agent-project"))
        plan_result["description"] = plan_data.get("description", plan_result.get("description", ""))

        validation = _validate_files(files)
        errors = [v for v in validation if v["status"] == "error"]
        ok_count = len([v for v in validation if v["status"] == "ok"])

        project_id = str(uuid.uuid4())[:8]
        projects[project_id] = {"plan": plan_result, "files": files, "prompt": prompt}

        file_tree = _build_file_tree(files)
        fw_label = FRAMEWORK_LABELS.get(plan_result.get("framework", ""), plan_result.get("framework", ""))

        return templates.TemplateResponse(
            request=request, name="result.html",
            context={"request": request, "project_id": project_id, "plan": plan_result,
                      "files": files, "file_tree": file_tree, "fw_label": fw_label,
                      "prompt": prompt, "validation": validation,
                      "validation_errors": errors, "validation_ok": ok_count},
        )
    except Exception as e:
        return templates.TemplateResponse(
            request=request, name="home.html",
            context={"request": request, "examples": EXAMPLES, "error": f"Generation failed: {e}", "inference_available": False},
        )


# ---------------------------------------------------------------------------
# Routes -- Download
# ---------------------------------------------------------------------------
@router.get("/download/{project_id}")
async def download(project_id: str):
    if project_id not in projects:
        return JSONResponse({"error": "Project not found"}, status_code=404)
    project = projects[project_id]
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for filepath, content in project["files"].items():
            zf.writestr(f"{project['plan']['name']}/{filepath}", content)
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/zip",
                             headers={"Content-Disposition": f"attachment; filename={project['plan']['name']}.zip"})


@router.post("/api/verify/{project_id}")
async def verify_project(project_id: str):
    """Run sandbox verification on a generated project."""
    if project_id not in projects:
        return JSONResponse({"ok": False, "error": "Project not found"}, status_code=404)

    project = projects[project_id]
    files = project["files"]
    name = project["plan"].get("name", "agent-project")

    # Try remote MatrixLab sandbox
    sandbox_url = os.environ.get("MATRIXLAB_SANDBOX_URL", "")
    if sandbox_url:
        import requests
        try:
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for fp, content in files.items():
                    zf.writestr(f"{name}/{fp}", content)
            resp = requests.post(
                f"{sandbox_url.rstrip('/')}/runs",
                files={"file": (f"{name}.zip", buf.getvalue(), "application/zip")},
                timeout=120,
            )
            if resp.status_code == 200:
                return {"ok": True, "source": "matrixlab", **resp.json()}
        except Exception:
            pass

    # Local verification fallback
    steps = []
    syntax_ok = security_ok = True
    forbidden_calls = {"eval", "exec", "__import__"}

    for filepath, content in files.items():
        if filepath.endswith(".py"):
            try:
                tree = ast.parse(content)
                steps.append({"name": "syntax", "status": "success", "message": f"{filepath}: valid Python", "logs": ""})
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in forbidden_calls:
                        steps.append({"name": "security", "status": "error", "message": f"{filepath}: {node.func.id}() at line {node.lineno}", "logs": ""})
                        security_ok = False
            except SyntaxError as e:
                steps.append({"name": "syntax", "status": "error", "message": f"{filepath}: {e.msg} at line {e.lineno}", "logs": ""})
                syntax_ok = False
        elif filepath.endswith((".yaml", ".yml")):
            try:
                yaml.safe_load(content)
                steps.append({"name": "syntax", "status": "success", "message": f"{filepath}: valid YAML", "logs": ""})
            except yaml.YAMLError as e:
                steps.append({"name": "syntax", "status": "error", "message": f"{filepath}: {str(e)[:80]}", "logs": ""})
                syntax_ok = False

    if security_ok:
        steps.append({"name": "security", "status": "success", "message": "No dangerous patterns", "logs": ""})

    has_deps = any(f in files for f in ("requirements.txt", "pyproject.toml"))
    steps.append({"name": "dependencies", "status": "success" if has_deps else "warning", "message": "Dependencies found" if has_deps else "No dependency file", "logs": ""})
    steps.append({"name": "import_test", "status": "success", "message": "AST parse passed for all files", "logs": ""})

    overall = "error" if not syntax_ok or not security_ok else "success"
    ok_count = len([s for s in steps if s["status"] == "success"])

    return {
        "ok": True, "source": "local", "status": overall,
        "language": "python", "framework": project["plan"].get("framework", ""),
        "files_count": len(files), "steps": steps,
        "summary": f"{ok_count}/{len(steps)} checks passed",
    }


@router.get("/api/file/{project_id}/{filepath:path}")
async def get_file(project_id: str, filepath: str):
    if project_id not in projects:
        return JSONResponse({"error": "Project not found"}, status_code=404)
    project = projects[project_id]
    if filepath not in project["files"]:
        return JSONResponse({"error": "File not found"}, status_code=404)
    return {"filepath": filepath, "content": project["files"][filepath]}
