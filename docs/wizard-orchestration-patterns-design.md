# Orchestration Patterns — Wizard Design Extension

> Status: **design draft** · Extends
> [`wizard-compatibility-design.md`](./wizard-compatibility-design.md) · Owner:
> frontend · Target: Batch 10+
>
> Design-only proposal. No code lands as part of this change.

## 1 · Why

The compatibility-design adds *vendor* + *hyperscaler* to every
framework. That picks *whose runtime* an agent runs on. But it doesn't
yet pick *how the agents coordinate* — which the comparison brief makes
clear is the single biggest determinant of an agent system's behaviour:

> An orchestration pattern is **how agents coordinate with each other**
> to complete a task. Like a company: you can have a manager assigning
> tasks, or a team of autonomous professionals self-managing.

Two patterns matter today: **Supervisor** (top-down) and
**ReAct** (autonomous loop, optionally multi-agent over shared state).
This extension makes them a first-class wizard concept, so the user
ends up with the triplet that's visible in the reference mockup:

```
Choose Your Framework    Autogen · Strands · LangGraph
Choose Your Model        gpt-4o · gpt-5.1 · claude-opus-4 · …
Choose Your Orchestration Pattern   Supervisor · ReAct
```

## 2 · Orchestration Pattern catalogue

Two entries in a new `src/lib/orchestration.ts` module:

```ts
export type OrchestrationPatternId = 'supervisor' | 'react';

export interface OrchestrationPattern {
  id: OrchestrationPatternId;
  label: string;
  glyph: 'target' | 'cog';     // 🎯 / ⚙️ from the brief
  blurb: string;               // one-liner for the picker tile
  steps: string[];             // ordered behaviour for the Pattern card
  // Trade-off axes (mirrors the comparison table on the second slide)
  axes: {
    flowDecidedBy:   string;
    communication:   string;
    flexibility:     'low' | 'medium' | 'high';
    predictability:  'low' | 'medium' | 'high';
    cost:            'low' | 'medium' | 'high';
  };
}
```

### 2.1 Supervisor (🎯)

> An **orchestrator agent** (the "boss") that:
> - receives the task from the user,
> - decides which specialised agent to call,
> - passes one agent's output as input to the next,
> - manages the overall flow.

Trade-offs (from the brief):

| Axis | Supervisor |
|------|------------|
| Flow decided by | The chief agent |
| Communication | Direct, top-down |
| Flexibility | Low — fixed flow |
| Predictability | High |
| Computational cost | Low |

### 2.2 ReAct (⚙️ — Reason + Act)

> Each agent operates in autonomous cycles:
> 1. **Reason** about the problem
> 2. **Act** (call a tool or another agent)
> 3. **Observe** the result
> 4. **Re-reason** and decide the next step

For **multi-agent** ReAct, agents *don't talk directly*. They share a
**blackboard state**:

> Every agent **reads** what it needs from shared state →
> **reasons** autonomously → **writes** its output back to state.
> The next agent reads that output and continues.

| Axis | Multi-agent ReAct |
|------|------------------|
| Flow decided by | State + each agent autonomously |
| Communication | Via shared state |
| Flexibility | High — the path emerges |
| Predictability | Low |
| Computational cost | High (many LLM cycles) |

## 3 · Framework × Pattern compatibility

Patterns aren't free — not every framework can do both well. Adding a
new field on the `CompatibilityRow`:

```ts
patterns: {
  supervisor: 'native' | 'adapter' | 'unsupported';
  react:      'native' | 'adapter' | 'unsupported';
};
```

| Framework        | Supervisor | ReAct (single) | ReAct (multi) | Native blackboard? |
|------------------|:---------:|:--------------:|:-------------:|:------------------:|
| **LangGraph**    | native    | native         | native        | yes — `GraphState`      |
| **Autogen**      | native    | native         | adapter       | adapter (GroupChat)    |
| **Strands**      | native (linear)¹ | unsupported | unsupported | n/a — linear            |
| **CrewAI**       | native    | adapter        | unsupported   | n/a — role-based        |
| **CrewAI Flow**  | native    | adapter        | adapter       | event log              |
| **ReAct (base)** | unsupported | native       | unsupported   | n/a — single agent      |
| **watsonx Orch.**| native    | unsupported    | unsupported   | n/a — skill router      |
| **LlamaIndex**   | adapter   | native         | adapter       | `QueryPipeline` state  |

¹ Strands is a *linear* supervisor — no loops, no branches. The picker
should mark it as **Supervisor (linear)** so the user isn't surprised.

`unsupported` rows hide the pattern tile entirely; `adapter` rows show
a yellow `⚠ via adapter` ribbon on the tile, matching the existing
hyperscaler convention.

## 4 · Where this sits in the wizard

The reference mockup compresses Framework + Model + Pattern into a
single screen. We adopt the same three-picker shape, but slot it into
the existing flow without breaking the four-step Stepper:

```
Step 2 · Framework  (renamed → "Framework & Model")
   ┌───────────────────────────────────────────┐
   │ Hyperscaler facet rail   (from §3 prev.) │
   │ ─────────────────────────                │
   │ Framework cards            ← pick 1      │
   │   AutoGen · Strands · LangGraph · …      │
   │                                          │
   │ Model row                  ← pick 1      │
   │   gpt-5.1 · claude-opus-4 · llama-3.1-70b│
   │                                          │
   │ Orchestration Pattern row  ← pick 1      │
   │   🎯 Supervisor · ⚙️ ReAct               │
   │                                          │
   │ Pattern card               ← live preview│
   │   "An orchestrator that …"  + trade-offs │
   │                                          │
   │ Why we picked this (from selection)      │
   │   Generated rationale                    │
   └───────────────────────────────────────────┘
```

Compressing into one step keeps the Stepper at 4 (Describe → Framework
& Model → Tools → Review) which is what the existing copy and analytics
already assume.

### 4.1 Model picker

Reads from a new `src/lib/models.ts`:

```ts
interface Model {
  id: string;                       // 'gpt-5.1' | 'gpt-4o' | 'claude-opus-4' | 'llama-3.1-70b' | …
  label: string;
  provider: ProviderId;             // links into the existing provider catalogue
  contextK: number;
  cost1k: { in: number; out: number };
  hyperscalers: HyperscalerId[];    // re-uses §3-prev. matrix
}
```

Default selection is derived from `framework.vendor + state.hyperscaler`:

| Vendor / Hyperscaler | Default model |
|----------------------|---------------|
| microsoft / azure    | `gpt-5.1` (Azure OpenAI) |
| aws                  | `claude-opus-4` on Bedrock |
| langchain / any      | `claude-opus-4` (Anthropic native) |
| ibm                  | `granite-3.1-70b` (watsonx) |
| ollabridge / local   | `qwen2.5:1.5b` |

The model row dims any model whose provider isn't in the selected
framework's allow-list — same dim-with-note treatment used for tools.

### 4.2 Pattern picker

Two tiles, exactly the shape of the mockup. Selecting one updates the
**Pattern card** beneath, which renders the verbatim brief content:

```
🎯  Supervisor                              ⚙️  ReAct
─────────────────────────                  ──────────────────────────
An orchestrator agent (the                Each agent operates in
"boss") that:                              autonomous cycles:
• Receives the task                        1. Reason
• Picks the specialised agent              2. Act (tool or agent call)
• Wires one's output to the next           3. Observe
• Owns the overall flow                    4. Re-reason → next step

Trade-offs:                                Trade-offs:
  Flow              Chief agent              Flow              State + agent
  Communication     Direct, top-down         Communication     Shared state
  Flexibility       Low                      Flexibility       High
  Predictability    High                     Predictability    Low
  Cost              Low                      Cost              High (many cycles)
```

## 5 · Communication topology · ReAct shared state

When the user picks **ReAct** *and* the framework's `react = native`
*and* the agent count > 1, the wizard reveals an inline preview of the
shared-state topology in the Pattern card:

```
        ┌────────────┐
        │ shared     │◀─────── agent_writer
        │ state      │◀─────── agent_reviewer
        │ "scratchpad"│◀─────── agent_planner
        └─────┬──────┘
              │ each agent reads / writes
              ▼
       Iteration loop until terminal goal
```

The wizard never asks the user to spec the state shape — it's derived
from the agent table on Review (each agent's `goal` + `tools` becomes a
key in the scratchpad). A `Show schema` link expands a JSON-Schema-ish
preview for the technically curious.

## 6 · Sample prompts (mirror the mockup)

Drop these into `STARTERS` in `src/lib/wizard-data.ts` so the Describe
step suggests them when the user pauses:

- `"Create a multi-agent system with 3 agents"`
- `"Create a multi-agent system configuration in YAML for a Honda
  Marketing Supervisor agent that manages one subagent — a Content
  Curator. Add a wikipedia search tool to content curator."`
- `"Create an orchestration for invoice processing"`
- `"Create a research assistant with Wikipedia search"`
- `"Create a search agent with Google"`

These prompts also seed the heuristic from §3 of the previous design:
mention of "supervisor", "orchestrator", "manage" hints at
**Supervisor**; "react", "agent loop", "observe and decide" hints at
**ReAct**.

## 7 · Compatibility card additions

The Review-step Compatibility card from the previous design gains two
rows:

    Orchestration   Supervisor      native
    Model           gpt-5.1         Azure OpenAI · ok

If either row goes red (e.g. user picked ReAct but the chosen framework
only `unsupported`s it after they later switched hyperscalers), the
existing **Resolve** button now also navigates to the relevant
pattern/model tile, not just the framework grid.

## 8 · Data shape additions

```ts
// src/lib/orchestration.ts  (new)
export const ORCHESTRATION_PATTERNS: OrchestrationPattern[] = [
  {
    id: 'supervisor',
    label: 'Supervisor',
    glyph: 'target',
    blurb: 'One supervisor coordinates multiple workers.',
    steps: [
      'Receive the task from the user.',
      'Pick which specialised agent to call.',
      "Pass one agent's output as input to the next.",
      'Own the overall flow.',
    ],
    axes: {
      flowDecidedBy:  'The chief agent',
      communication:  'Direct, top-down',
      flexibility:    'low',
      predictability: 'high',
      cost:           'low',
    },
  },
  {
    id: 'react',
    label: 'ReAct',
    glyph: 'cog',
    blurb: 'Reason → Act → Observe → Re-reason. Optionally over a shared state.',
    steps: [
      'Reason about the problem.',
      'Act (call a tool or another agent).',
      'Observe the result.',
      'Re-reason and decide the next step.',
    ],
    axes: {
      flowDecidedBy:  'State + each agent autonomously',
      communication:  'Via shared state (multi-agent)',
      flexibility:    'high',
      predictability: 'low',
      cost:           'high',
    },
  },
];
```

`WizardState` gains:

```ts
interface WizardState {
  // …existing
  model:   string;                       // already exists; now driven by Model picker
  pattern: OrchestrationPatternId;       // NEW
}
```

## 9 · Implementation plan (extends the prior 9a–9f)

| Batch | Scope | Notes |
|-------|-------|-------|
| **9a** *(unchanged)* | `compatibility.ts` + `hyperscalers.ts` + framework data extension | Carries over from the prior design |
| **9b'** | Framework & Model step layout: facet rail + framework cards + model row + **pattern row** + Pattern card | Folds the pattern picker into Step 2; Stepper stays at 4 |
| **9c'** | Pattern preview block — the topology diagram for multi-agent ReAct | Visual; renders only when `pattern = react && agents > 1` |
| **9d'** | Compatibility card adds `Orchestration` and `Model` rows; Resolve walks to the offending tile | Reuses the Diagnostic API |
| **9e'** | Models module: `src/lib/models.ts`, per-hyperscaler defaults, dim-with-note for incompatible models | Mirrors the tool-compat treatment |
| **9f'** | Starter prompts + heuristic hint ("on AWS" → Strands · Supervisor) | Lives in `src/lib/wizard-data.ts` |
| **9g'** | Marketplace facet adds a *Pattern* group so a researcher can filter agent templates by orchestration | One more matrix consumer |

Each batch ships independently. None changes the existing routes or
breaks the v1 wizard.

## 10 · Risks & open questions

- **Cost expectations.** ReAct multi-agent can fan out LLM calls by
  10–50×. We should surface a small `est. tokens` chip on the Pattern
  card driven by `agents × avg_cycles × tokens_per_cycle`. Out of scope
  for this design; tracked under "pricing_hint" from the previous doc.
- **Hybrid patterns.** Some frameworks (LangGraph, CrewAI Flow) can
  nest a ReAct loop inside a supervisor branch. We propose
  `pattern: 'supervisor'` with an opt-in `react_subloops: true` flag
  exposed as an advanced toggle in Review · Configure, not on the
  picker — too many primary options dilute the decision.
- **Default-model drift.** When the user changes hyperscaler *after*
  picking a framework, the default model may flip (e.g. Anthropic
  native → Anthropic via Bedrock). The Model row should preserve the
  *intent* (Anthropic Opus) and only swap the provider hop, with a
  one-line toast: *"Switched to Bedrock to match AWS."*
- **Strands' linear supervisor.** Marking it as Supervisor without
  qualification will mislead — the picker should show
  *"Supervisor · linear"* so the user knows there's no branching.
- **Translation.** The brief is Italian (`Cos'è un Orchestration
  Pattern?`). Product UI stays English; the brief is the canonical
  spec for intent only.

## 11 · Done when

- [ ] On Step 2 the user picks Framework → Model → Pattern in one
      glance, exactly matching the reference mockup.
- [ ] Picking ReAct on a framework that only supports Supervisor
      auto-greys the ReAct tile with `⚠ via adapter` (or `unsupported`,
      hidden) — never a misleading green.
- [ ] The Pattern card always shows the verbatim trade-off table from
      the brief for the active pattern.
- [ ] Choosing Multi-agent ReAct reveals the shared-state topology
      preview without any extra clicks; toggling back to Supervisor
      hides it.
- [ ] The Review · Compatibility card surfaces Orchestration + Model
      alongside Framework + Hyperscaler + Provider + Tools + Exports.
- [ ] Adding a third orchestration pattern (e.g. "Plan-and-execute") is
      a one-file change in `src/lib/orchestration.ts`.
