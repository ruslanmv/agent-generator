"""Back-compat adapter between the legacy ``ProjectSpec`` and Matrix contracts.

The engine reuses the existing keyword planner (``application.planning_service.plan``),
which speaks ``ProjectSpec``. This module is the only place that knows how to translate
between that legacy world and the new shared contracts, so the rest of the engine can work
in contract terms while still driving the proven generation pipeline underneath.
"""

from __future__ import annotations

from agent_generator.application.planning_service import plan as _plan
from agent_generator.contracts.blueprint import BlueprintStack, BlueprintTask
from agent_generator.contracts.idea import IdeaRequest
from agent_generator.domain.project_spec import FrameworkChoice, ProjectSpec

#: Maps an agent framework to the closest Matrix stack defaults. Used only as a hint when
#: a blueprint does not pin its own stack.
_FRAMEWORK_BACKEND = {
    FrameworkChoice.CREWAI: "fastapi",
    FrameworkChoice.CREWAI_FLOW: "fastapi",
    FrameworkChoice.LANGGRAPH: "fastapi",
    FrameworkChoice.REACT: "fastapi",
    FrameworkChoice.WATSONX_ORCHESTRATE: "watsonx-orchestrate",
}


def idea_to_project_spec(
    idea: IdeaRequest,
    *,
    use_llm: bool = False,
) -> tuple[ProjectSpec, list[str]]:
    """Plan a legacy ``ProjectSpec`` from a Matrix ``IdeaRequest``.

    Returns ``(spec, warnings)``. Uses the keyword planner by default (no credentials
    required); ``use_llm`` is forwarded but only takes effect when a provider is wired.
    """
    framework = None
    for forbidden in idea.constraints.forbidden_stack:
        # nothing to do here yet; reserved for future stack filtering
        _ = forbidden
    spec, warnings = _plan(idea.idea, framework=framework, use_llm=use_llm)
    return spec, warnings


def project_spec_to_stack(
    spec: ProjectSpec,
    *,
    database: str | None = None,
    auth: str = "none",
    deploy: str = "docker",
) -> BlueprintStack:
    """Derive a Matrix ``BlueprintStack`` from a legacy ``ProjectSpec``."""
    backend = _FRAMEWORK_BACKEND.get(spec.framework, "fastapi")
    return BlueprintStack(
        frontend="nextjs",
        backend=backend,
        worker="python",
        database=database,
        auth=auth,
        deploy=deploy,
    )


def project_spec_to_tasks(spec: ProjectSpec, *, limit: int = 6) -> list[BlueprintTask]:
    """Map ``ProjectSpec`` tasks onto controlled ``BlueprintTask`` entries.

    Legacy task ids are snake_case and free-form; controlled tasks use the ``TASK-NNN``
    contract id, so we re-number deterministically by position.
    """
    tasks: list[BlueprintTask] = []
    for index, task in enumerate(spec.tasks[:limit], start=1):
        slug = task.id.replace("_", "-")
        tasks.append(
            BlueprintTask(
                task_id=f"TASK-{index:03d}",
                title=task.description[:120].strip() or f"Implement {slug}",
                allowed_files=[
                    f"backend/app/{slug}.py",
                    f"backend/tests/test_{task.id}.py",
                ],
                acceptance_criteria=[
                    task.expected_output[:160].strip() or "Produces the expected output",
                    "No Matrix control files changed",
                ],
            )
        )
    if not tasks:
        tasks.append(
            BlueprintTask(
                task_id="TASK-001",
                title="Implement the first controlled route and tests",
                allowed_files=[
                    "backend/app/api/routes.py",
                    "backend/tests/test_routes.py",
                ],
                acceptance_criteria=["Endpoint exists", "Tests pass"],
            )
        )
    return tasks


__all__ = [
    "idea_to_project_spec",
    "project_spec_to_stack",
    "project_spec_to_tasks",
]
