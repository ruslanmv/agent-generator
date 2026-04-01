"""Fast keyword-based pre-classifier -- no LLM call needed."""
from __future__ import annotations


FRAMEWORK_KEYWORDS: dict[str, list[str]] = {
    "crewai": [
        "crew",
        "crewai",
        "agent team",
        "collaborative",
        "delegation",
        "multi-agent team",
    ],
    "langgraph": [
        "langgraph",
        "state graph",
        "state machine",
        "conditional",
        "branching",
        "graph workflow",
    ],
    "watsonx_orchestrate": [
        "watsonx",
        "orchestrate",
        "ibm",
        "adk",
        "watson",
    ],
    "crewai_flow": [
        "flow",
        "crewai flow",
        "sequential flow",
        "pipeline flow",
    ],
    "react": [
        "react agent",
        "reasoning",
        "think and act",
        "tool loop",
        "react pattern",
    ],
}

TOOL_KEYWORDS: dict[str, list[str]] = {
    "web_search": ["search", "google", "browse", "web search", "internet", "look up"],
    "pdf_reader": ["pdf", "document", "read file", "extract text", "parse document"],
    "http_client": ["api", "rest", "http", "fetch", "request", "endpoint", "call api"],
    "sql_query": ["sql", "database", "query", "db", "postgres", "mysql", "sqlite"],
    "vector_search": [
        "vector",
        "embedding",
        "semantic search",
        "similarity",
        "rag",
        "retrieval",
    ],
    "file_writer": [
        "write file",
        "save file",
        "export",
        "output file",
        "create file",
    ],
}

ROLE_KEYWORDS: dict[str, list[str]] = {
    "researcher": [
        "research",
        "find",
        "search",
        "discover",
        "investigate",
        "gather information",
    ],
    "writer": [
        "write",
        "draft",
        "compose",
        "author",
        "create content",
        "blog",
        "article",
    ],
    "analyst": [
        "analyze",
        "evaluate",
        "assess",
        "review",
        "examine",
        "data analysis",
    ],
    "coder": [
        "code",
        "program",
        "develop",
        "implement",
        "build software",
        "debug",
    ],
    "planner": [
        "plan",
        "strategy",
        "organize",
        "coordinate",
        "manage",
        "project manage",
    ],
    "reviewer": [
        "review",
        "quality",
        "check",
        "audit",
        "verify",
        "proofread",
    ],
}


def _score(
    prompt_lower: str, keyword_map: dict[str, list[str]], top_n: int = 3
) -> list[str]:
    """Score each key by counting how many of its keywords appear in the prompt."""
    scores: dict[str, int] = {}
    for key, keywords in keyword_map.items():
        score = sum(1 for kw in keywords if kw in prompt_lower)
        if score > 0:
            scores[key] = score
    return sorted(scores, key=lambda k: scores[k], reverse=True)[:top_n]


class KeywordPlanner:
    """Fast pre-classification using keyword scoring.

    Analyzes a user prompt to suggest framework, tools, roles, artifact mode,
    and complexity without making any LLM calls.
    """

    def classify(
        self,
        prompt: str,
        user_framework: str | None = None,
        user_artifact_mode: str | None = None,
    ) -> dict:
        """Classify a user prompt and return structured suggestions.

        Args:
            prompt: The raw user prompt describing the desired agent project.
            user_framework: Optional explicit framework override from the user.
            user_artifact_mode: Optional explicit artifact mode override.

        Returns:
            Dictionary with keys: suggested_framework, suggested_tools,
            suggested_roles, suggested_artifact_mode, complexity.
        """
        prompt_lower = prompt.lower().strip()
        frameworks = _score(prompt_lower, FRAMEWORK_KEYWORDS, top_n=1)
        tools = _score(prompt_lower, TOOL_KEYWORDS, top_n=5)
        roles = _score(prompt_lower, ROLE_KEYWORDS, top_n=5)

        word_count = len(prompt_lower.split())
        if word_count < 30:
            complexity = "low"
        elif word_count < 80:
            complexity = "medium"
        else:
            complexity = "high"

        return {
            "suggested_framework": user_framework
            or (frameworks[0] if frameworks else "crewai"),
            "suggested_tools": tools,
            "suggested_roles": roles,
            "suggested_artifact_mode": user_artifact_mode
            or self._infer_mode(prompt_lower, frameworks),
            "complexity": complexity,
        }

    def _infer_mode(self, prompt_lower: str, frameworks: list[str]) -> str:
        """Infer the best artifact mode from prompt content and framework."""
        if frameworks and frameworks[0] == "watsonx_orchestrate":
            return "yaml_only"
        if any(kw in prompt_lower for kw in ["yaml", "config", "configuration"]):
            return "code_and_yaml"
        return "code_only"
