"""Framework capability matrix -- what each framework supports."""
from __future__ import annotations

CAPABILITY_MATRIX: dict[str, dict[str, bool]] = {
    "crewai": {
        "code_only": True,
        "yaml_only": True,
        "code_and_yaml": True,
        "tool_templates": True,
        "mcp_wrapper": True,
    },
    "crewai_flow": {
        "code_only": True,
        "yaml_only": False,
        "code_and_yaml": False,
        "tool_templates": True,
        "mcp_wrapper": True,
    },
    "langgraph": {
        "code_only": True,
        "yaml_only": False,
        "code_and_yaml": False,
        "tool_templates": True,
        "mcp_wrapper": True,
    },
    "react": {
        "code_only": True,
        "yaml_only": False,
        "code_and_yaml": False,
        "tool_templates": True,
        "mcp_wrapper": True,
    },
    "watsonx_orchestrate": {
        "code_only": False,
        "yaml_only": True,
        "code_and_yaml": False,
        "tool_templates": False,
        "mcp_wrapper": False,
    },
}


def validate_combination(framework: str, mode: str) -> bool:
    """Return True if the given artifact mode is supported by the framework."""
    return CAPABILITY_MATRIX.get(framework, {}).get(mode, False)


def supported_modes(framework: str) -> list[str]:
    """Return the list of supported artifact modes for a framework."""
    caps = CAPABILITY_MATRIX.get(framework, {})
    return [
        k
        for k, v in caps.items()
        if v and k in ("code_only", "yaml_only", "code_and_yaml")
    ]


def supports_tools(framework: str) -> bool:
    """Return True if the framework supports tool templates."""
    return CAPABILITY_MATRIX.get(framework, {}).get("tool_templates", False)


def supports_mcp(framework: str) -> bool:
    """Return True if the framework supports MCP wrapping."""
    return CAPABILITY_MATRIX.get(framework, {}).get("mcp_wrapper", False)
