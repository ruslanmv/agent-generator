"""AI-coder prompt adapters (Batch 7).

Each supported AI coder gets a *contract-bound* prompt instead of one shared template:
task-scoped, citing the Ruslan Magana Definitions it must obey, with a bundle-fetch hint and
a mandatory ``MATRIX_STATUS`` stop condition. The per-coder shape is grounded in the
matrix-definitions rules that already exist:

* Claude Code   → RMD-110 (contract-first)
* Codex/ChatGPT → RMD-111 (acceptance-criteria driven)
* Cursor        → RMD-108 (patch-scoped workspace edits)
* GitPilot      → RMD-113 (Matrix-native, repository-scoped)
* IBM Bob       → RMD-112 (enterprise-safe boundaries)
* Generic       → RMD-114 (tool-agnostic, contract-first)

The core promise: *AI coders are workers, not architects* (RMD-101).
"""

from __future__ import annotations

from dataclasses import dataclass

from agent_generator.contracts.blueprint import BlueprintResult, BlueprintTask
from agent_generator.contracts.common import CoderId
from agent_generator.contracts.prompt_pack import PromptItem

CONTROL_CONTRACT_FILES = (
    "MATRIX_BLUEPRINT.yaml",
    "MATRIX_STANDARDS.lock",
    "MATRIX_ALLOWED_CHANGES.md",
    "MATRIX_ACCEPTANCE_CRITERIA.md",
)

# RMD rules every controlled prompt cites, regardless of coder.
_UNIVERSAL_RULES = ("RMD-101", "RMD-103", "RMD-105", "RMD-107", "RMD-108", "RMD-118", "RMD-119")


@dataclass(frozen=True)
class PromptContext:
    blueprint: BlueprintResult | None
    task: BlueprintTask | None
    bundle_id: str | None = None
    bundle_url: str | None = None
    rule_ids: tuple[str, ...] = ()
    version: str = "1.0.0"
    batch_label: str | None = None  # e.g. "Batch 03" — when implementing a batch
    parent_commit: str | None = None  # the commit this batch builds on


@dataclass(frozen=True)
class CoderAdapter:
    """A per-coder prompt renderer. Behavior differences live in the data, not in code."""

    coder: CoderId
    label: str
    coder_rule: str  # the RMD rule that governs this coder's prompt
    handoff_mode: str
    workflow: str  # coder-specific "how to receive/apply the work"
    output_format: str  # coder-specific "what to return"
    helper_filename: str = "MATRIX_INSTRUCTIONS.md"  # tool-native instruction file name

    def render(self, ctx: PromptContext) -> PromptItem:
        task = ctx.task
        task_id = task.task_id if task else "TASK-001"
        title = task.title if task else "Implement the first controlled task"
        allowed = list(task.allowed_files) if task else ["backend/app/api/routes.py"]
        criteria = list(task.acceptance_criteria) if task else ["Tests pass"]
        commands = (list(ctx.blueprint.acceptance_commands) if ctx.blueprint else []) or [
            "pytest -q",
            "ruff check .",
        ]

        fetch_url = ctx.bundle_url or (
            f"/api/v1/bundles/{ctx.bundle_id}/download" if ctx.bundle_id else None
        )
        content = self._render_body(ctx, task_id, title, allowed, criteria, commands, fetch_url)
        return PromptItem(
            coder=self.coder,
            label=self.label,
            path=f"coder-prompts/{self.coder.value}.md",
            content=content,
            contract_files=list(CONTROL_CONTRACT_FILES)
            + ["MATRIX_TASKS.md", "MATRIX_VALIDATION.md"],
            allowed_files=allowed,
            validation_commands=commands,
            hard_constraints=[
                "Edit only the allowed files (RMD-002)",
                "Do not modify MATRIX_BLUEPRINT.yaml or MATRIX_STANDARDS.lock (RMD-103)",
                "Do not add dependencies, services, or auth not in the blueprint (RMD-105)",
                "Keep changes patch-scoped to this task (RMD-108)",
            ],
        )

    def helper_files(self, ctx: PromptContext) -> dict[str, str]:
        """Emit the tool-native instruction file (``CLAUDE.md`` / ``AGENTS.md`` / plain rules).

        Returns ``{filename: content}`` — repository-level guidance derived from the same
        contract as the prompt: read the control files, edit only allowed files, run the
        acceptance commands, end with ``MATRIX_STATUS``. Native instruction files (Claude's
        ``CLAUDE.md``, Codex's ``AGENTS.md``) are officially supported; the others are plain
        markdown rules exports.
        """
        return {self.helper_filename: self._render_helper(ctx)}

    def _render_helper(self, ctx: PromptContext) -> str:
        commands = (list(ctx.blueprint.acceptance_commands) if ctx.blueprint else []) or [
            "pytest -q",
            "ruff check .",
        ]
        command_block = "\n".join(f"- `{c}`" for c in commands)
        contract_block = "\n".join(f"- {f}" for f in CONTROL_CONTRACT_FILES)
        batch_block = ""
        if ctx.batch_label:
            parent = f" (builds on commit {ctx.parent_commit})" if ctx.parent_commit else ""
            batch_block = (
                f"\n## Current batch\n\n"
                f"Implement **{ctx.batch_label}** only{parent}. Make the smallest change that "
                "satisfies this batch; do not start other work.\n"
            )
        return (
            f"# {self.label} — repository instructions\n"
            "\n"
            "This repository is a **Matrix Bundle**: a controlled contract for AI coders. "
            f"{self.label.split(' ')[0]} must follow it, not redesign it (RMD-101).\n"
            "\n"
            "## Always\n"
            "\n"
            "Read the contract before changing anything:\n"
            f"{contract_block}\n"
            "\n"
            "- Edit only the files allowed for the current task (RMD-002, RMD-107).\n"
            "- Never modify MATRIX_BLUEPRINT.yaml, MATRIX_STANDARDS.lock, or "
            ".github/workflows/ (RMD-103).\n"
            "- Do not add dependencies, services, or auth not in the blueprint (RMD-105).\n"
            "- Keep each change patch-scoped to one task (RMD-108).\n"
            f"{batch_block}"
            "\n"
            "## Validate before finishing (RMD-119)\n"
            "\n"
            f"{command_block}\n"
            "\n"
            "## Finish\n"
            "\n"
            "End every response with a stop condition (RMD-118):\n"
            "\n"
            "```\n"
            "MATRIX_STATUS: approved | needs_repair | rejected\n"
            "```\n"
        )

    def _render_body(
        self,
        ctx: PromptContext,
        task_id: str,
        title: str,
        allowed: list[str],
        criteria: list[str],
        commands: list[str],
        fetch_url: str | None,
    ) -> str:
        rules = ctx.rule_ids or _UNIVERSAL_RULES
        allowed_block = "\n".join(f"- {p}" for p in allowed)
        criteria_block = "\n".join(f"- {c}" for c in criteria)
        command_block = "\n".join(f"- `{c}`" for c in commands)
        contract_block = "\n".join(f"- {f}" for f in CONTROL_CONTRACT_FILES)
        fetch_line = f"Fetch the Matrix Bundle first: `GET {fetch_url}`\n\n" if fetch_url else ""
        rules_line = ", ".join(rules)
        batch_line = ""
        if ctx.batch_label:
            parent = f" It builds on commit {ctx.parent_commit}." if ctx.parent_commit else ""
            batch_line = (
                f"This is **{ctx.batch_label}**.{parent} Implement only what this batch "
                "requires — nothing else.\n\n"
            )

        return (
            f"# {self.label}\n"
            "\n"
            f"You are implementing MATRIX task **{task_id}** only. "
            f"AI coders are workers, not architects (RMD-101).\n"
            "\n"
            f"{batch_line}"
            f"{fetch_line}"
            f"{self.workflow.strip()} ({self.coder_rule})\n"
            "\n"
            f"## Read the contract first\n\n{contract_block}\n"
            "\n"
            f"## Task {task_id}: {title}\n"
            "\n"
            f"Allowed files — edit ONLY these (RMD-002, RMD-107):\n{allowed_block}\n"
            "\n"
            f"Acceptance criteria:\n{criteria_block}\n"
            "\n"
            "## Hard constraints\n"
            "- Do not modify MATRIX_BLUEPRINT.yaml or MATRIX_STANDARDS.lock (RMD-103).\n"
            "- Do not add dependencies, services, or auth not in the blueprint (RMD-105).\n"
            "- Do not edit files outside the allowlist (RMD-107).\n"
            "- Keep your change patch-scoped to this one task (RMD-108).\n"
            "\n"
            f"## Validate before finishing (RMD-119)\n\n{command_block}\n"
            "\n"
            f"## Output\n\n{self.output_format.strip()}\n"
            "\n"
            f"Governing rules: {rules_line}.\n"
            "\n"
            "End your response with a stop condition (RMD-118):\n"
            "```\n"
            "MATRIX_STATUS: approved | needs_repair | rejected\n"
            "```\n"
        )


__all__ = ["PromptContext", "CoderAdapter", "CONTROL_CONTRACT_FILES"]
