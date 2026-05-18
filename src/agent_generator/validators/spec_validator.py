"""Deep validation of a ProjectSpec for completeness and consistency."""

from __future__ import annotations

from pydantic import BaseModel, Field

from agent_generator.domain.project_spec import ProjectSpec


class ValidationResult(BaseModel):
    """Result of a validation pass, containing errors and warnings."""

    valid: bool = True
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class SpecValidator:
    """Deep validation of a ProjectSpec beyond Pydantic schema constraints.

    Checks for semantic correctness: unique IDs, valid cross-references,
    circular dependencies, and structural soundness.
    """

    def validate(self, spec: ProjectSpec) -> ValidationResult:
        """Run all validation checks against a ProjectSpec.

        Args:
            spec: The ProjectSpec to validate.

        Returns:
            A ValidationResult with any errors and warnings found.
        """
        errors: list[str] = []
        warnings: list[str] = []

        agent_ids = [a.id for a in spec.agents]
        task_ids = [t.id for t in spec.tasks]
        agent_id_set = set(agent_ids)
        task_id_set = set(task_ids)

        # 1. Agent ID uniqueness
        if len(agent_ids) != len(agent_id_set):
            errors.append("Duplicate agent IDs detected")

        # 2. Task ID uniqueness
        if len(task_ids) != len(task_id_set):
            errors.append("Duplicate task IDs detected")

        # 3. Every task references a valid agent
        for t in spec.tasks:
            if t.agent_id not in agent_id_set:
                errors.append(f"Task '{t.id}' references unknown agent '{t.agent_id}'")

        # 4. Every depends_on references a valid task
        for t in spec.tasks:
            for dep in t.depends_on:
                if dep not in task_id_set:
                    errors.append(f"Task '{t.id}' depends on unknown task '{dep}'")

        # 5. No circular dependencies
        if self._has_cycle(spec.tasks):
            errors.append("Circular task dependency detected")

        # 6. At least one entry-point task (no dependencies)
        if spec.tasks and all(t.depends_on for t in spec.tasks):
            warnings.append("No entry-point task found (all tasks have dependencies)")

        # 7. Tool ID uniqueness
        tool_ids = [t.id for t in spec.tools]
        if len(tool_ids) != len(set(tool_ids)):
            errors.append("Duplicate tool IDs detected")

        # 8. Agent tool references point to defined tools
        tool_id_set = set(tool_ids)
        for agent in spec.agents:
            for tool_ref in agent.tools:
                if tool_ref not in tool_id_set:
                    warnings.append(f"Agent '{agent.id}' references undefined tool '{tool_ref}'")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def _has_cycle(self, tasks: list) -> bool:
        """Detect cycles in task dependencies using DFS."""
        graph: dict[str, list[str]] = {t.id: list(t.depends_on) for t in tasks}
        visited: set[str] = set()
        in_stack: set[str] = set()

        def dfs(node: str) -> bool:
            if node in in_stack:
                return True
            if node in visited:
                return False
            visited.add(node)
            in_stack.add(node)
            for dep in graph.get(node, []):
                if dfs(dep):
                    return True
            in_stack.discard(node)
            return False

        return any(dfs(t.id) for t in tasks if t.id not in visited)
