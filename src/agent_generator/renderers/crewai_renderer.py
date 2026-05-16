"""CrewAI project renderer — generates a complete CrewAI 1.x project."""

from __future__ import annotations

import textwrap

import yaml

from agent_generator.domain.project_spec import ArtifactMode, ProjectSpec, ToolSpec
from agent_generator.domain.render_plan import RenderPlan
from agent_generator.renderers.base import BaseRenderer


class CrewAIRenderer(BaseRenderer):
    """Render a full CrewAI project structure.

    Supports two artifact modes:

    * **code_and_yaml** — idiomatic CrewAI 1.x layout with YAML configs,
      ``@agent`` / ``@task`` / ``@crew`` decorators, tool modules, tests,
      and packaging files.
    * **code_only** — a single ``main.py`` with everything inline
      (backward-compatible).
    """

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #

    def render(
        self,
        spec: ProjectSpec,
        plan: RenderPlan,
    ) -> dict[str, str]:
        if spec.artifact_mode == ArtifactMode.CODE_AND_YAML:
            return self._render_full_project(spec, plan)
        return self._render_code_only(spec, plan)

    # ================================================================== #
    #  code_and_yaml mode
    # ================================================================== #

    def _render_full_project(
        self,
        spec: ProjectSpec,
        plan: RenderPlan,
    ) -> dict[str, str]:
        files: dict[str, str] = {}

        tool_index = {t.id: t for t in spec.tools}
        # Collect all unique tool IDs referenced by agents
        all_tool_ids: list[str] = []
        seen: set[str] = set()
        for agent in spec.agents:
            for tid in agent.tools:
                if tid not in seen:
                    all_tool_ids.append(tid)
                    seen.add(tid)

        # --- config/agents.yaml ---
        files["config/agents.yaml"] = self._gen_agents_yaml(spec)

        # --- config/tasks.yaml ---
        files["config/tasks.yaml"] = self._gen_tasks_yaml(spec)

        # --- src/crew.py ---
        files["src/crew.py"] = self._gen_crew_py(spec, all_tool_ids)

        # --- src/main.py ---
        files["src/main.py"] = self._gen_main_py(spec)

        # --- src/tools/__init__.py ---
        files["src/tools/__init__.py"] = self._gen_tools_init(all_tool_ids)

        # --- Individual tool modules ---
        for tid in all_tool_ids:
            tool_spec = tool_index.get(tid)
            if tool_spec is not None:
                files[f"src/tools/{tid}.py"] = self._render_tool(tool_spec)

        # --- tests/test_smoke.py ---
        files["tests/test_smoke.py"] = self._gen_smoke_test(spec)

        # --- pyproject.toml ---
        files["pyproject.toml"] = self._gen_pyproject(spec, plan, tool_index, all_tool_ids)

        # --- README.md ---
        files["README.md"] = self._gen_readme(spec)

        # --- .env.example ---
        files[".env.example"] = self._gen_env_example(spec, tool_index, all_tool_ids)

        # --- .gitignore ---
        files[".gitignore"] = self._gen_gitignore()

        return files

    # ------------------------------------------------------------------ #
    #  YAML configs
    # ------------------------------------------------------------------ #

    def _gen_agents_yaml(self, spec: ProjectSpec) -> str:
        agents: dict[str, dict] = {}
        for a in spec.agents:
            entry: dict[str, object] = {
                "role": a.role,
                "goal": a.goal,
                "backstory": a.backstory or f"You are the {a.role}.",
            }
            if a.llm_override:
                entry["llm"] = a.llm_override
            agents[a.id] = entry
        return yaml.dump(agents, default_flow_style=False, sort_keys=False)

    def _gen_tasks_yaml(self, spec: ProjectSpec) -> str:
        tasks: dict[str, dict] = {}
        for t in spec.tasks:
            tasks[t.id] = {
                "description": t.description,
                "expected_output": t.expected_output,
                "agent": t.agent_id,
            }
        return yaml.dump(tasks, default_flow_style=False, sort_keys=False)

    # ------------------------------------------------------------------ #
    #  Python sources
    # ------------------------------------------------------------------ #

    def _gen_crew_py(self, spec: ProjectSpec, all_tool_ids: list[str]) -> str:
        tool_imports = ""
        if all_tool_ids:
            names = ", ".join(all_tool_ids)
            tool_imports = f"from tools import {names}"

        agent_methods: list[str] = []
        for a in spec.agents:
            tool_list = f"[{', '.join(a.tools)}]" if a.tools else "[]"
            agent_methods.append(
                f"    @agent\n"
                f"    def {a.id}(self) -> Agent:\n"
                f"        return Agent(\n"
                f'            config=self.agents_config["{a.id}"],\n'
                f"            tools={tool_list},\n"
                f"            verbose=True,\n"
                f"        )\n"
            )

        task_methods: list[str] = []
        for t in spec.tasks:
            task_methods.append(
                f"    @task\n"
                f"    def {t.id}(self) -> Task:\n"
                f"        return Task(\n"
                f'            config=self.tasks_config["{t.id}"],\n'
                f"        )\n"
            )

        agent_refs = ", ".join(f"self.{a.id}()" for a in spec.agents)
        task_refs = ", ".join(f"self.{t.id}()" for t in spec.tasks)

        class_name = _to_class_name(spec.name)

        lines = [
            f'"""CrewAI crew definition for {spec.name}."""',
            "from crewai import Agent, Crew, Process, Task",
            "from crewai.project import CrewBase, agent, crew, task",
        ]
        if tool_imports:
            lines.append(tool_imports)
        lines.append("")
        lines.append("")
        lines.append("@CrewBase")
        lines.append(f"class {class_name}:")
        lines.append(f'    """Crew for: {spec.description}"""')
        lines.append("")
        lines.append('    agents_config = "config/agents.yaml"')
        lines.append('    tasks_config = "config/tasks.yaml"')
        lines.append("")
        for m in agent_methods:
            lines.append(m)
        for m in task_methods:
            lines.append(m)
        lines.append("    @crew")
        lines.append("    def crew(self) -> Crew:")
        lines.append("        return Crew(")
        lines.append(f"            agents=[{agent_refs}],")
        lines.append(f"            tasks=[{task_refs}],")
        lines.append("            process=Process.sequential,")
        lines.append("            verbose=True,")
        lines.append("        )")
        lines.append("")

        return "\n".join(lines) + "\n"

    def _gen_main_py(self, spec: ProjectSpec) -> str:
        class_name = _to_class_name(spec.name)
        return textwrap.dedent(f"""\
            \"\"\"Entry point for {spec.name}.\"\"\"
            import sys
            from crew import {class_name}


            def main() -> None:
                \"\"\"Run the crew.\"\"\"
                inputs = {{}}
                result = {class_name}().crew().kickoff(inputs=inputs)
                print(result)


            if __name__ == "__main__":
                main()
        """)

    def _gen_tools_init(self, all_tool_ids: list[str]) -> str:
        lines = [f"from .{tid} import {tid}" for tid in all_tool_ids]
        if not lines:
            return ""
        lines.append("")  # trailing newline
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    #  Tests
    # ------------------------------------------------------------------ #

    def _gen_smoke_test(self, spec: ProjectSpec) -> str:
        class_name = _to_class_name(spec.name)
        return textwrap.dedent(f"""\
            \"\"\"Smoke tests for {spec.name}.\"\"\"
            import pytest
            from crew import {class_name}


            def test_crew_instantiation():
                \"\"\"Verify the crew class can be instantiated.\"\"\"
                crew_instance = {class_name}()
                assert crew_instance is not None


            def test_crew_has_agents():
                \"\"\"Verify the crew defines agents.\"\"\"
                crew_obj = {class_name}().crew()
                assert len(crew_obj.agents) > 0


            def test_crew_has_tasks():
                \"\"\"Verify the crew defines tasks.\"\"\"
                crew_obj = {class_name}().crew()
                assert len(crew_obj.tasks) > 0
        """)

    # ------------------------------------------------------------------ #
    #  Packaging
    # ------------------------------------------------------------------ #

    def _gen_pyproject(
        self,
        spec: ProjectSpec,
        plan: RenderPlan,
        tool_index: dict[str, ToolSpec],
        all_tool_ids: list[str],
    ) -> str:
        fw_version = plan.framework_version or "crewai==1.12.2"
        deps = [f'  "{fw_version}"']

        # Collect tool-specific dependencies
        extra: set[str] = set()
        for tid in all_tool_ids:
            ts = tool_index.get(tid)
            if ts and ts.template in _TOOL_DEPS:
                for d in _TOOL_DEPS[ts.template]:
                    extra.add(d)
        for d in sorted(extra):
            deps.append(f'  "{d}"')

        dep_block = ",\n".join(deps)

        return textwrap.dedent(f"""\
            [build-system]
            requires      = ["hatchling>=1.18"]
            build-backend = "hatchling.build"

            [project]
            name            = "{spec.name}"
            version         = "0.1.0"
            description     = "{spec.description}"
            requires-python = ">=3.10"

            dependencies = [
            {dep_block},
            ]

            [project.scripts]
            {spec.name} = "main:main"
        """)

    def _gen_readme(self, spec: ProjectSpec) -> str:
        agents_list = "\n".join(f"- **{a.role}**: {a.goal}" for a in spec.agents)
        tasks_list = "\n".join(f"- **{t.id}**: {t.description}" for t in spec.tasks)

        return textwrap.dedent(f"""\
            # {spec.name}

            {spec.description}

            ## Agents

            {agents_list}

            ## Tasks

            {tasks_list}

            ## Getting Started

            1. Install dependencies:

               ```bash
               pip install -e .
               ```

            2. Copy `.env.example` to `.env` and fill in required values.

            3. Run the crew:

               ```bash
               python src/main.py
               ```

            ## Project Structure

            ```
            config/
              agents.yaml     # Agent definitions
              tasks.yaml      # Task definitions
            src/
              main.py          # Entry point
              crew.py          # Crew class with @agent, @task, @crew decorators
              tools/           # Tool implementations
            tests/
              test_smoke.py    # Smoke tests
            ```
        """)

    def _gen_env_example(
        self,
        spec: ProjectSpec,
        tool_index: dict[str, ToolSpec],
        all_tool_ids: list[str],
    ) -> str:
        lines = ["# Required environment variables", ""]

        # LLM provider keys
        provider = spec.llm.provider.lower()
        if provider == "openai":
            lines.append("OPENAI_API_KEY=")
        elif provider in {"watsonx", "ibm"}:
            lines.append("WATSONX_API_KEY=")
            lines.append("WATSONX_PROJECT_ID=")
        else:
            lines.append(f"# LLM provider: {provider}")

        # Tool-specific env vars
        for tid in all_tool_ids:
            ts = tool_index.get(tid)
            if ts:
                for key, val in ts.inputs.items():
                    if key.endswith("_env_var"):
                        lines.append(f"{val}=")

        lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _gen_gitignore() -> str:
        return textwrap.dedent("""\
            __pycache__/
            *.py[cod]
            *$py.class
            .env
            .venv/
            venv/
            dist/
            build/
            *.egg-info/
            .mypy_cache/
            .ruff_cache/
            .pytest_cache/
        """)

    # ================================================================== #
    #  code_only mode
    # ================================================================== #

    def _render_code_only(
        self,
        spec: ProjectSpec,
        plan: RenderPlan,
    ) -> dict[str, str]:
        tool_index = {t.id: t for t in spec.tools}

        # Inline tool code blocks
        tool_blocks: list[str] = []
        for agent in spec.agents:
            for tid in agent.tools:
                ts = tool_index.get(tid)
                if ts is not None:
                    tool_blocks.append(self._render_tool(ts))

        tool_code = "\n\n".join(tool_blocks)

        agents_code = ""
        for a in spec.agents:
            tool_list = ", ".join(a.tools) if a.tools else ""
            agents_code += textwrap.dedent(f"""\
                {a.id} = Agent(
                    role="{a.role}",
                    goal="{a.goal}",
                    backstory=\"\"\"{a.backstory or f"You are the {a.role}."}\"\"\",
                    tools=[{tool_list}],
                    verbose=True,
                )

            """)

        tasks_code = ""
        for t in spec.tasks:
            tasks_code += textwrap.dedent(f"""\
                {t.id} = Task(
                    description=\"\"\"{t.description}\"\"\",
                    agent={t.agent_id},
                    expected_output=\"\"\"{t.expected_output}\"\"\",
                )

            """)

        agent_refs = ", ".join(a.id for a in spec.agents)
        task_refs = ", ".join(t.id for t in spec.tasks)

        main_py = textwrap.dedent(f"""\
            \"\"\"Auto-generated CrewAI project — {spec.name}.\"\"\"
            from crewai import Agent, Crew, Process, Task
            from crewai.tools import tool

            {tool_code}

            # --- Agents ---

            {agents_code}
            # --- Tasks ---

            {tasks_code}
            # --- Crew ---

            crew = Crew(
                agents=[{agent_refs}],
                tasks=[{task_refs}],
                process=Process.sequential,
                verbose=True,
            )


            def main():
                \"\"\"Run the crew.\"\"\"
                result = crew.kickoff()
                print(result)
                return result


            if __name__ == "__main__":
                main()
        """)

        return {"main.py": main_py}


# ────────────────────────────────────────────────────────────────
#  Internal helpers
# ────────────────────────────────────────────────────────────────

_TOOL_DEPS: dict[str, list[str]] = {
    "web_search": ["requests"],
    "pdf_reader": ["PyPDF2"],
    "http_client": ["requests"],
    "sql_query": ["sqlalchemy"],
    "file_writer": [],
    "vector_search": ["chromadb"],
}


def _to_class_name(kebab_name: str) -> str:
    """Convert a kebab-case project name to PascalCase class name."""
    return "".join(part.capitalize() for part in kebab_name.split("-")) + "Crew"
