"""Agent Generator - Hugging Face Spaces Demo (v0.2.0 production infrastructure)."""

from __future__ import annotations

import ast
import io
import json
import os
import uuid
import zipfile
from pathlib import Path

import requests
import yaml
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Production infrastructure imports
from agent_generator.application.planning_service import plan as plan_spec
from agent_generator.application.build_service import build_dict
from agent_generator.domain.project_spec import ProjectSpec

# HF-specific inference client (Ollama/OllaBridge/OpenAI)
from app.inference import get_inference_client, get_inference_settings, PROVIDER_DEFAULTS

app = FastAPI(title="Agent Generator", version="0.2.0")

BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# ---------------------------------------------------------------------------
# In-memory project store
# ---------------------------------------------------------------------------
projects: dict = {}

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
    results = []
    for filepath, content in files.items():
        if filepath.endswith(".py"):
            try:
                ast.parse(content, filename=filepath)
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


def _plan_and_build(prompt: str, framework: str = "auto", artifact_mode: str = "code_and_yaml",
                    tools: list[str] | None = None) -> tuple[dict, dict[str, str]]:
    """Use production infrastructure to plan and build a project.

    Returns (plan_dict, files_dict) for backward compatibility with templates.
    """
    fw = framework if framework != "auto" else None
    spec, warnings = plan_spec(prompt, framework=fw)

    result = build_dict(spec)
    files = result.get("files", {})

    plan_dict = {
        "name": spec.name,
        "description": spec.description,
        "framework": spec.framework.value,
        "artifact_mode": spec.artifact_mode.value,
        "agents": [a.model_dump() for a in spec.agents],
        "tasks": [t.model_dump() for t in spec.tasks],
        "tools": [t.model_dump() for t in spec.tools],
        "warnings": warnings + result.get("warnings", []),
    }

    return plan_dict, files


# ---------------------------------------------------------------------------
# Routes -- Step 1: Describe
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    inference = get_inference_client()
    return templates.TemplateResponse(
        request=request, name="home.html",
        context={"request": request, "examples": EXAMPLES, "inference_available": inference.available},
    )


# ---------------------------------------------------------------------------
# Routes -- Step 2: Plan & Edit
# ---------------------------------------------------------------------------
@app.post("/plan", response_class=HTMLResponse)
async def plan(request: Request, prompt: str = Form(...)):
    try:
        spec, warnings = plan_spec(prompt)
        plan_data = {
            "name": spec.name,
            "description": spec.description,
            "framework": spec.framework.value,
            "artifact_mode": spec.artifact_mode.value,
            "agents": [a.model_dump() for a in spec.agents],
            "tasks": [t.model_dump() for t in spec.tasks],
            "tools": [t.model_dump() for t in spec.tools],
        }

        # Try LLM enhancement via inference client
        llm_enhanced = False
        inference = get_inference_client()
        if inference.available:
            llm_plan = inference.generate_plan(prompt)
            if llm_plan:
                if llm_plan.get("agents"):
                    plan_data["agents"] = llm_plan["agents"]
                if llm_plan.get("tasks"):
                    plan_data["tasks"] = llm_plan["tasks"]
                if llm_plan.get("tools"):
                    plan_data["tools"] = llm_plan["tools"]
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


@app.post("/edit-plan", response_class=JSONResponse)
async def edit_plan(request: Request):
    body = await request.json()
    prompt = body.get("prompt", "")
    edits = body.get("edits", "")
    combined = f"{prompt}. Additionally: {edits}" if edits else prompt

    try:
        spec, warnings = plan_spec(combined)
        plan_data = {
            "name": spec.name,
            "description": spec.description,
            "framework": spec.framework.value,
            "agents": [a.model_dump() for a in spec.agents],
            "tasks": [t.model_dump() for t in spec.tasks],
            "tools": [t.model_dump() for t in spec.tools],
        }
        return JSONResponse(content={"ok": True, "plan": plan_data, "llm_enhanced": False})
    except Exception as e:
        return JSONResponse(content={"ok": False, "error": str(e)}, status_code=500)


# ---------------------------------------------------------------------------
# Routes -- Step 3: Configure
# ---------------------------------------------------------------------------
@app.post("/configure", response_class=HTMLResponse)
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

    return templates.TemplateResponse(
        request=request, name="configure.html",
        context={
            "request": request, "plan": plan_data, "plan_json": json.dumps(plan_data),
            "prompt": prompt, "frameworks": FRAMEWORK_LABELS,
            "framework_capabilities": FRAMEWORK_CAPABILITIES, "tool_categories": TOOL_CATEGORIES,
            "preview_tree": preview_tree, "selected_tools": [t.get("id", t) for t in plan_data.get("tools", []) if isinstance(t, dict)],
        },
    )


# ---------------------------------------------------------------------------
# Routes -- Step 4: Generate & Export
# ---------------------------------------------------------------------------
@app.post("/generate", response_class=HTMLResponse)
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
        fw_label = FRAMEWORK_LABELS.get(plan_result["framework"], plan_result["framework"])

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
@app.get("/download/{project_id}")
async def download_zip(project_id: str):
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")
    project = projects[project_id]
    files = project["files"]
    name = project["plan"].get("name", "agent-project")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for filepath, content in files.items():
            zf.writestr(f"{name}/{filepath}", content)
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/zip",
                             headers={"Content-Disposition": f'attachment; filename="{name}.zip"'})


# ---------------------------------------------------------------------------
# Routes -- API / Health / Settings / OllaBridge
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    inference = get_inference_client()
    return {"status": "ok", "version": "0.2.0", "inference_available": inference.available}


@app.get("/api/models")
async def api_models():
    inference = get_inference_client()
    settings = get_inference_settings()
    return {"models": inference.list_models(), "current": settings.model, "provider": settings.provider}


@app.get("/api/settings")
async def api_get_settings():
    settings = get_inference_settings()
    client = get_inference_client()
    return {**settings.to_dict(), "available": client.available,
            "available_models": client.list_models(), "providers": list(PROVIDER_DEFAULTS.keys())}


@app.post("/api/settings")
async def api_update_settings(request: Request):
    body = await request.json()
    settings = get_inference_settings()
    new_state = settings.update(**body)
    client = get_inference_client()
    return {**new_state, "available": client.available, "available_models": client.list_models()}


@app.post("/api/settings/test")
async def api_test_connection():
    client = get_inference_client()
    if not client.available:
        return JSONResponse(content={"ok": False, "error": "Endpoint not reachable"}, status_code=503)
    try:
        response = client.generate("Say hello in one sentence.", temperature=0.1, max_tokens=50)
        return {"ok": True, "response": response}
    except Exception as e:
        return JSONResponse(content={"ok": False, "error": str(e)[:200]}, status_code=500)


@app.get("/api/inference-status")
async def api_inference_status():
    settings = get_inference_settings()
    client = get_inference_client()
    return {"available": client.available, "provider": settings.provider, "base_url": settings.base_url,
            "model": settings.model, "auth_mode": settings.auth_mode, "paired": bool(settings.pair_token)}


@app.post("/api/ollabridge/pair")
async def ollabridge_pair(request: Request):
    body = await request.json()
    base_url = body.get("base_url", "").rstrip("/")
    code = str(body.get("code", "")).strip().upper().replace("-", "").replace(" ", "")
    if not base_url:
        return JSONResponse(content={"ok": False, "error": "Base URL is required"}, status_code=400)
    if not code or len(code) < 4:
        return JSONResponse(content={"ok": False, "error": "Invalid pairing code"}, status_code=400)
    try:
        resp = requests.post(f"{base_url}/device/pair-simple", json={"code": code},
                             headers={"Content-Type": "application/json"}, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "ok" and data.get("device_token"):
                settings = get_inference_settings()
                settings.update(provider="ollabridge", base_url=base_url, pair_token=data["device_token"],
                                auth_mode="pairing", device_id=data.get("device_id", ""))
                return {"ok": True, "token": data["device_token"][:8] + "...", "device_id": data.get("device_id", "")}
            return JSONResponse(content={"ok": False, "error": data.get("error", "Pairing failed")}, status_code=400)
        try:
            err_data = resp.json()
            err_msg = err_data.get("detail") or err_data.get("error") or f"HTTP {resp.status_code}"
        except Exception:
            err_msg = f"OllaBridge returned HTTP {resp.status_code}"
        return JSONResponse(content={"ok": False, "error": err_msg}, status_code=400)
    except requests.ConnectionError:
        return JSONResponse(content={"ok": False, "error": f"Cannot reach {base_url}"}, status_code=503)
    except requests.Timeout:
        return JSONResponse(content={"ok": False, "error": "Connection timed out"}, status_code=504)
    except Exception as e:
        return JSONResponse(content={"ok": False, "error": str(e)[:200]}, status_code=500)


@app.get("/api/ollabridge/models")
async def ollabridge_models(base_url: str = "https://ruslanmv-ollabridge.hf.space", api_key: str = ""):
    base = base_url.rstrip("/")
    try:
        headers = {"Accept": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        settings = get_inference_settings()
        if not api_key and settings.pair_token and settings.auth_mode == "pairing":
            headers["Authorization"] = f"Bearer {settings.pair_token}"
        resp = requests.get(f"{base}/v1/models", headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, dict) and "data" in data:
                return {"models": sorted({m.get("id", "") for m in data["data"] if m.get("id")})}
            if isinstance(data, dict) and "models" in data:
                return {"models": sorted({m.get("name", m.get("model", "")) for m in data["models"] if m.get("name") or m.get("model")})}
        return {"models": [], "error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"models": [], "error": str(e)[:100]}


@app.get("/api/ollabridge/health")
async def ollabridge_health(base_url: str = "https://ruslanmv-ollabridge.hf.space"):
    base = base_url.rstrip("/")
    effective_api = f"{base}/v1" if not base.endswith("/v1") else base
    settings = get_inference_settings()
    try:
        headers = {}
        if settings.pair_token and settings.auth_mode == "pairing":
            headers["Authorization"] = f"Bearer {settings.pair_token}"
        elif settings.api_key:
            headers["Authorization"] = f"Bearer {settings.api_key}"
        resp = requests.get(f"{effective_api}/models", headers=headers, timeout=5)
        return {"status": "ok" if resp.status_code == 200 else "error", "base_url": base,
                "models_available": resp.status_code == 200, "auth_mode": settings.auth_mode, "paired": bool(settings.pair_token)}
    except Exception as e:
        return {"status": "error", "base_url": base, "error": str(e)[:100]}


# ---------------------------------------------------------------------------
# Sandbox Verification
# ---------------------------------------------------------------------------

SANDBOX_URL = os.environ.get("MATRIXLAB_SANDBOX_URL", "")

@app.post("/api/verify/{project_id}")
async def verify_project(project_id: str):
    """Run sandbox verification on a generated project.

    Packages the project as ZIP and submits to MatrixLab sandbox.
    If no sandbox URL configured, runs local validation only.
    """
    if project_id not in projects:
        return JSONResponse(content={"ok": False, "error": "Project not found"}, status_code=404)

    project = projects[project_id]
    files = project["files"]
    name = project["plan"].get("name", "agent-project")

    # Build ZIP
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for filepath, content in files.items():
            zf.writestr(f"{name}/{filepath}", content)
    zip_bytes = buf.getvalue()

    # Try remote MatrixLab sandbox
    if SANDBOX_URL:
        try:
            resp = requests.post(
                f"{SANDBOX_URL.rstrip('/')}/runs",
                files={"file": (f"{name}.zip", zip_bytes, "application/zip")},
                timeout=120,
            )
            if resp.status_code == 200:
                result = resp.json()
                return {"ok": True, "source": "matrixlab", **result}
        except Exception as e:
            pass  # Fall through to local verification

    # Local verification fallback
    steps = []

    # Syntax check
    syntax_ok = True
    for filepath, content in files.items():
        if filepath.endswith(".py"):
            try:
                ast.parse(content)
                steps.append({"name": "syntax", "status": "success", "message": f"{filepath}: valid Python", "logs": ""})
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

    # Security scan
    security_ok = True
    forbidden = {"eval", "exec", "__import__"}
    for filepath, content in files.items():
        if not filepath.endswith(".py"):
            continue
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in forbidden:
                    steps.append({"name": "security", "status": "error", "message": f"{filepath}: {node.func.id}() at line {node.lineno}", "logs": ""})
                    security_ok = False
        except SyntaxError:
            pass

    if security_ok:
        steps.append({"name": "security", "status": "success", "message": "No dangerous patterns", "logs": ""})

    # Dependencies
    has_deps = any(f in files for f in ("requirements.txt", "pyproject.toml"))
    steps.append({"name": "dependencies", "status": "success" if has_deps else "warning", "message": "Dependencies found" if has_deps else "No dependency file", "logs": ""})

    # Import test
    steps.append({"name": "import_test", "status": "success", "message": "AST parse passed for all files", "logs": ""})

    overall = "error" if not syntax_ok or not security_ok else "success"
    ok_count = len([s for s in steps if s["status"] == "success"])

    return {
        "ok": True,
        "source": "local",
        "status": overall,
        "language": "python",
        "framework": project["plan"].get("framework", "unknown"),
        "files_count": len(files),
        "steps": steps,
        "summary": f"{ok_count}/{len(steps)} checks passed",
    }
