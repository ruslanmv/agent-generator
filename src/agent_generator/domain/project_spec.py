"""Canonical project specification — the single source of truth."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class FrameworkChoice(str, Enum):
    CREWAI = "crewai"
    CREWAI_FLOW = "crewai_flow"
    LANGGRAPH = "langgraph"
    REACT = "react"
    WATSONX_ORCHESTRATE = "watsonx_orchestrate"


class ArtifactMode(str, Enum):
    CODE_ONLY = "code_only"
    YAML_ONLY = "yaml_only"
    CODE_AND_YAML = "code_and_yaml"


class OutputTier(str, Enum):
    STARTER = "starter"
    PRODUCTION = "production"


class AgentSpec(BaseModel):
    id: str = Field(..., description="Unique agent identifier (snake_case).")
    role: str = Field(..., description="Agent role name.")
    goal: str = Field(..., description="What this agent tries to achieve.")
    backstory: str = Field(default="", description="Background context for the agent.")
    tools: list[str] = Field(default_factory=list, description="Tool IDs this agent can use.")
    llm_override: Optional[str] = Field(default=None, description="Optional model override.")


class TaskSpec(BaseModel):
    id: str = Field(..., description="Unique task identifier (snake_case).")
    description: str = Field(..., description="What this task does.")
    agent_id: str = Field(..., description="ID of the agent responsible.")
    expected_output: str = Field(..., description="What the task should produce.")
    depends_on: list[str] = Field(default_factory=list, description="IDs of prerequisite tasks.")


class ToolSpec(BaseModel):
    id: str = Field(..., description="Unique tool identifier.")
    template: str = Field(..., description="Tool catalog template key.")
    inputs: dict[str, str] = Field(default_factory=dict, description="Template variable overrides.")


class LLMSpec(BaseModel):
    provider: str = Field(default="watsonx")
    model: str = Field(default="meta-llama/llama-3-3-70b-instruct")
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)


class RuntimeSpec(BaseModel):
    serve_api: bool = Field(default=False)
    mcp_wrapper: bool = Field(default=False)
    mcp_port: int = Field(default=8080, ge=1, le=65535)
    healthcheck_path: str = Field(default="/health")


class ProjectSpec(BaseModel):
    """Canonical specification for a multi-agent project."""

    name: str = Field(
        ...,
        description="Project slug (kebab-case).",
        pattern=r"^[a-z0-9][a-z0-9-]*$",
    )
    version: str = Field(default="1.0", description="Schema version.")
    template_tier: OutputTier = Field(default=OutputTier.PRODUCTION)
    metadata: dict[str, str] = Field(default_factory=dict)
    description: str = Field(..., max_length=500)
    framework: FrameworkChoice
    artifact_mode: ArtifactMode = Field(default=ArtifactMode.CODE_ONLY)
    llm: LLMSpec = Field(default_factory=LLMSpec)
    agents: list[AgentSpec] = Field(..., min_length=1)
    tasks: list[TaskSpec] = Field(..., min_length=1)
    tools: list[ToolSpec] = Field(default_factory=list)
    runtime: RuntimeSpec = Field(default_factory=RuntimeSpec)

    @model_validator(mode="after")
    def validate_references(self) -> "ProjectSpec":
        agent_ids = {a.id for a in self.agents}
        task_ids = {t.id for t in self.tasks}
        tool_ids = {t.id for t in self.tools}

        for task in self.tasks:
            if task.agent_id not in agent_ids:
                raise ValueError(f"Task '{task.id}' references unknown agent '{task.agent_id}'")
            for dep in task.depends_on:
                if dep not in task_ids:
                    raise ValueError(f"Task '{task.id}' depends on unknown task '{dep}'")

        for agent in self.agents:
            for tool_id in agent.tools:
                if tool_id not in tool_ids:
                    raise ValueError(f"Agent '{agent.id}' references unknown tool '{tool_id}'")

        return self
