# Changelog

## 0.1.3 (2026-04-01)

### New Architecture

- **Domain layer**: `ProjectSpec` canonical schema, `RenderPlan`, `CapabilityMatrix`
- **Planners**: `KeywordPlanner` (instant, no LLM), `LLMPlanner` (structured output), `SpecNormalizer`
- **Renderers**: CrewAI (11-file projects), LangGraph (StateGraph), WatsonX (YAML), `Packager` (ZIP)
- **Tool catalog**: 6 approved templates (web_search, pdf_reader, http_client, sql_query, file_writer, vector_search)
- **Validators**: Spec validation, Python AST + security scan, YAML validation, pipeline orchestrator

### Framework Upgrades

- CrewAI generator: real `@CrewBase`/`@agent`/`@task` decorators, agents.yaml + tasks.yaml config
- LangGraph generator: `StateGraph` with `TypedDict` state, `START`/`END` constants
- CrewAI Flow generator: `Flow[FlowState]` with `@start`/`@listen` decorators
- ReAct generator: real reasoning loop with tool registry and `MAX_ITERATIONS` guard
- WatsonX Orchestrate: already production-ready (unchanged)

### Web UI

- Migrated from Flask to FastAPI
- Enterprise 4-step wizard: Describe -> Plan & Edit -> Configure -> Generate & Export
- Glassmorphism dark theme with file tree, syntax highlighting, ZIP download
- OllaBridge inference integration for AI-enhanced planning
- Framework capability matrix with live validation
- Grouped tool selection (Data, Document, Integration)

### HF Spaces Demo

- Self-contained demo at https://huggingface.co/spaces/ruslanmv/agent-generator
- Works without LLM credentials (keyword-based planning)
- All 5 frameworks supported
- OllaBridge-compatible for real inference when connected

### Infrastructure

- Pydantic v1 validators migrated to v2 (`@field_validator`, `@model_validator`)
- Dependencies updated to latest (pydantic 2.12, fastapi 0.135, crewai 1.12, langgraph 1.1)
- 31 tests passing (up from 2)
- Updated README, docs, Dockerfile
- Python 3.10+ required (was 3.9+)

## 0.1.2 (2025-07-22)

- Initial alpha release
- CLI with 5 framework generators
- WatsonX + OpenAI providers
- Flask web UI
- MCP wrapper support
