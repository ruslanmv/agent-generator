"""Render the six MATRIX control files, docs, and README (Batch 5).

Each renderer takes a ``BlueprintResult`` (and, where relevant, the rendered standards lock)
and returns deterministic file content. These are the human- and machine-readable contract
the AI coder must follow.
"""

from __future__ import annotations

from agent_generator.artifacts.canonical import canonical_yaml
from agent_generator.contracts.blueprint import BlueprintResult
from agent_generator.contracts.standards import StandardsLock

CONTROL_FILE_NAMES: tuple[str, ...] = (
    "MATRIX_BLUEPRINT.yaml",
    "MATRIX_STANDARDS.lock",
    "MATRIX_TASKS.md",
    "MATRIX_ALLOWED_CHANGES.md",
    "MATRIX_ACCEPTANCE_CRITERIA.md",
    "MATRIX_VALIDATION.md",
)


def render_blueprint_yaml(blueprint: BlueprintResult) -> str:
    return canonical_yaml(blueprint.to_definitions_dict())


def render_tasks_md(blueprint: BlueprintResult) -> str:
    lines = [
        f"# Matrix Tasks — {blueprint.name}",
        "",
        "Implement one task at a time. Touch only the files listed for that task.",
        "",
    ]
    for task in blueprint.tasks:
        lines.append(f"## {task.task_id}: {task.title}")
        lines.append("")
        lines.append("Allowed files:")
        lines.extend(f"- `{f}`" for f in task.allowed_files)
        if task.acceptance_criteria:
            lines.append("")
            lines.append("Done when:")
            lines.extend(f"- {c}" for c in task.acceptance_criteria)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_allowed_changes_md(blueprint: BlueprintResult) -> str:
    lines = [
        "# Allowed Changes",
        "",
        "AI coders edit only inside these roots:",
        "",
    ]
    lines.extend(f"- `{root}`" for root in blueprint.allowed_change_roots)
    lines += ["", "## Per-task allowlists", ""]
    for task in blueprint.tasks:
        files = ", ".join(f"`{f}`" for f in task.allowed_files) or "(none)"
        lines.append(f"- {task.task_id}: {files}")
    lines += ["", "## Forbidden (never edit)", ""]
    lines.extend(f"- `{f}`" for f in blueprint.forbidden_changes)
    lines += [
        "",
        "Changing a forbidden file, the stack, or the dependency set is rule RMD-002/RMD-003 "
        "and will be rejected by validation.",
    ]
    return "\n".join(lines) + "\n"


def render_acceptance_md(blueprint: BlueprintResult) -> str:
    lines = ["# Acceptance Criteria", "", "## Per task", ""]
    for task in blueprint.tasks:
        lines.append(f"### {task.task_id}: {task.title}")
        lines.extend(f"- {c}" for c in task.acceptance_criteria)
        lines.append("")
    lines += ["## Commands that must pass before finishing", ""]
    lines.extend(f"- `{cmd}`" for cmd in blueprint.acceptance_commands)
    return "\n".join(lines).rstrip() + "\n"


def render_validation_md(blueprint: BlueprintResult, lock: StandardsLock | None) -> str:
    rule_lines = ""
    if lock and lock.rules:
        shown = ", ".join(lock.rules[:12])
        more = "" if len(lock.rules) <= 12 else f", … (+{len(lock.rules) - 12} more)"
        rule_lines = f"\nApplied rules: {shown}{more}\n"
    return (
        "# Validation\n"
        "\n"
        "After your AI coder finishes, validate the output against this contract:\n"
        "\n"
        "```bash\n"
        "agent-generator matrix validate --repo .\n"
        "```\n"
        "\n"
        "Validation checks: forbidden files unchanged, no unapproved dependencies, required "
        "files present, architecture matches MATRIX_BLUEPRINT.yaml, and the standards lock "
        "digest is intact.\n"
        f"{rule_lines}"
        "\n"
        "Result is one of: `approved`, `needs-repair` (with a repair prompt), or `rejected`.\n"
    )


def render_readme(blueprint: BlueprintResult, version: str) -> str:
    pages = "\n".join(f"- `{p}`" for p in blueprint.pages) or "- (none)"
    return (
        f"# {blueprint.name}\n"
        "\n"
        f"> {blueprint.idea}\n"
        "\n"
        f"Matrix Bundle `v{version}` — a controlled contract for AI coders. This is not a loose "
        "prompt: the AI coder implements the locked blueprint task by task.\n"
        "\n"
        "## Control files\n"
        "\n"
        "- `MATRIX_BLUEPRINT.yaml` — the locked architecture contract (do not edit).\n"
        "- `MATRIX_STANDARDS.lock` — the signed standards pinned to this build (do not edit).\n"
        "- `MATRIX_TASKS.md` — the ordered tasks to implement.\n"
        "- `MATRIX_ALLOWED_CHANGES.md` — exactly which files may change.\n"
        "- `MATRIX_ACCEPTANCE_CRITERIA.md` — when each task is done.\n"
        "- `MATRIX_VALIDATION.md` — how the result is validated.\n"
        "\n"
        "## Pages\n"
        "\n"
        f"{pages}\n"
        "\n"
        "## How to use\n"
        "\n"
        "1. Open `coder-prompts/` and copy the prompt for your AI coder.\n"
        "2. Let it implement one task at a time.\n"
        "3. Validate the output before shipping.\n"
    )


def render_architecture_doc(blueprint: BlueprintResult) -> str:
    stack = blueprint.stack
    routes = "\n".join(
        f"- `{r.method} {r.path}` — {r.summary or ''}".rstrip() for r in blueprint.api_routes
    )
    services = "\n".join(f"- {s}" for s in blueprint.services)
    return (
        f"# Architecture — {blueprint.name}\n"
        "\n"
        "## Stack\n"
        "\n"
        f"- Frontend: {stack.frontend}\n"
        f"- Backend: {stack.backend}\n"
        f"- Worker: {stack.worker or 'none'}\n"
        f"- Database: {stack.database or 'none'}\n"
        f"- Auth: {stack.auth}\n"
        f"- Deploy: {stack.deploy}\n"
        "\n"
        "## Services\n"
        "\n"
        f"{services}\n"
        "\n"
        "## API routes\n"
        "\n"
        f"{routes}\n"
        "\n"
        "This architecture is locked. New services, routes, or dependencies require a new "
        "blueprint version (see the Update requirements flow), not an in-place edit.\n"
    )


def render_security_doc(blueprint: BlueprintResult, lock: StandardsLock | None) -> str:
    profile = lock.quality_level.value if lock else blueprint.quality_level.value
    auth_note = (
        "Auth is enabled: use the hardened JWT + password-hashing profile, not the bare "
        "OAuth2 demo flow."
        if blueprint.stack.auth != "none"
        else "Auth was not requested; do not add authentication unless a new version asks for it."
    )
    return (
        f"# Security — {blueprint.name}\n"
        "\n"
        f"Quality profile: **{profile}**. Follows the Ruslan Magana Definitions and the OWASP "
        "ASVS / Top Ten / GenAI baselines pinned in `MATRIX_STANDARDS.lock`.\n"
        "\n"
        f"## Authentication\n\n{auth_note}\n"
        "\n"
        "## Agent safety\n\n"
        "- Untrusted input is segregated from system instructions (LLM01).\n"
        "- Model output is validated before reaching shell/API/file sinks (LLM05).\n"
        "- Tools are explicitly allowlisted; agency is bounded (LLM06).\n"
    )


def render_standards_report(blueprint: BlueprintResult, lock: StandardsLock | None) -> str:
    if not lock:
        return (
            "# Standards Report\n\nStandards pack was unavailable at generation time. "
            "Set MATRIX_DEFINITIONS_DIR and regenerate to pin a signed pack.\n"
        )
    return (
        "# Standards Report\n"
        "\n"
        f"- Pack: `{lock.definitions_pack.pack_id}` `{lock.definitions_pack.version}`\n"
        f"- Pack digest: `{lock.definitions_pack.checksum}`\n"
        f"- Quality level: `{lock.quality_level.value}`\n"
        f"- Rules applied: {len(lock.rules)}\n"
        "\n"
        "## Applied rule ids\n"
        "\n" + "\n".join(f"- {r}" for r in lock.rules) + "\n"
    )


__all__ = [
    "CONTROL_FILE_NAMES",
    "render_blueprint_yaml",
    "render_tasks_md",
    "render_allowed_changes_md",
    "render_acceptance_md",
    "render_validation_md",
    "render_readme",
    "render_architecture_doc",
    "render_security_doc",
    "render_standards_report",
]
