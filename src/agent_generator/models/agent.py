# ────────────────────────────────────────────────────────────────
#  src/agent_generator/models/agent.py
# ────────────────────────────────────────────────────────────────
"""
Agent‑level data structures.

Each `Agent` owns a set of tools plus the LLM configuration that backs
its reasoning.  The default `LLMConfig` is tuned for IBM watsonx.ai but
can be overridden per‑agent or at runtime via `Settings`.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class LLMConfig(BaseModel):
    """Provider‑agnostic language‑model settings."""

    provider: str = Field(
        default="watsonx",
        description="Name of the LLM provider (e.g. watsonx, openai).",
    )
    model: str = Field(
        ...,
        description="Full model identifier understood by the provider.",
        examples=["meta-llama-3-70b-instruct"],
    )
    temperature: float = Field(
        default=0.7,
        ge=0,
        le=2,
        description="Sampling temperature for text generation.",
    )
    max_tokens: int = Field(
        default=4096,
        ge=1,
        description="Token cap for a single completion.",
    )

    @field_validator("model")
    @classmethod
    def _strip_spaces(cls, v: str) -> str:  # noqa: D401
        return v.strip()

    # Convenience
    def json_schema(self) -> dict:  # noqa: D401
        """Return the JSON Schema for this model."""
        return self.model_json_schema()


class Tool(BaseModel):
    """An executable capability the agent can call."""

    name: str = Field(..., description="Unique tool name (snake‑case).")
    description: Optional[str] = Field(
        None, description="Human readable sentence describing the tool."
    )
    endpoint: Optional[str] = Field(
        None,
        description="HTTP endpoint or internal reference implementing the tool.",
    )

    def json_schema(self) -> dict:  # noqa: D401
        return self.model_json_schema()


class Agent(BaseModel):
    """
    A reasoning entity backed by an LLM.

    Attributes
    ----------
    id
        Unique identifier used by workflows to reference this agent.
    role
        Short sentence (“research assistant”, “content writer” …).
    tools
        List of capabilities this agent may invoke.
    llm
        Provider + model + sampling parameters.
    """

    id: str = Field(..., description="Unique agent identifier.")
    role: str = Field(..., description="Concise description of the agent’s role.")
    tools: List[Tool] = Field(
        default_factory=list,
        description="Tools (APIs/skills) the agent can invoke during execution.",
    )
    llm: LLMConfig = Field(
        default_factory=LLMConfig,
        description="LLM configuration; defaults to watsonx meta‑llama‑3‑70b.",
    )

    def json_schema(self) -> dict:  # noqa: D401
        """Return the JSON Schema for this model."""
        return self.model_json_schema()
