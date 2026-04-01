"""Base renderer — abstract interface for all code-generation backends."""
from __future__ import annotations

from abc import ABC, abstractmethod

from jinja2 import Environment, PackageLoader

from agent_generator.domain.project_spec import ProjectSpec, ToolSpec
from agent_generator.domain.render_plan import RenderPlan
from agent_generator.tools.registry import render_tool


class BaseRenderer(ABC):
    """Abstract base class for project renderers.

    Every concrete renderer must implement :meth:`render`, which takes a
    ``ProjectSpec`` and ``RenderPlan`` and produces a mapping of
    ``relative_path -> file_content``.
    """

    def __init__(self) -> None:
        self._jinja_env = Environment(
            loader=PackageLoader("agent_generator", "renderers/templates"),
            keep_trailing_newline=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    # ------------------------------------------------------------------ #
    #  Abstract API
    # ------------------------------------------------------------------ #

    @abstractmethod
    def render(
        self,
        spec: ProjectSpec,
        plan: RenderPlan,
    ) -> dict[str, str]:
        """Generate all project files.

        Parameters
        ----------
        spec:
            Canonical project specification.
        plan:
            Deterministic plan of artifacts to generate.

        Returns
        -------
        dict[str, str]
            Mapping of ``relative_path -> rendered_content``.
        """

    # ------------------------------------------------------------------ #
    #  Shared helpers
    # ------------------------------------------------------------------ #

    def _render_template(self, template_name: str, **context: object) -> str:
        """Render a Jinja2 template from the ``renderers/templates`` package directory.

        Parameters
        ----------
        template_name:
            Template file name (e.g. ``"crewai/main.py.j2"``).
        **context:
            Template variables.

        Returns
        -------
        str
            Rendered template content.
        """
        template = self._jinja_env.get_template(template_name)
        return template.render(**context)

    @staticmethod
    def _render_tool(tool_spec: ToolSpec) -> str:
        """Render a tool from the catalog.

        Parameters
        ----------
        tool_spec:
            The tool specification containing the catalog template key
            and any template-level inputs.

        Returns
        -------
        str
            Rendered Python source for the tool.
        """
        return render_tool(tool_spec.template, tool_spec.inputs)
