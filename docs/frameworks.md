# Supported Frameworks

This page describes each target framework that **agent‑generator** can produce, along with typical use cases and output artifacts.

---

## 1 WatsonX Orchestrate (`watsonx_orchestrate`)

- **Output:** native YAML agent definitions  
- **Use case:** import directly into IBM WatsonX Orchestrate via `orchestrate agents import`  
- **File extension:** `.yaml`  
- **Example command:**
  ```bash
  agent-generator "Email summariser" \
    -f watsonx_orchestrate \
    -o summariser.yaml
````

---

## 2 CrewAI (`crewai`)

* **Output:** Python package using the CrewAI SDK
* **Use case:** define an event‑driven multi‑agent workflow with built‑in retry and monitoring
* **File extension:** `.py`
* **Supports:** optional MCP FastAPI wrapper (`--mcp`)
* **Example command:**

  ```bash
  agent-generator "Analyse tweets" \
    -f crewai \
    --mcp \
    -o tweets_workflow.py
  ```

---

## 3 CrewAI Flow (`crewai_flow`)

* **Output:** Python “flow definition” for CrewAI Flow (a distinct event pipeline)
* **Use case:** orchestrate asynchronous tasks via CrewAI Flow’s managed broker
* **File extension:** `.py`
* **Example command:**

  ```bash
  agent-generator "Process incoming orders" \
    -f crewai_flow \
    -o order_flow.py
  ```

---

## 4 LangGraph (`langraph`)

* **Output:** Python DAG description for LangGraph
* **Use case:** build complex data‑processing pipelines with explicit node dependencies
* **File extension:** `.py`
* **Example command:**

  ```bash
  agent-generator "ETL pipeline for sales data" \
    -f langraph \
    -o etl_pipeline.py
  ```

---

## 5 ReAct (`react`)

* **Output:** Python script implementing the Reason‑Act loop with tool calls
* **Use case:** tasks requiring interleaved planning and execution (e.g. research & code generation)
* **File extension:** `.py`
* **Example command:**

  ```bash
  agent-generator "Generate unit tests" \
    -f react \
    -o test_generator.py
  ```

---

## 6 BeeAI Orchestration (`beeai`)

* **Output:** JSON/HTTP‑based multi‑agent orchestration using the BeeAI framework
* **Use case:** drive the planning & build pipeline itself with BeeAI sub‑agents
* **File extension:** *none* (results are side‑effects under `build/beeai/`)
* **Example command:**

  ```bash
  agent-generator "Research assistant for PDFs" \
    -f beeai \
    --build
  ```

---

### Framework Comparison

| Framework            | Language | Extension | MCP support | Notes                              |
| -------------------- | -------- | --------- | ----------- | ---------------------------------- |
| watsonx\_orchestrate | YAML     | `.yaml`   | –           | Native Orchestrate import          |
| crewai               | Python   | `.py`     | ✓           | CrewAI SDK                         |
| crewai\_flow         | Python   | `.py`     | ✓           | CrewAI Flow pipelines              |
| langraph             | Python   | `.py`     | ✓           | Directed acyclic graph definitions |
| react                | Python   | `.py`     | ✓           | Reason‑Act pattern                 |
| beeai                | Python   | *n/a*     | internal    | Backend orchestration via BeeAI    |

Jump in: **[Installation ➜](installation.md)** · **[Usage ➜](usage.md)** · **[Architecture ➜](architecture.md)**
