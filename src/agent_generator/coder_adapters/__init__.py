"""AI-coder prompt adapter registry (Batch 7).

Each ``CoderId`` maps to a ``CoderAdapter`` whose prompt is grounded in the matrix-definitions
rule that governs that coder. Use ``get_adapter`` / ``render_prompt`` from the engine.
"""

from __future__ import annotations

from agent_generator.coder_adapters.base import CoderAdapter, PromptContext
from agent_generator.contracts.common import CoderId
from agent_generator.contracts.prompt_pack import PromptItem

CLAUDE_CODE = CoderAdapter(
    coder=CoderId.CLAUDE_CODE,
    label="Claude Code controlled prompt",
    coder_rule="RMD-110",
    handoff_mode="cli",
    helper_filename="CLAUDE.md",
    workflow=(
        "Work in the repository. Read the whole bundle contract before writing any code, then "
        "implement the task in small, verifiable steps."
    ),
    output_format=(
        "Return, in order: (1) a brief implementation plan, (2) the exact files you changed, "
        "(3) the results of the validation commands, (4) any blockers where a policy stopped you."
    ),
)

CODEX_CHATGPT = CoderAdapter(
    coder=CoderId.CODEX_CHATGPT,
    label="Codex / ChatGPT controlled prompt",
    coder_rule="RMD-111",
    handoff_mode="chat",
    helper_filename="AGENTS.md",
    workflow=(
        "Drive the work from the acceptance criteria: implement exactly what each criterion "
        "requires and nothing more."
    ),
    output_format=(
        "Output a single unified diff limited to the allowed files. Then, for each acceptance "
        "criterion, state pass or fail with one line of evidence."
    ),
)

CURSOR = CoderAdapter(
    coder=CoderId.CURSOR,
    label="Cursor controlled prompt",
    coder_rule="RMD-108",
    handoff_mode="workspace",
    workflow=(
        "In your workspace, restrict edits to the allowed files. If a requested change needs a "
        "new file or dependency, stop and explain why instead of doing it."
    ),
    output_format=(
        "Provide a concise change summary, the exact commands you ran, and whether the result "
        "is ready for validation."
    ),
)

GITPILOT = CoderAdapter(
    coder=CoderId.GITPILOT,
    label="GitPilot controlled prompt",
    coder_rule="RMD-113",
    handoff_mode="git",
    # GitPilot reads workspace rules from `.gitpilotrules` (and `.gitpilot/rules/*.md`), so emit the
    # Matrix contract there: its Explorer/Planner/Coder/Reviewer then honor it natively, no extra
    # wiring. See gitpilot/gitpilot/rules.py (load_rules).
    helper_filename=".gitpilotrules",
    workflow=(
        "Work Matrix-native and repository-scoped: create a feature branch for the task and "
        "make one focused commit. Do not touch files outside the allowlist."
    ),
    output_format=(
        "Output the branch name, the commit diff (allowed files only), and pass/fail for each "
        "acceptance criterion."
    ),
)

IBM_BOB = CoderAdapter(
    coder=CoderId.IBM_BOB,
    label="IBM Bob controlled prompt",
    coder_rule="RMD-112",
    handoff_mode="enterprise",
    workflow=(
        "Operate within enterprise-safe boundaries: no external network calls, no new services, "
        "no secrets in code. Implement only the assigned task."
    ),
    output_format=(
        "Return a change summary, the validation results, and a short audit note describing what "
        "changed and why it stays within the contract."
    ),
)

GENERIC = CoderAdapter(
    coder=CoderId.GENERIC_AI_CODER,
    label="Controlled implementation prompt",
    coder_rule="RMD-114",
    handoff_mode="generic",
    workflow=(
        "However you receive this work, treat the bundle as a contract. Implement only the "
        "assigned task and edit only the allowed files."
    ),
    output_format=(
        "Return a brief implementation plan, the exact files changed, and the validation "
        "results."
    ),
)

_REGISTRY: dict[CoderId, CoderAdapter] = {
    a.coder: a for a in (CLAUDE_CODE, CODEX_CHATGPT, CURSOR, GITPILOT, IBM_BOB, GENERIC)
}


def get_adapter(coder: CoderId | str) -> CoderAdapter:
    """Return the adapter for a coder, falling back to the generic adapter (RMD-109)."""
    if isinstance(coder, str):
        try:
            coder = CoderId(coder)
        except ValueError:
            return GENERIC
    return _REGISTRY.get(coder, GENERIC)


def render_prompt(coder: CoderId | str, ctx: PromptContext) -> PromptItem:
    return get_adapter(coder).render(ctx)


__all__ = [
    "CoderAdapter",
    "PromptContext",
    "get_adapter",
    "render_prompt",
    "CLAUDE_CODE",
    "CODEX_CHATGPT",
    "CURSOR",
    "GITPILOT",
    "IBM_BOB",
    "GENERIC",
]
