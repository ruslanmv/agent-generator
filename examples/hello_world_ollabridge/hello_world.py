"""Hello-world CrewAI agent that runs through OllaBridge Cloud.

Generated with:
    agent-generator \\
      "A friendly hello-world agent that greets the user by name, then asks \\
       a question and prints the answer." \\
      --framework crewai --provider watsonx --dry-run --output hello_world.py

Then re-pointed at OllaBridge (an OpenAI-compatible /v1 endpoint) so the
agent's LLM calls go to https://ruslanmv-ollabridge.hf.space.

Required env (loaded automatically from a .env file next to this script):
    OLLABRIDGE_BASE_URL   default: https://ruslanmv-ollabridge.hf.space
    OLLABRIDGE_TOKEN      device pair token returned by pair_ollabridge.py
    OLLABRIDGE_MODEL      default: qwen2.5:1.5b

Run:
    python pair_ollabridge.py GKEV-8985   # ← exchange your pairing code first
    python hello_world.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from crewai import Agent as CrewAgent
from crewai import Crew, Process
from crewai import Task as CrewTask
from crewai import LLM


# ────────────────────────────────────────────────────────────
# Load .env if present (no python-dotenv dependency required)
# ────────────────────────────────────────────────────────────
def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv(Path(__file__).with_name(".env"))


# ────────────────────────────────────────────────────────────
# Wire CrewAI's LLM to OllaBridge's OpenAI-compatible /v1 API
# ────────────────────────────────────────────────────────────
BASE_URL = os.environ.get("OLLABRIDGE_BASE_URL", "https://ruslanmv-ollabridge.hf.space").rstrip("/")
TOKEN = os.environ.get("OLLABRIDGE_TOKEN", "")
MODEL = os.environ.get("OLLABRIDGE_MODEL", "qwen2.5:1.5b")

if not TOKEN:
    sys.stderr.write(
        "OLLABRIDGE_TOKEN is not set. Pair this device first:\n"
        "    python pair_ollabridge.py YOUR-CODE\n"
    )
    sys.exit(1)

# CrewAI delegates to LiteLLM, which routes the `openai/...` model prefix
# through the OpenAI-compatible client. OllaBridge speaks that protocol.
ollabridge_llm = LLM(
    model=f"openai/{MODEL}",
    base_url=f"{BASE_URL}/v1",
    api_key=TOKEN,
    temperature=0.7,
    max_tokens=512,
)


# ────────────────────────────────────────────────────────────
# Agents
# ────────────────────────────────────────────────────────────
assistant = CrewAgent(
    role="Friendly Assistant",
    goal="Greet the user, ask one question, and print the answer.",
    backstory="A warm, concise assistant that values short, clear replies.",
    verbose=True,
    allow_delegation=False,
    llm=ollabridge_llm,
)


# ────────────────────────────────────────────────────────────
# Tasks
# ────────────────────────────────────────────────────────────
hello_task = CrewTask(
    description=(
        "Greet the user by their name (use {name}), then ask them: "
        "'What is one thing you'd like to learn today?' Wait for an "
        "imagined answer and respond enthusiastically with one sentence."
    ),
    expected_output=(
        "A two-line message: line 1 is the greeting + question, line 2 is the "
        "enthusiastic response to a sample answer."
    ),
    agent=assistant,
)


# ────────────────────────────────────────────────────────────
# Crew
# ────────────────────────────────────────────────────────────
crew = Crew(
    agents=[assistant],
    tasks=[hello_task],
    process=Process.sequential,
    verbose=True,
)


def main() -> Any:
    return crew.kickoff(inputs={"name": os.environ.get("USER_NAME", "Ruslan")})


if __name__ == "__main__":
    print(main())
