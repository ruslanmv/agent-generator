# ────────────────────────────────────────────────────────────────
#  src/agent_generator/frameworks/base.py
# ────────────────────────────────────────────────────────────────
"""
Base class + registry for every code‑generation backend.

Concrete generators live in sub‑packages (crewai, langgraph, …) and must
implement `_emit_core_code(workflow, settings)`.

`generate_code()` handles cross‑cutting extras:

* Adds a minimal **MCP server scaffold** when `mcp=True` *and* the
  output is Python.
* Returns the final source string (framework generators decide whether
  that’s `.py` or `.yaml`).

Downstream usage:
-----------------
    from agent_generator.frameworks import FRAMEWORKS
    code = FRAMEWORKS["crewai"]().generate_code(workflow, settings, mcp=True)
"""

from __future__ import annotations

import textwrap
from abc import ABC, abstractmethod
from typing import ClassVar, Dict, Type

from agent_generator.config import Settings
from agent_generator.models.workflow import Workflow

# Public registry populated via BaseFrameworkGenerator.__init_subclass__
FRAMEWORKS: Dict[str, Type["BaseFrameworkGenerator"]] = {}


# ────────────────────────────────────────────────
# Abstract base
# ────────────────────────────────────────────────


class BaseFrameworkGenerator(ABC):
    """
    Abstract interface every framework generator must implement.

    Subclass attributes
    -------------------
    framework : str
        Registry key (e.g. "crewai").
    file_extension : str
        "py" or "yaml". Dictates whether MCP wrapping is allowed.
    """

    framework: ClassVar[str] = "base"
    file_extension: ClassVar[str] = "txt"

    # Registry magic
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.framework == "base":
            # Don't register the base class itself
            return
        if cls.framework in FRAMEWORKS:
            raise RuntimeError(f"Duplicate framework key: {cls.framework}")
        FRAMEWORKS[cls.framework] = cls

    # Public API
    def generate_code(
        self,
        workflow: Workflow,
        settings: Settings,
        *,
        mcp: bool = False,
    ) -> str:
        """
        Orchestrate code emission + optional MCP scaffold.

        Parameters
        ----------
        workflow : Workflow
            Validated Workflow object.
        settings : Settings
            Global config instance.
        mcp : bool
            If True and file is Python, append MCP server wrapper.

        Returns
        -------
        str
            Full source code or YAML.
        """
        core_code = self._emit_core_code(workflow, settings).rstrip() + "\n"

        if mcp and self.file_extension == "py":
            core_code = self._wrap_mcp_server(core_code, settings.mcp_default_port)

        return core_code

    @abstractmethod
    def _emit_core_code(self, workflow: Workflow, settings: Settings) -> str:
        """
        Framework-specific generator method to be implemented by subclasses.
        """

    @staticmethod
    def _wrap_mcp_server(code: str, port: int) -> str:
        """
        Append a tiny FastAPI MCP server so the file can be dockerised and
        registered in an MCP Gateway.

        Expects the core code to expose `main()` returning serialisable output.
        """
        wrapper = textwrap.dedent(
            f"""
            # ──────────────────────────────────────────────────────
            #  MCP HTTP wrapper (auto‑generated)
            # ──────────────────────────────────────────────────────
            if __name__ == "__main__":
                import json
                from fastapi import FastAPI
                from fastapi.middleware.cors import CORSMiddleware
                import uvicorn

                app = FastAPI(title="agent-generator MCP skill")

                app.add_middleware(
                    CORSMiddleware,
                    allow_origins=["*"],
                    allow_credentials=True,
                    allow_methods=["*"],
                    allow_headers=["*"],
                )

                @app.post("/invoke")
                async def invoke():
                    result = main()  # type: ignore[name-defined]
                    return json.loads(json.dumps(result, default=str))

                uvicorn.run(app, host="0.0.0.0", port={port})
            """
        ).lstrip()

        return f"{code}\n{wrapper}"


__all__ = ["BaseFrameworkGenerator", "FRAMEWORKS"]
