---
title: Agent Generator
emoji: 🤖
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
license: apache-2.0
pinned: false
short_description: Describe an AI team in English. Get runnable code.
tags:
  - agents
  - crewai
  - langgraph
  - watsonx
  - code-generation
---

# Agent Generator — Live Demo

This is the **public demo** of [agent-generator](https://github.com/ruslanmv/agent-generator) running as a [Hugging Face Space](https://huggingface.co/spaces). It serves the **same React SPA** shipped with the web, desktop, and mobile builds — there is no separate demo UI to maintain.

## What you can try

| Feature | Works in demo |
|---|---|
| Describe an agent team in natural language | ✅ |
| Pick a framework (CrewAI, LangGraph, WatsonX, CrewAI Flow, ReAct) | ✅ |
| Inspect the compatibility matrix (8 frameworks × 5 hyperscalers × 2 patterns × 7 models) | ✅ |
| Browse the marketplace fixture | ✅ |
| Generate a project + download as ZIP | ✅ |
| Sign in with GitHub | 🚫 disabled in demo |
| Persistent project history | 🚫 in-memory only |
| Real run executions / Docker builds | 🚫 demo-mode stubs |

## How it works

```
            HuggingFace Space (Docker SDK, port 7860)
            ┌──────────────────────────────────────────────┐
            │  GET /            → frontend/dist (real SPA)  │
            │  POST /api/plan   ┐                            │
            │  POST /api/build  │ ─→ agent_generator         │
            │  POST /api/generate┘   (PyPI / git+ pinned)    │
            │  GET  /api/compatibility/*  (reused verbatim  │
            │  GET  /api/marketplace/*    from backend/app) │
            └──────────────────────────────────────────────┘
```

- The SPA bundle is built from the **same `frontend/` source** as the desktop and mobile shells with `AG_BUILD_CHANNEL=hf`. A single `IS_DEMO` flag gates auth, persistence, and run history.
- The generator pipeline (`planning_service → ProjectSpec → build_service`) is the **published `agent-generator` Python package**, pinned by CI to the deployed commit so the demo never drifts.
- The compatibility matrix and marketplace endpoints are **literally the production modules** at `backend/app/api/{compatibility,marketplace}.py`, copied in at deploy time.

## Local reproduction

```bash
docker build -t agent-generator-hf hf
docker run --rm -p 7860:7860 agent-generator-hf
```

Open <http://localhost:7860>.

You can also use the Makefile targets at the repo root:

```bash
make hf-build      # build the Space image locally
make hf-run        # start it on :7860
```

## Continuous deployment

Every push to `master` triggers `.github/workflows/hf-space.yml`, which:

1. Builds the SPA with `AG_BUILD_CHANNEL=hf`.
2. Stages the deploy tree (vendoring `frontend/dist/` and the two reused backend modules).
3. Pushes to <https://huggingface.co/spaces/ruslanmv/agent-generator>.

A second workflow (`hf-space-pr.yml`) smoke-tests the same tree on pull requests without deploying.

## License

Apache-2.0.
