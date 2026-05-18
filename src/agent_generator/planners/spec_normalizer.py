"""Validate and normalize a ProjectSpec after LLM generation.

Performs compatibility checks, reference validation, and cycle detection.
Returns a corrected spec along with a list of warnings about adjustments made.
"""

from __future__ import annotations

from collections import deque

from agent_generator.domain.capability_matrix import supported_modes, validate_combination
from agent_generator.domain.project_spec import ArtifactMode, ProjectSpec

KNOWN_TOOL_TEMPLATES = frozenset(
    {
        "web_search",
        "pdf_reader",
        "http_client",
        "sql_query",
        "vector_search",
        "file_writer",
    }
)


class SpecNormalizer:
    """Validate references, fix inconsistencies, and report warnings."""

    def normalize(self, spec: ProjectSpec) -> tuple[ProjectSpec, list[str]]:
        """Normalize a ProjectSpec and return it with any warnings.

        Checks performed:
        1. Capability matrix compatibility (adjusts artifact_mode if needed).
        2. Tool template references exist in the known catalog.
        3. Agent ID references in tasks are valid.
        4. Task dependency references are valid.
        5. No circular dependencies (topological sort check).
        6. Tool references in agent specs point to defined tools.

        Args:
            spec: The ProjectSpec to normalize.

        Returns:
            Tuple of (possibly modified ProjectSpec, list of warning strings).
        """
        warnings: list[str] = []

        self._check_capability_matrix(spec, warnings)
        self._check_tool_templates(spec, warnings)
        self._check_agent_references(spec, warnings)
        self._check_task_dependencies(spec, warnings)
        self._check_circular_dependencies(spec, warnings)
        self._check_agent_tool_references(spec, warnings)

        return spec, warnings

    def _check_capability_matrix(self, spec: ProjectSpec, warnings: list[str]) -> None:
        """Adjust artifact_mode if unsupported by the chosen framework."""
        if not validate_combination(spec.framework.value, spec.artifact_mode.value):
            available = supported_modes(spec.framework.value)
            if available:
                original = spec.artifact_mode.value
                spec.artifact_mode = ArtifactMode(available[0])
                warnings.append(
                    f"Adjusted artifact_mode from '{original}' to "
                    f"'{spec.artifact_mode.value}' "
                    f"(unsupported for {spec.framework.value})"
                )

    def _check_tool_templates(self, spec: ProjectSpec, warnings: list[str]) -> None:
        """Ensure all tool templates reference known catalog entries."""
        for tool in spec.tools:
            if tool.template not in KNOWN_TOOL_TEMPLATES:
                warnings.append(
                    f"Unknown tool template '{tool.template}', " f"defaulting to 'http_client'"
                )
                tool.template = "http_client"

    def _check_agent_references(self, spec: ProjectSpec, warnings: list[str]) -> None:
        """Ensure all tasks reference valid agent IDs."""
        agent_ids = {a.id for a in spec.agents}
        for task in spec.tasks:
            if task.agent_id not in agent_ids:
                fallback = spec.agents[0].id
                warnings.append(
                    f"Task '{task.id}' references unknown agent "
                    f"'{task.agent_id}', reassigned to '{fallback}'"
                )
                task.agent_id = fallback

    def _check_task_dependencies(self, spec: ProjectSpec, warnings: list[str]) -> None:
        """Remove invalid task dependency references."""
        task_ids = {t.id for t in spec.tasks}
        for task in spec.tasks:
            invalid = [d for d in task.depends_on if d not in task_ids]
            if invalid:
                warnings.append(f"Task '{task.id}' has invalid depends_on: {invalid}, removed")
                task.depends_on = [d for d in task.depends_on if d in task_ids]

    def _check_circular_dependencies(self, spec: ProjectSpec, warnings: list[str]) -> None:
        """Detect circular dependencies using Kahn's topological sort algorithm."""
        task_ids = {t.id for t in spec.tasks}
        graph: dict[str, list[str]] = {t.id: list(t.depends_on) for t in spec.tasks}
        in_degree: dict[str, int] = {tid: 0 for tid in task_ids}

        for tid, deps in graph.items():
            for dep in deps:
                if dep in in_degree:
                    in_degree[dep] = in_degree.get(dep, 0)
                    # dep has tid depending on it; tid's in_degree is already set
                    pass

        # Build adjacency list (dependency -> dependents)
        adjacency: dict[str, list[str]] = {tid: [] for tid in task_ids}
        in_degree = {tid: 0 for tid in task_ids}
        for tid, deps in graph.items():
            for dep in deps:
                if dep in adjacency:
                    adjacency[dep].append(tid)
                    in_degree[tid] += 1

        queue: deque[str] = deque(tid for tid, deg in in_degree.items() if deg == 0)
        visited_count = 0
        while queue:
            node = queue.popleft()
            visited_count += 1
            for neighbor in adjacency.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if visited_count < len(task_ids):
            warnings.append(
                "Circular task dependency detected; "
                "clearing depends_on for all tasks in the cycle"
            )
            # Break cycles by clearing all depends_on
            for task in spec.tasks:
                task.depends_on = []

    def _check_agent_tool_references(self, spec: ProjectSpec, warnings: list[str]) -> None:
        """Ensure agents only reference tools defined in the spec."""
        tool_ids = {t.id for t in spec.tools}
        for agent in spec.agents:
            invalid_tools = [t for t in agent.tools if t not in tool_ids]
            if invalid_tools:
                warnings.append(
                    f"Agent '{agent.id}' references unknown tools: " f"{invalid_tools}, removed"
                )
                agent.tools = [t for t in agent.tools if t in tool_ids]
