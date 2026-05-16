# Hyperscaler-aware Generation — End-to-End Design

> Status: **design draft** · Owner: frontend · Target: Batch 9+ of the
> Agent Generator frontend
>
> This document is a design proposal only. No code lands as part of this
> change; the implementation plan at the bottom carves the work into
> follow-up batches.

## 1 · Why

Agents differ not only by *what* they do but by *how their agents
coordinate*. The three reference frameworks (cf. the comparison slide
attached to the brief) embody three distinct coordination philosophies:

| Framework | Vendor | Pattern | Strength | Risk |
|-----------|--------|---------|----------|------|
| **AutoGen**  | Microsoft / Azure | "Brainstorming" — free back-and-forth between agents | Iterative quality, self-critique | Loop forever or drift off-topic if not throttled |
| **Strands**  | Amazon AWS        | "Assembly line" — sequential hand-off, no looping  | Fast, deterministic, cheap | A bad step taints every downstream agent |
| **LangGraph**| LangChain         | "Industrial process" — explicit state machine, branches gated by validators | Predictable, auditable, retry-friendly | Higher design cost; every transition must be modeled |

The wizard already supports CrewAI, LangGraph, ReAct, watsonx
Orchestrate, CrewAI Flow, plus AutoGen and LlamaIndex as plug-ins. This
design *upgrades* those entries from "names in a list" to
**first-class, hyperscaler-aware** options so the user can pick the
right philosophy *and* know up front which Marketplace tools, providers,
and export targets will actually work.

## 2 · Three new dimensions on every framework entry

Every record in `src/lib/wizard-data.ts → FRAMEWORKS` grows three
fields:

```ts
interface Framework {
  // …existing fields (id, name, tag, stage, rationale, structure)
  vendor:        'microsoft' | 'aws' | 'langchain' | 'ibm' | 'crewai' | 'community';
  philosophy:    'brainstorm' | 'pipeline' | 'graph' | 'react' | 'custom';
  hyperscalers:  ('azure' | 'aws' | 'gcp' | 'ibm' | 'on_prem')[];
  pattern: {
    summary:  string;   // "Free back-and-forth" / "Linear hand-off" / "Validated state machine"
    risk:     string;   // The red line from the slide
    icon:     'brainstorm' | 'pipeline' | 'graph' | 'react' | 'custom';
  };
}
```

The vendor + hyperscaler tag drives every downstream filter. The
philosophy + pattern drive the rationale card the user sees on the
Framework step.

### 2.1 Compatibility matrix (initial baseline)

| Framework        | Vendor      | Azure | AWS | GCP | IBM | On-prem | Providers (LLM)                          | Notable tools | Export targets |
|------------------|-------------|:---:|:---:|:---:|:---:|:------:|------------------------------------------|---------------|----------------|
| **AutoGen**      | Microsoft   | ●   | ◐   | ◐   | ◐   | ●      | Azure OpenAI · OpenAI · Anthropic        | Most generic tools; Azure AI Search | Azure AI Foundry · Docker · HF · ZIP |
| **Strands**      | AWS         | ◐   | ●   | ◐   | ◐   | ●      | Bedrock · Anthropic · Cohere             | Bedrock-Agents tools, AWS Lambda    | AWS Bedrock Agents · Docker · ZIP   |
| **LangGraph**    | LangChain   | ●   | ●   | ●   | ●   | ●      | Anthropic · OpenAI · watsonx · Ollama · OllaBridge | Tool-agnostic | All targets |
| **CrewAI**       | CrewAI      | ●   | ●   | ●   | ●   | ●      | Anthropic · OpenAI · watsonx · OllaBridge | Tool-agnostic | All targets |
| **watsonx Orch.**| IBM         | ◐   | ◐   | ◐   | ●   | ◐      | watsonx                                   | watsonx Skills | watsonx Orchestrate · Docker |
| **ReAct**        | community   | ●   | ●   | ●   | ●   | ●      | any                                       | any           | Docker · ZIP |
| **LlamaIndex**   | community   | ●   | ●   | ●   | ●   | ●      | any                                       | data tools    | Docker · HF · ZIP |

`●` = native · `◐` = works via a generic adapter · *blank* = not
supported in this batch.

The matrix lives in a new module `src/lib/compatibility.ts` and is the
**single source of truth** that every wizard step, the Marketplace
filter rail, and the Export grid consult.

## 3 · How the wizard changes, step by step

### Step 1 — Describe

No UI change today. Optionally, when the prompt clearly names a cloud
(`"on AWS"`, `"in Azure"`, `"watsonx"`), surface a one-line hint above
the Stepper: *"We'll preselect Strands since you mentioned AWS — you can
override on the next step."* (Heuristic; no LLM call.)

### Step 2 — Framework  *(biggest change)*

The 4-column card grid grows three new affordances:

1. **Hyperscaler facet rail** (left, 200 px) — chips for *Any · Azure ·
   AWS · GCP · IBM · On-prem*; selecting one filters the grid.
2. **Philosophy filter** — three pill toggles above the grid:
   *Brainstorm · Assembly line · Industrial process* (plus "Any"). The
   illustrations from the comparison slide become small monochrome
   glyphs next to the framework name in each card.
3. **Pattern card** under the grid — when a framework is selected,
   surface the **slide's content verbatim**:

       Pattern: Brainstorming
       The writer drafts, the reviewer critiques, the writer fixes.
       It's free back-and-forth.
       ⚠ Risk: They could argue forever or drift off-topic
                if not monitored.

   ↳ Colour-coded by status: pattern in `tokens.ink2`, risk in
   `tokens.err`. Same shape for all three philosophies so the user can
   compare like-for-like.

A small `<HyperscalerBadge>` (Azure / AWS / LangChain / IBM logos, mono
+ cobalt) sits in the top-right of every card.

### Step 3 — Tools

Tools cards inherit a derived flag `compatibleWithSelection: boolean`
from the chosen framework + hyperscaler. Incompatible tools are not
hidden but rendered dim with an inline note (`requires Strands · AWS`),
so the user can see what they'd unlock by switching frameworks.

### Step 4 — Review

The existing right column adds a new **Compatibility** card *between*
Reasoning and Output:

    ┌──────── Compatibility ────────────────┐
    │ Framework      AutoGen      microsoft   │
    │ Hyperscaler    Azure        native      │
    │ LLM provider   Azure OpenAI ok          │
    │ Tools          web_search   ok          │
    │                az_ai_search ok          │
    │                bedrock_kb   ⚠ Strands   │
    │ Export targets Azure AI Foundry ok      │
    │                AWS Bedrock      not sup │
    └────────────────────────────────────┘

Hovering a row shows the exact rule (`framework.hyperscalers includes
'aws' = false`). A red **Resolve** button appears if any row is
incompatible: it walks the user to the offending step pre-filtered.

### Step 5 (mobile) / footer (desktop) — Export

The Export grid greys out targets that aren't in the framework's
`export_targets` whitelist and replaces the chevron with a small lock
glyph plus tooltip *"Available with LangGraph or CrewAI"*. The HomePilot
runtime adapter modal pulls its dependency list from the *intersection*
of the framework + hyperscaler matrices, so the ✓/⚠/✕ glyphs reflect
reality.

### Marketplace

The Browse facet rail gains a *Hyperscaler* group (Azure / AWS / GCP /
IBM / On-prem), and every result card displays its `hyperscalers`
badges so a researcher can pick a tool that fits their cloud at a
glance.

### Settings → Providers

Providers reorder into three groups:

- **Cloud LLM** — Anthropic (Azure-hosted + native), OpenAI, Azure
  OpenAI, AWS Bedrock, Google Vertex
- **Enterprise** — IBM watsonx, OllaBridge
- **Local** — Ollama

Each row gains a small chip showing the hyperscalers it can serve.

## 4 · New components & files

| Path                                              | What it does |
|---------------------------------------------------|--------------|
| `src/lib/compatibility.ts`                        | The matrix + helpers `isCompatible(framework, dim, value)` and `compatibilityFor(state)` returning a `Diagnostic[]` |
| `src/lib/hyperscalers.ts`                         | Hyperscaler catalogue (Azure / AWS / GCP / IBM / On-prem) with brand colours, mono glyphs, default LLM provider |
| `src/components/icons/HyperscalerBadge.tsx`       | 28×16 mono badge — same shape as `<TypeBadge>` |
| `src/components/icons/PatternGlyph.tsx`           | The three SVGs from the comparison slide (megaphone / arrow chain / circle process) |
| `src/pages/wizard/StepFramework.tsx`              | Add hyperscaler facets, philosophy filter, Pattern card |
| `src/pages/wizard/components/CompatibilityCard.tsx` | New right-column card on the Review step |
| `src/pages/marketplace/Browse.tsx`                | Add the Hyperscaler facet group |
| `src/lib/export-data.ts → ExportAdapter`          | Add `supports: HyperscalerId[]` and `frameworks: FrameworkId[]` so the grid can grey-out the incompatible ones |

No new dependencies. The matrix is plain TS so it tree-shakes; the
diagnostics utility is < 80 lines.

## 5 · End-to-end flow

```
┌─────────────┐   prompt   ┌─────────────┐
│  Describe   │──────────▶│ heuristic   │
└─────────────┘            │ hint cloud  │
                           └──────┬──────┘
                                  │ vendor / hyperscaler hint
                                  ▼
┌───────────────────────────────────────────────────────┐
│  Step 2 · Framework                              │
│   ▸ Hyperscaler facet rail                       │
│   ▸ Philosophy filter (brainstorm/pipeline/graph)│
│   ▸ Pattern card (slide content + risk)          │
│   ▸ HyperscalerBadge on every framework card     │
└────────┬───────────────────────────────────────────┘
         │ chosen framework + hyperscaler
         ▼
┌───────────────────────────────────────────────────────┐
│  Step 3 · Tools                                  │
│   ▸ Tools dimmed when not in matrix              │
│   ▸ Inline "requires Strands · AWS" note         │
└────────┬───────────────────────────────────────────┘
         │ chosen tool set
         ▼
┌───────────────────────────────────────────────────────┐
│  Step 4 · Review                                 │
│   ▸ Configure (LLM provider segmented filtered   │
│     by framework + hyperscaler)                  │
│   ▸ Compatibility card                           │
│       fram/hyp/prov/tools/exports rows           │
│       Resolve button on warn/err                 │
└────────┬───────────────────────────────────────────┘
         │
         ▼
┌───────────────────────────────────────────────────────┐
│  /export                                         │
│   ▸ Export grid greys non-matching targets       │
│   ▸ Runtime-adapter modal uses matrix ✓/⚠/✕      │
└────────────────────────────────────────────────────────┘
```

`useCompatibility()` reads the wizard state and returns a memoised
`Diagnostic[]` that the Review card and the Resolve button both
consume — single source of truth, no duplicated logic.

## 6 · Data shape (proposed)

```ts
// src/lib/compatibility.ts
export type HyperscalerId = 'azure' | 'aws' | 'gcp' | 'ibm' | 'on_prem';
export type FrameworkId   = 'autogen' | 'strands' | 'langgraph' | 'crewai'
                          | 'crewflow' | 'react' | 'wxo' | 'llamaidx' | 'custom';

export interface CompatibilityRow {
  framework:    FrameworkId;
  vendor:       Vendor;
  hyperscalers: HyperscalerId[];           // native = listed; via adapter = `${id}:adapter`
  providers:    ProviderId[];
  tools:        ToolId[];                  // empty = "tool-agnostic"
  exports:      ExportTargetId[];          // empty = "all"
}

export const COMPATIBILITY: CompatibilityRow[] = [/* matrix from §2.1 */];

export type Diagnostic =
  | { ok: true;  message: string }
  | { ok: false; severity: 'warn' | 'err'; message: string; resolveStep: 1 | 2 | 3 };

export function compatibilityFor(state: WizardState): Diagnostic[];
```

## 7 · Implementation plan (follow-up batches)

| Batch | Scope | Why this slice |
|-------|-------|----------------|
| **9a** | `compatibility.ts` + `hyperscalers.ts` + Framework data extension (vendor / philosophy / hyperscalers) | Data first, no UI changes — keeps the diff reviewable |
| **9b** | `StepFramework` upgrades: hyperscaler facet rail, philosophy filter, Pattern card, HyperscalerBadge | Visible change with the highest direct value |
| **9c** | Tools step dimming + inline incompatibility notes | Surfaces the matrix without blocking the user |
| **9d** | Review · CompatibilityCard + Resolve flow + provider filter on Configure | Closes the loop before Generate |
| **9e** | Export grid greying + Runtime-adapter modal lookup; Marketplace hyperscaler facet | Same matrix, two more consumers |
| **9f** | Settings → Providers grouping + hyperscaler chips | Polish; no logic change |

Each batch ships independently — earlier ones are safe to merge while
later ones are still in review.

## 8 · Risks & open questions

- **Adapter quality.** Marking a hyperscaler as `◐` (via adapter) is
  cheap to declare in the matrix but expensive to validate. We should
  back this with a "verified" flag set only after a CI integration test
  passes, and surface `unverified` as a separate severity.
- **Strands availability.** AWS Strands is a recent release; we should
  pin a minimum AWS SDK version in the manifest and surface it in the
  Compatibility card so the user can pre-flight the upgrade.
- **Bedrock pricing vs. Azure OpenAI quotas.** Out of scope for this
  design (Compatibility ≠ Cost), but we should add a `pricing_hint`
  field to the matrix in a later iteration.
- **Plug-in templates.** Custom frameworks ship via the Plug-in
  templates section of Settings; their compatibility row should be
  declared in the template manifest, not hard-coded.
- **Localisation.** The Pattern card copy from the comparison slide is
  Italian; we keep English in product and treat the slide as the canonical
  reference for *intent* only.

## 9 · Done when

- [ ] A user describing *"AWS pipeline that summarises invoices"* lands
      on Strands by default, sees its hyperscaler badge, reads the
      assembly-line pattern and risk callout, and gets *only* AWS-
      compatible tools, providers, and export targets surfaced.
- [ ] Switching to Azure on the facet rail repaints the grid to AutoGen
      + watsonx + LangGraph + CrewAI, the Pattern card updates, and
      Bedrock disappears from the export grid.
- [ ] The Review's Compatibility card never shows an incompatible
      configuration as `ok` — every red row has a working Resolve
      action that re-opens the offending step pre-filtered.
- [ ] All matrix data is one tree-shakable module; adding a fourth
      hyperscaler is a one-file change.
