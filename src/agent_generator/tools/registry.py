"""Tool template registry — maps tool IDs to Jinja2 catalog templates."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from jinja2 import Environment, FileSystemLoader


@dataclass(frozen=True)
class ToolTemplate:
    """Metadata for an approved tool template in the catalog."""

    id: str
    description: str
    deps: list[str] = field(default_factory=list)
    inputs: list[str] = field(default_factory=list)


# ────────────────────────────────────────────────────────────────
#  Approved tool catalog
# ────────────────────────────────────────────────────────────────

TOOL_CATALOG: dict[str, ToolTemplate] = {
    "web_search": ToolTemplate(
        id="web_search",
        description="Search the web for information",
        deps=["requests"],
        inputs=["api_key_env_var"],
    ),
    "pdf_reader": ToolTemplate(
        id="pdf_reader",
        description="Extract text from PDF files",
        deps=["PyPDF2"],
        inputs=[],
    ),
    "http_client": ToolTemplate(
        id="http_client",
        description="Make HTTP API requests",
        deps=["requests"],
        inputs=["base_url"],
    ),
    "sql_query": ToolTemplate(
        id="sql_query",
        description="Query SQL databases",
        deps=["sqlalchemy"],
        inputs=["connection_string_env_var"],
    ),
    "file_writer": ToolTemplate(
        id="file_writer",
        description="Write content to files",
        deps=[],
        inputs=["output_dir"],
    ),
    "vector_search": ToolTemplate(
        id="vector_search",
        description="Semantic vector search",
        deps=["chromadb"],
        inputs=["collection_name"],
    ),
}

# ────────────────────────────────────────────────────────────────
#  Template rendering
# ────────────────────────────────────────────────────────────────

_CATALOG_DIR = Path(__file__).resolve().parent / "catalog"

_env = Environment(
    loader=FileSystemLoader(str(_CATALOG_DIR)),
    keep_trailing_newline=True,
    trim_blocks=True,
    lstrip_blocks=True,
)


def render_tool(tool_id: str, inputs: dict[str, str] | None = None) -> str:
    """Render a tool template from the catalog.

    Parameters
    ----------
    tool_id:
        Key in ``TOOL_CATALOG`` (e.g. ``"web_search"``).
    inputs:
        Template variables specific to this tool instance.

    Returns
    -------
    str
        Rendered Python source code for the tool.

    Raises
    ------
    KeyError
        If *tool_id* is not in the catalog.
    """
    if tool_id not in TOOL_CATALOG:
        raise KeyError(f"Unknown tool '{tool_id}'. " f"Available: {sorted(TOOL_CATALOG)}")
    template = _env.get_template(f"{tool_id}.py.j2")
    return template.render(**(inputs or {}))
