# Bee‑AI Multi‑Agent Backend – Architecture Documentation

**Version:** 1.0 – 2025‑07‑25

---

## 1. Purpose

This backend provides an *AI‑assisted code‑generation service* consumed by the **`agent‑generator`** CLI. It turns a free‑text use‑case into production‑ready artefacts:

- **Plan** – decide which toolkits/gateways to reuse and which to scaffold.  
- **Build** – generate Python tools, MCP gateway stubs and an Agent‑Builder YAML bundle, ready for watsonx Orchestrate.  

The service is exposed over HTTP (`/plan`, `/build`) **and** can run in‑process when `GENERATOR_BACKEND_URL=local`.

---

## 2. High‑Level Component Diagram

```text
┌────────────────────────────┐        HTTP/JSON or in‑proc
│  agent‑generator CLI       │ ─────────────────────────────►  /plan
└────────────────────────────┘                                 │
                                                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│           Bee‑AI Backend (FastAPI)                                   │
│                                                                      │
│  ┌──────────────┐           ┌───────────────────┐                    │
│  │  /plan       │  ───────► │  Planning Agent   │                    │
│  └──────────────┘           └───────────────────┘                    │
│        ▲                                 │ JSON plan                │
│        │                                 ▼                          │
│  ┌──────────────┐           ┌───────────────────┐                    │
│  │  /build      │  ───────► │ Builder Manager   │ ─┬──── async ──────┤
│  └──────────────┘           └───────────────────┘  │                 │
│                                                     │                │
│     ┌───────────────────────┐  ┌─────────────────┐  │                │
│     │ Py‑Tool Builder       │  │ MCP‑Tool Builder│  │  gather()      │
│     └───────────────────────┘  └─────────────────┘  │                │
│                 │                  │               ▼                │
│                 └────────────┬─────┴──────┐  Merger Agent            │
│                              ▼             └─────────┬──────────────┘
│                 build/<framework>/…                  ▼               │
└──────────────────────────────────────────────────────────────────────┘
````

---

## 3. Key Modules

| Path                                           | Responsibility                                                                      |
| ---------------------------------------------- | ----------------------------------------------------------------------------------- |
| `backend/main.py`                              | FastAPI app, routes `/plan` & `/build`; injects settings & logging                  |
| `backend/config.py`                            | **Settings** – reads `.env` (watsonx credentials, ports, dirs). No secrets in code. |
| `backend/logging_conf.py`                      | Central `dictConfig` for consistent logs                                            |
| `backend/utils.py`                             | Filesystem helpers (`ensure_dirs`, `relative_tree`)                                 |
| `backend/agents/planning_agent.py`             | *Architect* LLM agent – chooses framework & build tasks                             |
| `backend/agents/builder_manager.py`            | Orchestrates leaf builders with `asyncio.gather`, then merges                       |
| `backend/agents/builders/py_tool_builder.py`   | Scaffolds Python tool packages                                                      |
| `backend/agents/builders/mcp_tool_builder.py`  | Pulls‑in or links existing MCP gateways                                             |
| `backend/agents/builders/yaml_agent_writer.py` | Generates final Agent‑Builder YAML                                                  |
| `backend/agents/merger_agent.py`               | Collates artefacts, returns final tree preview                                      |

---

## 4. Request‑/Response Contracts

### 4.1 `POST /plan`

**Request Body**

```json
{
  "use_case": "Research assistant …",
  "preferred_framework": "watsonx_orchestrate",
  "mcp_catalog": {"docling_gateway": {…}}
}
```

**Response (200)**

```json
{
  "selected_framework": "watsonx_orchestrate",
  "project_tree": ["build/…", …],
  "build_tasks": [
    {"kind": "python_tool", "name": "pdf_summariser"},
    {"kind": "mcp_tool", "gateway": "docling_gateway"}
  ]
}
```

### 4.2 `POST /build`

**Request Body**
Body is the previous plan object.

**Response (200)**

```json
{
  "status": "ok",
  "summary": {
    "framework": "watsonx_orchestrate",
    "tree": ["agents/research_assistant.yaml", "tool_sources/…", …]
  }
}
```

**Errors**

* `500` – Returns JSON `{ "detail": "…" }` if planning/build fails.

---

## 5. Sequence Diagram (Happy Path)

```text
CLI          Backend           Planner            BuilderMgr    Leaf Builders
 │  /plan     │                  │                  │              │
 │──────────▶ │                  │                  │              │
 │            │── calls LLM ───▶ │                  │              │
 │            │◀── plan JSON ─── │                  │              │
 │◀── plan────│                  │                  │              │
 │  /build    │                  │                  │              │
 │──────────▶ │                  │                  │              │
 │            │                  │── gather ─┬───▶  │              │
 │            │                  │           │      │─── build────▶│  
 │            │                  │           │      │─── build────▶│  
 │            │                  │           └──────┘              │
 │            │◀──────── summary │                  │              │
 │◀── OK──────│                  │                  │              │
```

---

## 6. Environment Variables

| Variable           | Required | Description                              |
| ------------------ | -------- | ---------------------------------------- |
| `WATSONX_API_KEY`  | ✔        | IAM key for watsonx.ai                   |
| `WATSONX_URL`      | ✔        | e.g. `https://us-south.ml.cloud.ibm.com` |
| `PROJECT_ID`       | ✔        | watsonx.ai project GUID                  |
| `OPENAI_API_KEY`   |          | Fallback LLM provider                    |
| `BEE_BACKEND_HOST` |          | Bind address (default `0.0.0.0`)         |
| `BEE_BACKEND_PORT` |          | Port (default `8000`)                    |
| `BUILD_BASE_DIR`   |          | Output directory (default `./build`)     |

---

## 7. Error Handling & Logging

* **Validation** – All request payloads are validated by Pydantic models.
* **Missing secrets** – `config.Settings` raises a clear `RuntimeError` if required env vars are missing.
* **HTTP errors** – Surface as FastAPI `HTTPException(500)` with a backtrace in logs.
* **Logging** – Components log at `INFO` by default; set `LOG_LEVEL=DEBUG` for verbose LLM diagnostics.

---

## 8. Deployment

1. **Install dependencies**

   ```bash
   pip install agent-generator[all]
   ```
2. **Configure environment**

   ```bash
   cp .env.example .env
   # Edit .env with your WatsonX/OpenAI keys and optional overrides
   ```
3. **Run the service**

   ```bash
   python -m backend.main
   # or
   uvicorn backend.main:app --host 0.0.0.0 --port 8000
   ```
4. **Point your CLI** at it

   ```bash
   export GENERATOR_BACKEND_URL=http://localhost:8000
   agent-generator
   ```

---

## 9. Extending the System

* **Add new frameworks**:

  1. Write a new leaf builder under `backend/agents/builders/`.
  2. Update the planning prompt in `planning_agent.py`.
* **Scale build tasks**:
  Replace `asyncio.gather` in `BuilderManager` with a distributed task queue.
* **Persistent catalogue**:
  Swap `mcp_catalog` in-memory JSON with a database-backed service.

