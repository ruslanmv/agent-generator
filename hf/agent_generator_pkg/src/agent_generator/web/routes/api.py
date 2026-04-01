"""
JSON API endpoints for the Agent Generator.

POST /api/plan     - Parse prompt into ProjectSpec + warnings
POST /api/build    - Take ProjectSpec and produce artifacts
POST /api/generate - Combined plan + build (backward compatible)

Settings / Inference:
GET  /api/settings          - Current LLM settings
POST /api/settings          - Update settings
POST /api/settings/test     - Test connection
GET  /api/models            - List available models
GET  /api/inference-status  - Connection status
POST /api/ollabridge/pair   - Pairing proxy
GET  /api/ollabridge/models - Models proxy
GET  /api/ollabridge/health - Health proxy
"""
from __future__ import annotations

from typing import Any, Optional

import requests as http_requests
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError

from agent_generator.application.planning_service import plan as plan_spec
from agent_generator.application.build_service import build_dict
from agent_generator.config import Settings, get_settings
from agent_generator.frameworks import FRAMEWORKS
from agent_generator.web.inference import (
    get_inference_client,
    get_inference_settings,
    PROVIDER_DEFAULTS,
)

router = APIRouter()


# ── Request / Response Models ────────────────────────────────────

class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Natural language description of the agent team.")
    framework: str = Field(default="crewai", description="Framework: crewai, crewai_flow, langgraph, react, watsonx_orchestrate")
    provider: Optional[str] = Field(default=None, description="LLM provider: watsonx or openai")
    model: Optional[str] = Field(default=None, description="Model identifier override")
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    mcp: bool = Field(default=False, description="Enable MCP HTTP wrapper")
    artifact_mode: str = Field(default="code_only", description="code_only, yaml_only, or code_and_yaml")
    tools: list[str] = Field(default_factory=list, description="Tool IDs to include")


class PlanRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    framework: str = Field(default="crewai")
    artifact_mode: str = Field(default="code_only")
    tools: list[str] = Field(default_factory=list)


class AgentInfo(BaseModel):
    role: str
    goal: str
    tools: list[str] = Field(default_factory=list)


class TaskInfo(BaseModel):
    description: str
    agent_role: str
    expected_output: str = ""
    depends_on: list[str] = Field(default_factory=list)


class ProjectPlan(BaseModel):
    name: str
    description: str
    framework: str
    artifact_mode: str
    agents: list[AgentInfo]
    tasks: list[TaskInfo]
    warnings: list[str] = Field(default_factory=list)


class BuildRequest(BaseModel):
    plan: ProjectPlan
    provider: Optional[str] = Field(default=None)
    model: Optional[str] = Field(default=None)
    temperature: Optional[float] = Field(default=None)
    mcp: bool = Field(default=False)


class FileArtifact(BaseModel):
    path: str
    content: str
    language: str = "python"


class BuildResponse(BaseModel):
    project_name: str
    framework: str
    files: list[FileArtifact]
    diagram: str = ""
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    validation_passed: bool = True


class GenerateResponse(BaseModel):
    code: str
    diagram: str
    framework: str = ""
    warnings: list[str] = Field(default_factory=list)


# ── Core Endpoints ──────────────────────────────────────────────

@router.post("/plan", response_model=ProjectPlan)
async def plan(req: PlanRequest):
    """Parse a natural language prompt into a structured project plan."""
    prompt = req.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required.")

    fw = req.framework if req.framework in FRAMEWORKS else None
    spec, warnings = plan_spec(prompt, framework=fw)

    agents = [AgentInfo(role=a.role, goal=a.goal, tools=a.tools) for a in spec.agents]
    tasks = [TaskInfo(description=t.description, agent_role=t.agent_id,
                      expected_output=t.expected_output, depends_on=t.depends_on) for t in spec.tasks]

    return ProjectPlan(
        name=spec.name,
        description=spec.description,
        framework=spec.framework.value,
        artifact_mode=req.artifact_mode or spec.artifact_mode.value,
        agents=agents,
        tasks=tasks,
        warnings=warnings,
    )


@router.post("/build", response_model=BuildResponse)
async def build(req: BuildRequest):
    """Take a structured plan and produce code artifacts."""
    p = req.plan
    fw = p.framework if p.framework in FRAMEWORKS else "crewai"

    spec, _ = plan_spec(p.description, framework=fw)
    result = build_dict(spec, mcp=req.mcp)

    files = [FileArtifact(path=path, content=content, language="python" if path.endswith(".py") else "yaml")
             for path, content in result.get("files", {}).items()]

    return BuildResponse(
        project_name=spec.name,
        framework=fw,
        files=files,
        diagram=result.get("diagram", ""),
        errors=result.get("errors", []),
        warnings=result.get("warnings", []) + list(p.warnings),
        validation_passed=result.get("valid", True),
    )


@router.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    """Combined plan + build endpoint (backward compatible)."""
    prompt = req.prompt.strip()
    fw = req.framework.strip() if req.framework.strip() in FRAMEWORKS else None

    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required.")

    spec, warnings = plan_spec(prompt, framework=fw)
    result = build_dict(spec, mcp=req.mcp)

    # Pick the main code file
    code = ""
    for path, content in result.get("files", {}).items():
        if path.endswith((".py", ".yaml")) and ("main" in path or path.endswith(".yaml")):
            code = content
            break
    if not code:
        code = next(iter(result.get("files", {}).values()), "")

    return GenerateResponse(
        code=code,
        diagram=result.get("diagram", ""),
        framework=spec.framework.value,
        warnings=warnings + result.get("warnings", []),
    )


# ── Settings / Inference Endpoints ──────────────────────────────

@router.get("/models")
async def api_models():
    """List available LLM models."""
    inference = get_inference_client()
    models = inference.list_models()
    settings = get_inference_settings()
    return {"models": models, "current": settings.model, "provider": settings.provider}


@router.get("/settings")
async def api_get_settings():
    """Get current LLM settings."""
    settings = get_inference_settings()
    client = get_inference_client()
    return {
        **settings.to_dict(),
        "available": client.available,
        "available_models": client.list_models(),
        "providers": list(PROVIDER_DEFAULTS.keys()),
    }


@router.post("/settings")
async def api_update_settings(request: Request):
    """Update LLM settings (provider, model, base_url, api_key, temperature, max_tokens)."""
    body = await request.json()
    settings = get_inference_settings()
    new_state = settings.update(**body)
    client = get_inference_client()
    return {
        **new_state,
        "available": client.available,
        "available_models": client.list_models(),
    }


@router.post("/settings/test")
async def api_test_connection():
    """Test the current LLM connection with a simple prompt."""
    client = get_inference_client()
    if not client.available:
        return JSONResponse(
            content={"ok": False, "error": "Endpoint not reachable"},
            status_code=503,
        )
    try:
        response = client.generate("Say hello in one sentence.", temperature=0.1, max_tokens=50)
        return {"ok": True, "response": response}
    except Exception as e:
        return JSONResponse(
            content={"ok": False, "error": str(e)[:200]},
            status_code=500,
        )


@router.get("/inference-status")
async def api_inference_status():
    """Check if inference is connected."""
    settings = get_inference_settings()
    client = get_inference_client()
    available = client.available
    return {
        "available": available,
        "provider": settings.provider,
        "base_url": settings.base_url,
        "model": settings.model,
        "auth_mode": settings.auth_mode,
        "paired": bool(settings.pair_token),
    }


# ── OllaBridge Pairing Proxy ────────────────────────────────────

@router.post("/ollabridge/pair")
async def ollabridge_pair(request: Request):
    """Proxy device pairing request to OllaBridge Cloud."""
    body = await request.json()
    base_url = body.get("base_url", "").rstrip("/")
    code = str(body.get("code", "")).strip().upper().replace("-", "").replace(" ", "")

    if not base_url:
        return JSONResponse(content={"ok": False, "error": "Base URL is required"}, status_code=400)
    if not code or len(code) < 4:
        return JSONResponse(content={"ok": False, "error": "Invalid pairing code"}, status_code=400)

    try:
        resp = http_requests.post(
            f"{base_url}/device/pair-simple",
            json={"code": code},
            headers={"Content-Type": "application/json"},
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "ok" and data.get("device_token"):
                settings = get_inference_settings()
                settings.update(
                    provider="ollabridge",
                    base_url=base_url,
                    pair_token=data["device_token"],
                    auth_mode="pairing",
                    device_id=data.get("device_id", ""),
                )
                return {
                    "ok": True,
                    "token": data["device_token"][:8] + "...",
                    "device_id": data.get("device_id", ""),
                }
            return JSONResponse(
                content={"ok": False, "error": data.get("error", "Pairing failed")},
                status_code=400,
            )
        try:
            err_data = resp.json()
            err_msg = err_data.get("detail") or err_data.get("error") or f"HTTP {resp.status_code}"
        except Exception:
            if resp.status_code == 503:
                err_msg = "OllaBridge is starting up. Try again in a moment."
            else:
                err_msg = f"OllaBridge returned HTTP {resp.status_code}"
        return JSONResponse(content={"ok": False, "error": err_msg}, status_code=400)
    except http_requests.ConnectionError:
        return JSONResponse(content={"ok": False, "error": f"Cannot reach {base_url}"}, status_code=503)
    except http_requests.Timeout:
        return JSONResponse(content={"ok": False, "error": "Connection timed out"}, status_code=504)
    except Exception as e:
        return JSONResponse(content={"ok": False, "error": str(e)[:200]}, status_code=500)


@router.get("/ollabridge/models")
async def ollabridge_models(base_url: str = "https://ruslanmv-ollabridge.hf.space", api_key: str = ""):
    """Proxy model listing to an OllaBridge instance."""
    base = base_url.rstrip("/")
    try:
        headers = {"Accept": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        settings = get_inference_settings()
        if not api_key and settings.pair_token and settings.auth_mode == "pairing":
            headers["Authorization"] = f"Bearer {settings.pair_token}"

        resp = http_requests.get(f"{base}/v1/models", headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, dict) and "data" in data:
                models = sorted({m.get("id", "") for m in data["data"] if m.get("id")})
                return {"models": models}
            if isinstance(data, dict) and "models" in data:
                models = sorted({
                    m.get("name", m.get("model", ""))
                    for m in data["models"]
                    if m.get("name") or m.get("model")
                })
                return {"models": models}
        return {"models": [], "error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"models": [], "error": str(e)[:100]}


@router.get("/ollabridge/health")
async def ollabridge_health(base_url: str = "https://ruslanmv-ollabridge.hf.space"):
    """Check OllaBridge health."""
    base = base_url.rstrip("/")
    effective_api = f"{base}/v1" if not base.endswith("/v1") else base
    settings = get_inference_settings()
    try:
        headers = {}
        if settings.pair_token and settings.auth_mode == "pairing":
            headers["Authorization"] = f"Bearer {settings.pair_token}"
        elif settings.api_key:
            headers["Authorization"] = f"Bearer {settings.api_key}"
        resp = http_requests.get(f"{effective_api}/models", headers=headers, timeout=5)
        return {
            "status": "ok" if resp.status_code == 200 else "error",
            "base_url": base,
            "models_available": resp.status_code == 200,
            "auth_mode": settings.auth_mode,
            "paired": bool(settings.pair_token),
        }
    except Exception as e:
        return {"status": "error", "base_url": base, "error": str(e)[:100]}
