"""LLM-powered spec generator.

Takes a BaseProvider instance and keyword hints from the KeywordPlanner.
Uses a carefully crafted few-shot prompt to produce a ProjectSpec JSON.
Includes a JSON repair loop (max 2 attempts) for robustness.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Optional

from jinja2 import Template

from agent_generator.domain.project_spec import ProjectSpec
from agent_generator.providers.base import BaseProvider

log = logging.getLogger(__name__)

_SPEC_PROMPT = Template(
    """\
You are an expert AI systems architect specializing in multi-agent workflows.

Given the user's request below, produce a ProjectSpec JSON object that defines
the complete agent project.

## User Request
{{ prompt }}

## Pre-Analysis Hints
- Suggested framework: {{ hints.suggested_framework }}
- Suggested tools: {{ hints.suggested_tools | join(', ') or 'none detected' }}
- Suggested agent roles: {{ hints.suggested_roles | join(', ') or 'none detected' }}
- Suggested artifact mode: {{ hints.suggested_artifact_mode }}

## Available Tool Templates
web_search, pdf_reader, http_client, sql_query, vector_search, file_writer

## Rules
1. Create distinct agents with clear, non-overlapping roles.
2. Each task must reference exactly one agent_id and have a clear expected_output.
3. Use depends_on to express task ordering (empty list for first tasks).
4. Only reference tool templates from the available list above.
5. Use snake_case for all IDs.
6. The project name should be a short kebab-case slug.

## Example Output
```json
{
  "name": "research-report",
  "description": "Research a topic and write a comprehensive report",
  "framework": "crewai",
  "artifact_mode": "code_only",
  "agents": [
    {
      "id": "researcher",
      "role": "Senior Researcher",
      "goal": "Find comprehensive information on the given topic",
      "backstory": "An experienced researcher with deep expertise in information gathering",
      "tools": ["search_tool"]
    },
    {
      "id": "writer",
      "role": "Technical Writer",
      "goal": "Produce a well-structured report from research findings",
      "backstory": "A skilled writer who excels at synthesizing complex information",
      "tools": ["file_tool"]
    }
  ],
  "tasks": [
    {
      "id": "research_task",
      "description": "Research the topic thoroughly using available tools",
      "agent_id": "researcher",
      "expected_output": "Detailed research notes with sources",
      "depends_on": []
    },
    {
      "id": "write_task",
      "description": "Write a comprehensive report based on research findings",
      "agent_id": "writer",
      "expected_output": "A polished report in markdown format",
      "depends_on": ["research_task"]
    }
  ],
  "tools": [
    {"id": "search_tool", "template": "web_search", "inputs": {}},
    {"id": "file_tool", "template": "file_writer", "inputs": {}}
  ]
}
```

## Output
Respond with ONLY valid JSON matching the structure above. No markdown fences,
no explanation, just the JSON object."""
)

_REPAIR_PROMPT = Template(
    """\
The following JSON is invalid. Please fix it so it is valid JSON and return
ONLY the corrected JSON object. No explanation, no markdown fences.

## Broken JSON
{{ broken_json }}

## Error
{{ error }}"""
)


def extract_json_block(text: str) -> str:
    """Extract a JSON object from an LLM response.

    Handles several common response formats:
    - JSON wrapped in ```json ... ``` fences
    - JSON wrapped in ``` ... ``` fences (no language tag)
    - Raw JSON object starting with {
    - JSON embedded in surrounding prose

    Args:
        text: Raw LLM response text.

    Returns:
        Cleaned JSON string ready for parsing.

    Raises:
        ValueError: If no JSON object can be found in the text.
    """
    if not text or not text.strip():
        raise ValueError("Empty response from LLM")

    stripped = text.strip()

    # Try fenced code blocks first (```json ... ``` or ``` ... ```)
    fence_match = re.search(r"```(?:json)?\s*\n?(.*?)```", stripped, re.DOTALL)
    if fence_match:
        candidate = fence_match.group(1).strip()
        if candidate.startswith("{"):
            return candidate

    # Try to find a raw JSON object by matching balanced braces
    brace_start = stripped.find("{")
    if brace_start != -1:
        depth = 0
        for i in range(brace_start, len(stripped)):
            if stripped[i] == "{":
                depth += 1
            elif stripped[i] == "}":
                depth -= 1
                if depth == 0:
                    return stripped[brace_start : i + 1]

    raise ValueError("No JSON object found in LLM response")


class LLMPlanner:
    """Produces a ProjectSpec from a user prompt via a single LLM call.

    Uses keyword hints from the KeywordPlanner to guide the LLM toward
    producing a well-structured specification.  Includes a JSON repair
    loop: if the first response contains invalid JSON, the LLM is asked
    to fix it (max 2 total attempts).
    """

    MAX_ATTEMPTS: int = 2

    def __init__(self, provider: BaseProvider) -> None:
        self.provider = provider

    def plan(self, prompt: str, hints: dict) -> Optional[ProjectSpec]:
        """Generate a ProjectSpec from a user prompt.

        Args:
            prompt: The user's natural-language description of the project.
            hints: Pre-classification hints from KeywordPlanner.classify().

        Returns:
            A validated ProjectSpec instance, or *None* if the LLM could
            not produce valid output after ``MAX_ATTEMPTS`` tries.
        """
        rendered = _SPEC_PROMPT.render(prompt=prompt, hints=hints)
        raw_response = self.provider.generate(rendered)

        last_error: str = ""
        json_str: str = ""

        for attempt in range(self.MAX_ATTEMPTS):
            try:
                if attempt == 0:
                    json_str = extract_json_block(raw_response)
                else:
                    # Repair attempt: ask the LLM to fix the broken JSON
                    repair_prompt = _REPAIR_PROMPT.render(
                        broken_json=json_str, error=last_error
                    )
                    raw_response = self.provider.generate(repair_prompt)
                    json_str = extract_json_block(raw_response)

                spec_dict = json.loads(json_str)
                return ProjectSpec(**spec_dict)

            except (json.JSONDecodeError, ValueError) as exc:
                last_error = str(exc)
                log.warning(
                    "LLMPlanner attempt %d/%d failed (JSON): %s",
                    attempt + 1,
                    self.MAX_ATTEMPTS,
                    last_error,
                )
            except Exception as exc:
                last_error = str(exc)
                log.warning(
                    "LLMPlanner attempt %d/%d failed (validation): %s",
                    attempt + 1,
                    self.MAX_ATTEMPTS,
                    last_error,
                )

        log.error("LLMPlanner exhausted %d attempts", self.MAX_ATTEMPTS)
        return None
