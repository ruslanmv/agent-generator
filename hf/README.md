---
title: Agent Generator
emoji: 🤖
colorFrom: blue
colorTo: blue
sdk: docker
app_port: 7860
license: apache-2.0
short_description: Generate multi-agent AI projects from plain English
---

# Agent Generator

Generate complete, production-ready multi-agent AI projects from a simple text description.

## Supported Frameworks

- **CrewAI** — Python + YAML config (agents.yaml, tasks.yaml, crew.py, tools)
- **LangGraph** — StateGraph with typed state and node functions
- **WatsonX Orchestrate** — ADK-compliant YAML for IBM WatsonX
- **CrewAI Flow** — Event-driven pipelines with @start/@listen
- **ReAct** — Reasoning + action loop with tool registry

## Features

- 6 built-in tool templates (web search, PDF reader, SQL, HTTP, file writer, vector search)
- Glassmorphism dark theme UI with file tree and syntax highlighting
- Download generated projects as ZIP
- Iterate with follow-up prompts
- Full validation pipeline (AST, YAML, security scan)

## Local Run

```bash
docker build -t agent-generator .
docker run -p 7860:7860 agent-generator
```

Open http://localhost:7860
