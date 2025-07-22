
# 🛠️ agent‑generator 

*A one‑line prompt … a fully configured multi‑agent team, served via an MCP Gateway.*


![logo](images/logo.png)


`agent‑generator` converts plain‑English requirements into runnable code or YAML workflows for:

- **CrewAI** & **CrewAI Flow**  
- **LangGraph**  
- **ReAct**  
- **WatsonX Orchestrate** (YAML)

You can choose your LLM provider:

- **IBM WatsonX** (default)  
- **OpenAI** (via `--provider openai` or `AGENTGEN_PROVIDER=openai`)

---

## Why Multi‑Agent + MCP Gateway?

Splitting a complex task into specialized agents lets you:

- **Parallelize** subtasks (e.g. research, summarise, review)  
- **Specialize** prompts per role for cleaner, maintainable code  
- **Visualize** your workflow as Mermaid/DOT diagrams  

The **MCP server wrapper** (FastAPI) and **MCP Gateway** provide:

- **Unified HTTP entrypoint** for all agents  
- **Route isolation** per task or agent  
- **Built‑in monitoring**, health checks, and cost endpoints  

This makes your multi‑agent system production‑ready with minimal boilerplate.

---

## Highlights

| Feature                         | ✓   |
|---------------------------------|-----|
| IBM WatsonX *default*           | ✅  |
| OpenAI support                  | ✅  |
| Plug‑in providers               | ✅  |
| MCP server wrapper & Gateway    | ✅  |
| Rich CLI + Flask UI             | ✅  |
| Mermaid / DOT diagrams          | ✅  |

---

<div class="admonition tip">
<strong>Quick install</strong>

```bash
pip install agent-generator[web,openai]
```

</div>

Jump in: **[Installation ➜](installation.md)** · **[Usage ➜](usage.md)** · **[Frameworks ➜](frameworks.md)**










