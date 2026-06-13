"""Coder prompt contracts — single prompt response and multi-coder pack."""

from __future__ import annotations

from pydantic import Field

from agent_generator.contracts.common import CoderId, StrictModel


class PromptItem(StrictModel):
    coder: CoderId
    label: str
    path: str
    content: str = Field(min_length=20)
    contract_files: list[str] = Field(default_factory=list)
    allowed_files: list[str] = Field(default_factory=list)
    validation_commands: list[str] = Field(default_factory=list)
    hard_constraints: list[str] = Field(default_factory=list)


class PromptPack(StrictModel):
    prompt_pack_id: str
    bundle_id: str
    blueprint_id: str
    default_coder: CoderId
    prompts: list[PromptItem]


class PromptResponse(StrictModel):
    coder: CoderId | str
    label: str = "Controlled implementation prompt"
    path: str = "coder-prompts/generic-ai-coder.md"
    prompt: str
    bundle_id: str | None = None
    bundle_url: str | None = None
    task_id: str = "TASK-001"
    contract_files: list[str]
    allowed_files: list[str] = Field(default_factory=list)
    validation_commands: list[str] = Field(default_factory=list)
    hard_constraints: list[str] = Field(default_factory=list)
    handoff_mode: str | None = None


class CoderHandoff(StrictModel):
    """Everything needed to hand a (batch) to one AI coder: prompt + tool-native helper files."""

    coder: CoderId
    prompt: PromptResponse
    helper_files: dict[str, str] = Field(default_factory=dict)  # filename -> content
    batch_id: str | None = None


__all__ = ["PromptItem", "PromptPack", "PromptResponse", "CoderHandoff"]
