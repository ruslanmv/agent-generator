# backend/agents/builder_manager.py

import asyncio
import logging
from typing import Any, Dict, List, Callable, Coroutine

from .builders import py_tool_builder, mcp_tool_builder, yaml_agent_writer
from .merger_agent import MergerAgent

logger = logging.getLogger(__name__)

# Map task kinds to their corresponding builder function
_LEAF_BUILDERS: Dict[str, Callable[[Dict[str, Any], str], Coroutine[Any, Any, None]]] = {
    "python_tool": py_tool_builder.build,
    "mcp_tool": mcp_tool_builder.build,
}


class BuilderManager:
    """
    Orchestrates all build tasks in parallel, then merges the results.

    - Fans out each 'python_tool' and 'mcp_tool' task to its builder.
    - Always runs the YAML agent writer last.
    - Uses asyncio.gather for concurrency.
    - Returns a dict suitable for the /build response: {"framework": ..., "tree": [...]}
    """

    def __init__(self) -> None:
        self.merger = MergerAgent()

    async def build(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the build plan.

        Parameters
        ----------
        plan : dict
            A PlanResponse dict with keys:
              - selected_framework: str
              - build_tasks: List[dict]
        Returns
        -------
        dict
            {
              "framework": selected_framework,
              "tree": [ ... list of relative paths ... ]
            }
        """
        fw: str = plan.get("selected_framework", "")
        tasks: List[Dict[str, Any]] = plan.get("build_tasks", [])

        logger.info("Starting build for framework '%s' with %d tasks", fw, len(tasks))

        # Prepare coroutines for python_tool and mcp_tool builders
        coros: List[Coroutine[Any, Any, None]] = []
        for task in tasks:
            kind = task.get("kind")
            builder_fn = _LEAF_BUILDERS.get(kind)
            if not builder_fn:
                logger.warning("Unknown task kind '%s'; skipping", kind)
                continue
            coros.append(builder_fn(task, fw))
            logger.debug("Scheduled builder for task: %s", task)

        # Schedule the YAML agent writer as the final step
        coros.append(yaml_agent_writer.build(plan, fw))
        logger.debug("Scheduled YAML agent writer for framework '%s'", fw)

        # Execute all build tasks in parallel
        await asyncio.gather(*coros)
        logger.info("All build tasks completed for framework '%s'", fw)

        # Merge and return the final tree
        tree = self.merger.merge(fw)
        logger.info("Merged bundle contains %d artefacts", len(tree))

        return {"framework": fw, "tree": tree}
