"""Unified planning service used by CLI and Web API."""

from __future__ import annotations

import re
import warnings as _warnings
from typing import Optional

from agent_generator.application.validation_service import validate_spec
from agent_generator.domain.project_spec import (
    AgentSpec,
    ArtifactMode,
    FrameworkChoice,
    LLMSpec,
    OutputTier,
    ProjectSpec,
    RuntimeSpec,
    TaskSpec,
    ToolSpec,
)
from agent_generator.planners.keyword_planner import KeywordPlanner
from agent_generator.planners.spec_normalizer import SpecNormalizer

_keyword_planner = KeywordPlanner()
_normalizer = SpecNormalizer()


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9\s-]", "", text.lower())
    slug = re.sub(r"[\s_]+", "-", slug.strip())
    return slug[:40] or "agent-project"


def _extract_roles(prompt: str, hints: dict) -> list[dict]:
    """Extract agent roles from keyword hints + prompt analysis."""
    roles = hints.get("suggested_roles", [])
    if not roles:
        roles = ["assistant"]
    agents = []
    for role in roles[:4]:
        agents.append(
            {
                "id": role.replace(" ", "_").lower(),
                "role": role.replace("_", " ").title(),
                "goal": f"Handle {role}-related tasks effectively",
                "backstory": f"An experienced {role} with deep domain expertise.",
                "tools": hints.get("suggested_tools", [])[:2],
            }
        )
    return agents


def _extract_tasks(prompt: str, agents: list[dict]) -> list[dict]:
    """Extract tasks from prompt sentences."""
    sentences = [s.strip() for s in re.split(r"[.!?]+", prompt) if s.strip() and len(s.strip()) > 5]
    if not sentences:
        sentences = [prompt.strip()]
    tasks = []
    for i, sentence in enumerate(sentences[:8]):
        agent_idx = i % len(agents)
        task_id = f"task_{i + 1}"
        tasks.append(
            {
                "id": task_id,
                "description": sentence,
                "agent_id": agents[agent_idx]["id"],
                "expected_output": f"Completed: {sentence[:80]}",
                "depends_on": [f"task_{i}"] if i > 0 else [],
            }
        )
    return tasks


def plan(
    prompt: str,
    framework: Optional[str] = None,
    artifact_mode: Optional[str] = None,
    provider: Optional[str] = None,
    mcp: bool = False,
    use_llm: bool = False,
) -> tuple[ProjectSpec, list[str]]:
    """Plan a project from a natural language prompt.

    Returns (validated_spec, warnings).
    This is the ONLY entry point for creating a ProjectSpec.
    Used by both CLI and Web API.

    Parameters
    ----------
    use_llm : bool
        If True *and* a provider is given, attempt LLM-based planning
        before falling back to the keyword-based planner.
    """
    # Step 1: keyword classification (always runs -- provides hints)
    hints = _keyword_planner.classify(
        prompt, user_framework=framework, user_artifact_mode=artifact_mode
    )

    # ── Optional LLM planning stage ──────────────────────────────
    if use_llm and provider:
        _warnings.warn(
            "LLM-based planning is experimental and not enabled by default.",
            stacklevel=2,
        )
        try:
            from agent_generator.providers import PROVIDERS

            if provider in PROVIDERS:
                from agent_generator.config import get_settings_lenient
                from agent_generator.planners.llm_planner import LLMPlanner

                provider_inst = PROVIDERS[provider](get_settings_lenient())
                llm_planner = LLMPlanner(provider_inst)
                llm_spec = llm_planner.plan(prompt, hints)
                if llm_spec is not None:
                    spec, norm_warnings = _normalizer.normalize(llm_spec)
                    validation = validate_spec(spec)
                    return spec, norm_warnings + validation.warnings
        except Exception:
            pass  # Fall through to keyword-based planning

    # ── Keyword-based fallback (always works, no credentials) ────
    fw = hints["suggested_framework"]
    mode = hints["suggested_artifact_mode"]
    agents = _extract_roles(prompt, hints)
    tasks = _extract_tasks(prompt, agents)
    tools = [{"id": t, "template": t, "inputs": {}} for t in hints.get("suggested_tools", [])]

    spec = ProjectSpec(
        name=_slugify(prompt[:50]),
        description=prompt[:500],
        framework=FrameworkChoice(fw),
        artifact_mode=ArtifactMode(mode),
        template_tier=OutputTier.PRODUCTION,
        llm=LLMSpec(provider=provider or "watsonx"),
        agents=[AgentSpec(**a) for a in agents],
        tasks=[TaskSpec(**t) for t in tasks],
        tools=[ToolSpec(**t) for t in tools],
        runtime=RuntimeSpec(mcp_wrapper=mcp),
    )

    # Step 3: normalize (fix references, apply defaults)
    spec, norm_warnings = _normalizer.normalize(spec)

    # Step 4: validate
    validation = validate_spec(spec)
    all_warnings = norm_warnings + validation.warnings

    if not validation.valid:
        all_warnings.extend(validation.errors)

    return spec, all_warnings
