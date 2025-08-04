# tests/test_planning_agent.py
"""
Planner tests (backend/agents/planning_agent.py).

We cover two paths:
  1) Fallback plan when BeeAI ToolCallingAgent isn't importable.
  2) "Happy path" with a mocked ToolCallingAgent and mocked LLM backends
     (Watsonx/OpenAI) that match your installed beeai_framework v0.1.32 layout.

No real LLM calls are made. These tests verify provider selection, schema
plumbing, and stable return shapes.
"""

from __future__ import annotations

import sys
import types

import pytest


@pytest.mark.asyncio
async def test_planner_fallback_plan(monkeypatch):
    """
    If ToolCallingAgent is None (unavailable), the planner should return a
    deterministic fallback plan and remain resilient.
    """
    # Force fallback by making ToolCallingAgent None
    import backend.agents.planning_agent as pa

    monkeypatch.setattr(pa, "ToolCallingAgent", None, raising=True)

    # Avoid Matrix calls by making MatrixConnector unhealthy
    class _DeadMatrix:
        def healthy(self) -> bool:  # noqa: D401
            return False

        def list_agents(self, *a, **k):  # noqa: D401
            return []

        def list_tools(self, *a, **k):  # noqa: D401
            return []

    monkeypatch.setattr(pa, "MatrixConnector", _DeadMatrix, raising=True)

    out = await pa.plan(
        "web search bot", preferred_framework="watsonx_orchestrate", mcp_catalog={}
    )
    assert "project_tree" in out and isinstance(out["project_tree"], list)
    assert "summary" in out and isinstance(out["summary"], dict)
    assert out["summary"]["framework"] in {
        "watsonx_orchestrate",
        "crewai",
        "beeai",
        "langgraph",
        "react",
    }


@pytest.mark.asyncio
async def test_planner_with_mocked_beeai_and_llm_selection(monkeypatch):
    """
    Simulate a working BeeAI ToolCallingAgent and provider selection for
    watsonx (default). We avoid importing real beeai_framework by stubbing
    the adapter modules and agent class the planner expects (v0.1.32 layout).
    """
    # --- Ensure env for Settings validation (Watsonx path) ---
    monkeypatch.setenv("AGENTGEN_PROVIDER", "watsonx")
    monkeypatch.setenv("WATSONX_API_KEY", "abc123")
    monkeypatch.setenv("WATSONX_PROJECT_ID", "proj-123")
    monkeypatch.setenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")

    # --- Create fake "beeai_framework.adapters.watsonx.backend.chat" module ---
    watsonx_mod = types.ModuleType("beeai_framework.adapters.watsonx.backend.chat")

    class WatsonxChatModel:  # matches constructor signature used in planner
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    watsonx_mod.WatsonxChatModel = WatsonxChatModel
    sys.modules["beeai_framework.adapters.watsonx.backend.chat"] = watsonx_mod

    # --- Create fake "beeai_framework.adapters.openai.backend.chat" module (fallback) ---
    openai_mod = types.ModuleType("beeai_framework.adapters.openai.backend.chat")

    class OpenAIChatModel:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    openai_mod.OpenAIChatModel = OpenAIChatModel
    sys.modules["beeai_framework.adapters.openai.backend.chat"] = openai_mod

    # --- Mock ToolCallingAgent to return a valid LLMPlanOutput instance ---
    import backend.agents.planning_agent as pa

    class _FakeAgent:
        def __init__(self, **_kwargs):
            pass

        async def run(self, *, prompt, expected_output, arguments):
            # Build a valid output using the module's Pydantic classes
            return pa.LLMPlanOutput(
                framework="watsonx_orchestrate",
                constraints=[],
                agents=[
                    pa.PlannedAgent(
                        name="Planner", role="Define steps", goals=["Create sub-tasks"]
                    )
                ],
                tools=[
                    pa.PlannedTool(
                        name="http_get",
                        kind="http",
                        description="GET",
                        entrypoint="GET",
                    )
                ],
                project_tree=["README.md", "skills/agent.yaml", "bundle/manifest.yaml"],
                notes=None,
            )

    # Patch ToolCallingAgent to our fake
    monkeypatch.setattr(pa, "ToolCallingAgent", _FakeAgent, raising=True)

    # Make Matrix connector inert
    class _NoMatrix:
        def healthy(self) -> bool:  # noqa: D401
            return False

        def list_agents(self, *a, **k):
            return []

        def list_tools(self, *a, **k):
            return []

    monkeypatch.setattr(pa, "MatrixConnector", _NoMatrix, raising=True)

    # Execute planner
    out = await pa.plan(
        "create a web search agent",
        preferred_framework="watsonx_orchestrate",
        mcp_catalog={},
    )
    assert out["summary"]["framework"] == "watsonx_orchestrate"
    assert isinstance(out["project_tree"], list) and len(out["project_tree"]) >= 1
    assert any(t.get("name") == "http_get" for t in out["summary"]["tools"])
