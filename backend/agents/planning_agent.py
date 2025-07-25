# backend/agents/planning_agent.py
from __future__ import annotations

import logging
import textwrap
from typing import Any, Dict, List, Literal # Import Literal for the prompt example

from pydantic import BaseModel, Field # Import Field for more detailed schema in LLMPlanOutput

# BeeAI agent infrastructure ───────────────────────────────────────────────
from beeai_framework.agents.tool_calling.agent import ToolCallingAgent
from beeai_framework.agents.tool_calling.prompts import PromptTemplateInput
from beeai_framework.memory.token_memory import TokenMemory
from beeai_framework.template import PromptTemplate

# LLM adapters
from beeai_framework.adapters.openai import OpenAIChatModel
from beeai_framework.adapters.watsonx import WatsonxChatModel

# Project utilities
from ..config import settings
from ..utils import relative_tree


##TODO
#Option A (Recommended): Modify the prompt to include project_tree:
#Make the prompt explicitly ask for project_tree if it's genuinely part of the LLM's direct output. However, looking at your plan function, project_tree is constructed by the application after the LLM output is received. This means the project_tree should NOT be part of the LLM's direct JSON output.



logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
#  Pydantic models for the API
# ═══════════════════════════════════════════════════════════════════════════
class PlanRequest(BaseModel):
    use_case: str
    preferred_framework: str
    mcp_catalog: Dict[str, Any]


class BuildTask(BaseModel):
    """Schema for a single build task."""
    kind: Literal["python_tool", "mcp_tool"] = Field(
        ..., description="Type of task: 'python_tool' or 'mcp_tool'"
    )
    name: str = Field(..., description="Name of the tool or component")
    gateway: str | None = Field(
        None, description="Gateway name, required for 'mcp_tool'"
    )

class LLMPlanOutput(BaseModel):
    """
    Schema for the JSON output expected directly from the LLM.
    This matches the structure requested in the prompt.
    """
    selected_framework: str = Field(
        ..., description="The framework chosen for the project"
    )
    build_tasks: List[BuildTask] = Field(
        ..., description="List of build tasks (existing MCP tools or new Python tools)"
    )


class PlanResponse(BaseModel):
    selected_framework: str
    project_tree: List[str]
    build_tasks: List[Dict[str, Any]]


# ═══════════════════════════════════════════════════════════════════════════
#  Prompt template
# ═══════════════════════════════════════════════════════════════════════════
# Refined prompt to explicitly include the JSON structure and example
_ARCH_PROMPT = textwrap.dedent(
    """
    You are a senior AI software architect. Your goal is to generate a project plan.

    Given:
      • a user use‑case (natural language),
      • their preferred framework,
      • an MCP tool catalogue (JSON map of gateway→tools).

    Decide which existing MCP tools to reuse and which Python tools to scaffold to fulfill the use-case.
    You MUST output a valid JSON object. Do not include any explanatory text outside the JSON.
    The JSON object MUST strictly adhere to the following schema and examples:

    ```json
    {
      "selected_framework": "string",
      "build_tasks": [
        {
          "kind": "python_tool" | "mcp_tool",
          "name": "string",
          "gateway"?: "string" // This field is required ONLY if 'kind' is 'mcp_tool'
        }
      ]
    }
    ```

    Example for `build_tasks`:
    - To scaffold a new Python tool for data processing: `{"kind": "python_tool", "name": "data_processor"}`
    - To reuse an existing MCP tool called "authenticator" under the "auth_gateway": `{"kind": "mcp_tool", "name": "authenticator", "gateway": "auth_gateway"}`

    Provide only the JSON output.
    """
)

# _EmptySchema is now less relevant as LLMPlanOutput is passed directly, but keep for consistency if needed by PromptTemplateInput
class _EmptySchema(BaseModel):
    """Placeholder schema (no fields)."""
    pass

_SYSTEM_TEMPLATE = PromptTemplate(
    PromptTemplateInput(schema=_EmptySchema, template=_ARCH_PROMPT)
)

# ═══════════════════════════════════════════════════════════════════════════
#  Planner function
# ═══════════════════════════════════════════════════════════════════════════
async def plan(req: PlanRequest) -> PlanResponse:
    """Generate a build‑plan using either OpenAI or Watsonx."""
    logger.info("Planning for use‑case: %s", req.use_case)

    # 1. Pick the LLM adapter --------------------------------------------------------
    pf = req.preferred_framework.lower()
    if "openai" in pf:
        llm = OpenAIChatModel(
            api_key=settings.openai_api_key,
            model=settings.openai_model_name,
        )
    elif "watsonx" in pf:
        llm = WatsonxChatModel(
            model_id=settings.watsonx_model_id,
            api_key=settings.watsonx_api_key,
            project_id=settings.watsonx_project_id,
            space_id=settings.watsonx_space_id,
            base_url=settings.watsonx_url,
        )
    else:
        raise ValueError(f"Unsupported framework: {req.preferred_framework!r}")

    # 2. Create the Tool‑Calling agent ----------------------------------------------
    # It's good that final_answer_as_tool is False, as we want direct JSON output for planning.
    architect = ToolCallingAgent(
        llm=llm,
        memory=TokenMemory(llm=llm),
        templates={"system": _SYSTEM_TEMPLATE},
        final_answer_as_tool=False,
    )

    # 3. Run the agent ---------------------------------------------------------------
    user_prompt = (
        f"USE_CASE:\n{req.use_case}\n"
        f"PREFERRED_FRAMEWORK:\n{req.preferred_framework}\n"
        f"MCP_CATALOG:\n{req.mcp_catalog}"
    )

    try:
        # Pass the LLMPlanOutput schema directly to expected_output
        run_out = await architect.run(prompt=user_prompt, expected_output=LLMPlanOutput)
        # The result from architect.run when using expected_output will be an instance
        # of the specified Pydantic model (LLMPlanOutput in this case).
        llm_output: LLMPlanOutput = run_out.result

        # Convert the Pydantic model to a dictionary for easier access with existing logic
        plan_json: Dict[str, Any] = llm_output.model_dump()

    except Exception as e:
        logger.error(f"Planning failed after multiple iterations: {e}", exc_info=True)
        # Re-raise or handle more gracefully, possibly returning an error response
        raise e # Re-raise the original error for now to propagate it up

    # 4. Build the preview tree ------------------------------------------------------
    fw = plan_json["selected_framework"]
    base = settings.build_base / fw
    tree: list[str] = [
        f"{settings.build_base}/",
        f"{base}/",
        f"{base}/agents/",
    ]
    for task in plan_json.get("build_tasks", []):
        if task.get("kind") == "python_tool":
            tree.append(f"{base}/tool_sources/{task['name']}/")
        elif task.get("kind") == "mcp_tool":
            # Ensure 'gateway' exists for mcp_tool kind before accessing
            if "gateway" in task and task["gateway"]:
                tree.append(f"{base}/mcp_servers/{task['gateway']}/")
            else:
                logger.warning(f"MCP tool '{task.get('name', 'unknown')}' missing 'gateway' field. Skipping directory for this task.")


    logger.debug("Plan tree preview: %s", tree)

    # 5. Return the structured response ---------------------------------------------
    return PlanResponse(
        selected_framework=fw,
        project_tree=tree,
        build_tasks=plan_json["build_tasks"],
    )