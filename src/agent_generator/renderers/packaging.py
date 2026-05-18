"""Packaging utilities — ZIP bundling, pyproject.toml, README, .gitignore."""

from __future__ import annotations

import io
import textwrap
import zipfile

from agent_generator.domain.project_spec import ProjectSpec
from agent_generator.domain.render_plan import RenderPlan


class Packager:
    """Utility class for packaging rendered project files."""

    @staticmethod
    def to_zip(files: dict[str, str], project_name: str) -> bytes:
        """Bundle rendered files into a ZIP archive.

        Parameters
        ----------
        files:
            Mapping of ``relative_path -> file_content``.
        project_name:
            Root directory name inside the ZIP.

        Returns
        -------
        bytes
            In-memory ZIP file content.
        """
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for path, content in sorted(files.items()):
                arcname = f"{project_name}/{path}"
                zf.writestr(arcname, content)
        return buf.getvalue()

    @staticmethod
    def generate_pyproject(spec: ProjectSpec, plan: RenderPlan) -> str:
        """Generate a ``pyproject.toml`` for the project.

        Parameters
        ----------
        spec:
            Canonical project specification.
        plan:
            Render plan with dependency information.

        Returns
        -------
        str
            Rendered ``pyproject.toml`` content.
        """
        deps_list = [f'"{d}"' for d in plan.dependencies]
        if plan.framework_version:
            deps_list.insert(0, f'"{plan.framework_version}"')
        deps_lines = ",\n".join(f"  {d}" for d in deps_list)

        lines = [
            "[build-system]",
            'requires      = ["hatchling>=1.18"]',
            'build-backend = "hatchling.build"',
            "",
            "[project]",
            f'name            = "{spec.name}"',
            'version         = "0.1.0"',
            f'description     = "{spec.description}"',
            'requires-python = ">=3.10"',
            'license         = { text = "MIT" }',
            "",
            "dependencies = [",
            deps_lines,
            "]",
            "",
            "[project.scripts]",
            f'{spec.name} = "main:main"',
            "",
        ]
        return "\n".join(lines) + "\n"

    @staticmethod
    def generate_readme(spec: ProjectSpec) -> str:
        """Generate a project README.md.

        Parameters
        ----------
        spec:
            Canonical project specification.

        Returns
        -------
        str
            Rendered README content.
        """
        agents_section = "\n".join(f"- **{a.role}**: {a.goal}" for a in spec.agents)
        tasks_section = "\n".join(f"- **{t.id}**: {t.description}" for t in spec.tasks)

        return textwrap.dedent(f"""\
            # {spec.name}

            {spec.description}

            ## Framework

            {spec.framework.value}

            ## Agents

            {agents_section}

            ## Tasks

            {tasks_section}

            ## Getting Started

            1. Install dependencies:

               ```bash
               pip install -e .
               ```

            2. Run the project:

               ```bash
               python src/main.py
               ```
        """)

    @staticmethod
    def generate_gitignore() -> str:
        """Generate a standard Python .gitignore.

        Returns
        -------
        str
            .gitignore content.
        """
        return textwrap.dedent("""\
            # Byte-compiled / optimized / DLL files
            __pycache__/
            *.py[cod]
            *$py.class

            # Distribution / packaging
            dist/
            build/
            *.egg-info/

            # Virtual environments
            .env
            .venv/
            venv/
            ENV/

            # IDE
            .idea/
            .vscode/
            *.swp
            *.swo

            # Testing / linting caches
            .mypy_cache/
            .ruff_cache/
            .pytest_cache/
            htmlcov/
            .coverage

            # OS files
            .DS_Store
            Thumbs.db
        """)
