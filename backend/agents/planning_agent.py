# backend/agents/planning_agent.py
"""
Planner (AI) for agent-generator.

Goals
-----
- Produce a **structured plan** the builders can consume (framework, agents, tools, project_tree).
- Prefer **existing** assets discovered via the Matrix Python SDK (agents, tools, code).
- Use a **BeeAI tool-calling agent** with a strict Pydantic schema to converge quickly.
- Remain **resilient**: if the loop cannot converge within a few iterations,
  return a deterministic **fallback** plan (optionally using discovered Matrix assets).
- Avoid noisy traces (e.g., aiohttp "Unclosed client session") by keeping this module
  free of long-lived sessions; orchestration cleanup should be handled by the proxy.

This module exposes:
    - `plan(use_case, preferred_framework=None, mcp_catalog=None) -> dict`
      Async entrypoint used by the OrchestratorProxy.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

# ── Import shims for BeeAI: support multiple SDK layouts & “no SDK” case ─────
ToolCallingAgent: Any
BaseTool: Any

try:
    # Newer layouts first
    from beeai_framework.agents.tool_calling.agent import ToolCallingAgent  # type: ignore
except Exception:
    ToolCallingAgent = None  # will trigger deterministic fallback

try:
    # Some versions expose BaseTool in package root
    from beeai_framework.tools import BaseTool  # type: ignore
except Exception:
    try:
        # Older versions
        from beeai_framework.tools.base import BaseTool  # type: ignore
    except Exception:
        # Minimal shim so our tools still type-check and run in fallback mode
        class BaseTool:  # type: ignore[no-redef]
            name: str = "tool"
            description: str = ""

            async def __call__(self, *_args, **_kwargs):  # pragma: no cover
                raise NotImplementedError("BaseTool call not implemented (shim).")

# Matrix connector (optional, failure-tolerant)
from agent_generator.integrations.matrix_connector import MatrixConnector

# LLM provider settings
from agent_generator.config import Settings


# ──────────────────────────────────────────────────────────────────────────────
# Structured outputs (kept tight to force convergence)
# ──────────────────────────────────────────────────────────────────────────────

class PlannedTool(BaseModel):
    name: str
    kind: str = Field(description="python|mcp|http|js|yaml")
    description: Optional[str] = None
    entrypoint: Optional[str] = None  # module:func for py, URL for HTTP, mcp id, etc.


class PlannedAgent(BaseModel):
    name: str
    role: str
    goals: List[str]


class LLMPlanOutput(BaseModel):
    framework: str
    constraints: List[str] = Field(default_factory=list)
    agents: List[PlannedAgent] = Field(default_factory=list)
    tools: List[PlannedTool] = Field(default_factory=list)
    project_tree: List[str] = Field(default_factory=list)
    notes: Optional[str] = None

    @field_validator("framework")
    @classmethod
    def _normalize_framework(cls, v: str) -> str:
        return (v or "").strip().lower()


# ──────────────────────────────────────────────────────────────────────────────
# Minimal BeeAI tools (pure Python, no network)
# ──────────────────────────────────────────────────────────────────────────────

class FrameworkSelectorTool(BaseTool):
    name = "framework_selector"
    description = "Select best framework from {watsonx_orchestrate, crewai, langgraph, beeai, react}."

    async def __call__(
        self, _context=None, *, use_case: str, preferred: Optional[str] = None
    ) -> str:  # type: ignore[override]
        preferred = (preferred or "").strip().lower()
        candidates = {"watsonx_orchestrate", "crewai", "langgraph", "beeai", "react"}
        if preferred in candidates:
            return preferred
        uc = (use_case or "").lower()
        if "orchestrate" in uc or "skill" in uc or "watsonx" in uc:
            return "watsonx_orchestrate"
        if "ui" in uc or "frontend" in uc or "react" in uc:
            return "react"
        if "graph" in uc or "state" in uc:
            return "langgraph"
        if "beeai" in uc:
            return "beeai"
        return "crewai"


class TaskDecomposerTool(BaseTool):
    name = "task_decomposer"
    description = "Decompose the use case into 2-5 agents with names, roles, and 2-4 goals."

    async def __call__(self, _context=None, *, use_case: str) -> List[Dict[str, Any]]:  # type: ignore[override]
        uc = (use_case or "").lower()
        agents: List[Dict[str, Any]] = []
        if any(k in uc for k in ("search", "google", "bing", "web")):
            agents.append({"name": "Searcher", "role": "Web search specialist", "goals": ["Query the web", "Collect credible sources"]})
            agents.append({"name": "Synthesizer", "role": "Summarize and synthesize findings", "goals": ["Remove duplicates", "Produce concise answers"]})
        else:
            agents.append({"name": "Planner", "role": "Define steps to solve the task", "goals": ["Create sub-tasks", "Track progress"]})
            agents.append({"name": "Executor", "role": "Run tools to complete sub-tasks", "goals": ["Call tools", "Return results"]})
        return agents


class ToolCatalogBuilder(BaseTool):
    name = "tool_catalog_builder"
    description = "List minimal tools (python/http/mcp) required to complete the use case."

    async def __call__(self, _context=None, *, use_case: str) -> List[Dict[str, Any]]:  # type: ignore[override]
        uc = (use_case or "").lower()
        if "search" in uc or "google" in uc:
            return [
                {"name": "http_get", "kind": "http", "description": "Perform HTTP GET requests", "entrypoint": "GET"},
                {"name": "search_results_parser", "kind": "python", "description": "Parse and rank results", "entrypoint": "tools.search:parse_results"},
            ]
        return [{"name": "py_tool", "kind": "python", "description": "Generic Python tool", "entrypoint": "tools.common:run"}]


class FileTreePlanner(BaseTool):
    name = "file_tree_planner"
    description = "Return a list of file paths that should exist in the final project."

    async def __call__(self, _context=None, *, framework: str) -> List[str]:  # type: ignore[override]
        return _plan_file_tree(framework)


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class PlanRequest:
    use_case: str
    preferred_framework: Optional[str] = None
    mcp_catalog: Dict[str, Any] | None = None


async def plan(
    use_case: str,
    preferred_framework: Optional[str] = None,
    mcp_catalog: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    req = PlanRequest(
        use_case=use_case,
        preferred_framework=preferred_framework,
        mcp_catalog=mcp_catalog or {},
    )
    return await _run_planner(req)


# ──────────────────────────────────────────────────────────────────────────────
# Core planner
# ──────────────────────────────────────────────────────────────────────────────

async def _run_planner(req: PlanRequest) -> Dict[str, Any]:
    # 0) Discover Matrix assets (failure-tolerant)
    matrix = MatrixConnector()
    discovered_agents = matrix.list_agents(query=req.use_case) if matrix.healthy() else []
    discovered_tools = matrix.list_tools(query=req.use_case) if matrix.healthy() else []

    # If BeeAI planner isn't importable, return a deterministic plan that still uses Matrix
    if ToolCallingAgent is None:
        return await _fallback_plan_with_matrix(req, discovered_agents, discovered_tools)

    # ─── choose LLM based on AGENTGEN_PROVIDER (defaults to watsonx) ────────────
    settings = Settings()
    provider = settings.agentgen_provider.lower()  # alias to `provider`

    if provider == "watsonx":
        # beeai_framework 0.1.32 location & class name
        # beeai_framework.adapters.watsonx.backend.chat.WatsonxChatModel
        from beeai_framework.adapters.watsonx.backend.chat import WatsonxChatModel

        llm = WatsonxChatModel(
            model_id=settings.model,            # note: model_id (not model)
            api_key=settings.watsonx_api_key,
            project_id=settings.watsonx_project_id,
            base_url=settings.watsonx_url,
            temperature=settings.temperature,   # accepted via **kwargs
        )
    else:
        # beeai_framework 0.1.32 location
        # beeai_framework.adapters.openai.backend.chat.OpenAIChatModel
        from beeai_framework.adapters.openai.backend.chat import OpenAIChatModel

        llm = OpenAIChatModel(
            model_id=settings.model,            # note: model_id (not model)
            api_key=getattr(settings, "openai_api_key", None),
            temperature=settings.temperature,
        )

    # Compose a bounded, schema-driven BeeAI planner
    agent = ToolCallingAgent(
        llm=llm,
        tools=[
            FrameworkSelectorTool(),
            TaskDecomposerTool(),
            ToolCatalogBuilder(),
            FileTreePlanner(),
        ],
        save_intermediate_steps=False,   # or True if you want the logs
        tool_call_checker=True,
    )

    sys_prompt = (
        "You are a senior solution architect.\n"
        "Prefer using existing agents/tools from the catalog when available.\n"
        "If a suitable Matrix tool exists, reference it instead of creating a new one.\n"
        "Output must be feasible and minimal."
    )

    hints = ""
    if discovered_agents:
        hints += "\nKnown agents: " + ", ".join(a.name for a in discovered_agents[:5])
    if discovered_tools:
        hints += "\nKnown tools: " + ", ".join(t.name for t in discovered_tools[:5])

    try:
        out: LLMPlanOutput = await agent.run(
            prompt=(
                f"{sys_prompt}\n"
                f"User use-case: {req.use_case}\n"
                f"User preferred framework: {req.preferred_framework or ''}\n"
                f"{hints}\n"
                "Use known agents/tools if they fit; otherwise propose minimal new ones."
            ),
            expected_output=LLMPlanOutput,
            arguments={
                "framework_selector": {"use_case": req.use_case, "preferred": req.preferred_framework},
                "task_decomposer": {"use_case": req.use_case},
            },
        )

        if not out.tools and discovered_tools:
            out.tools = [
                PlannedTool(name=t.name, kind=t.kind, description=t.description, entrypoint=t.entrypoint)
                for t in discovered_tools[:3]
            ]

        if not out.project_tree:
            framework = out.framework or (req.preferred_framework or "crewai")
            out.project_tree = _plan_file_tree(framework)

        return {
            "project_tree": out.project_tree,
            "summary": {
                "framework": out.framework,
                "agents": [a.model_dump() for a in out.agents]
                if out.agents
                else [{"name": x.name, "role": "Matrix agent", "goals": []} for x in discovered_agents[:2]],
                "tools": [t.model_dump() for t in out.tools],
                "constraints": out.constraints,
                "notes": "Planner used Matrix catalog." if matrix.healthy() else "Planner ran without Matrix catalog.",
                "location": f"build/{out.framework}/",
            },
        }

    except Exception:
        # If BeeAI loop fails for any reason (including iteration exhaustion), use fallback
        return await _fallback_plan_with_matrix(req, discovered_agents, discovered_tools)


# ──────────────────────────────────────────────────────────────────────────────
# Deterministic fallback (never loops)
# ──────────────────────────────────────────────────────────────────────────────

async def _fallback_plan_with_matrix(
    req: PlanRequest,
    discovered_agents: list,
    discovered_tools: list,
) -> Dict[str, Any]:
    fw = (req.preferred_framework or "").strip().lower()
    if fw not in {"watsonx_orchestrate", "crewai", "langgraph", "beeai", "react"}:
        fw = "crewai"

    agents = (
        [{"name": a.name, "role": "Matrix agent", "goals": []} for a in discovered_agents[:2]]
        or [
            {"name": "Searcher", "role": "Web search specialist", "goals": ["Query the web", "Collect sources"]},
            {"name": "Synthesizer", "role": "Summarize and prioritize", "goals": ["De-duplicate", "Generate concise output"]},
        ]
    )

    tools = (
        [
            {"name": t.name, "kind": t.kind, "description": t.description, "entrypoint": t.entrypoint}
            for t in discovered_tools[:3]
        ]
        or [
            {"name": "http_get", "kind": "http", "description": "Perform HTTP GET requests", "entrypoint": "GET"},
            {"name": "search_results_parser", "kind": "python", "description": "Parse and rank results", "entrypoint": "tools.search:parse_results"},
        ]
    )

    tree = _plan_file_tree(fw)

    return {
        "project_tree": tree,
        "summary": {
            "framework": fw,
            "agents": agents,
            "tools": tools,
            "constraints": [],
            "notes": "Fallback planner used Matrix discovery where possible.",
            "location": f"build/{fw}/",
        },
    }


@dataclass
class PlanResponse:
    project_tree: List[str]
    summary: Dict[str, Any]


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _plan_file_tree(framework: str) -> List[str]:
    fw = (framework or "").strip().lower()
    common = ["README.md", "requirements.txt", ".env.example"]
    if fw == "watsonx_orchestrate":
        return common + ["skills/agent.yaml", "bundle/manifest.yaml"]
    if fw in ("crewai", "beeai", "langgraph"):
        return common + ["src/main.py", "src/agents/__init__.py", "src/tools/__init__.py"]
    if fw == "react":
        return common + ["src/App.tsx", "src/components/SearchPanel.tsx", "package.json"]
    return common + ["src/main.py", "src/agents/__init__.py", "src/tools/__init__.py"]


__all__ = ["PlanRequest", "plan", "LLMPlanOutput", "PlannedTool", "PlannedAgent"]
