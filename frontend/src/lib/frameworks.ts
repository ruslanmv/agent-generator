// Extended framework catalogue — vendor + philosophy + hyperscalers +
// pattern descriptor. Used by the Framework & Model v2 step (Batch 10)
// and the Compatibility diagnostics.
//
// Distinct from the legacy `FRAMEWORKS` in `wizard-data.ts` which the
// existing Step 2 still consumes. Once Batch 10 lands, the legacy export
// becomes a thin re-export of this one.

import type { HyperscalerId, VendorId } from './hyperscalers';
import type { StagePill } from '@/components/primitives/Pill';

export type FrameworkId =
  | 'autogen'
  | 'strands'
  | 'langgraph'
  | 'crewai'
  | 'wxo'
  | 'crewflow'
  | 'react'
  | 'llamaidx';

export type PhilosophyId = 'brainstorm' | 'pipeline' | 'graph';

export interface Philosophy {
  id: PhilosophyId;
  label: string;
  blurb: string;
  /** Matches the PatternGlyph kind in the design canvas. */
  icon: PhilosophyId;
}

export const PHILOSOPHIES: Philosophy[] = [
  { id: 'brainstorm', label: 'Brainstorm',    blurb: 'Free back-and-forth between agents.',     icon: 'brainstorm' },
  { id: 'pipeline',   label: 'Assembly line', blurb: 'Linear hand-off, no loops.',              icon: 'pipeline'   },
  { id: 'graph',      label: 'Industrial',    blurb: 'Explicit state machine with branches.',   icon: 'graph'      },
];

export interface FrameworkPattern {
  summary: string;
  risk: string;
  glyph: PhilosophyId;
}

export interface FrameworkX {
  id: FrameworkId;
  name: string;
  vendor: VendorId;
  philosophy: PhilosophyId;
  pattern: FrameworkPattern;
  hyperscalers: HyperscalerId[];
  stage: StagePill;
}

export const FRAMEWORKS_X: FrameworkX[] = [
  {
    id: 'autogen',
    name: 'AutoGen',
    vendor: 'microsoft',
    philosophy: 'brainstorm',
    pattern: {
      summary: 'Free back-and-forth — write, critique, fix.',
      risk: 'May argue forever or drift off-topic if not monitored.',
      glyph: 'brainstorm',
    },
    hyperscalers: ['azure', 'on_prem'],
    stage: 'beta',
  },
  {
    id: 'strands',
    name: 'Strands',
    vendor: 'amazon',
    philosophy: 'pipeline',
    pattern: {
      summary: 'Assembly line — output of one agent feeds the next.',
      risk: 'A bad step taints every downstream agent.',
      glyph: 'pipeline',
    },
    hyperscalers: ['aws', 'on_prem'],
    stage: 'new',
  },
  {
    id: 'langgraph',
    name: 'LangGraph',
    vendor: 'langchain',
    philosophy: 'graph',
    pattern: {
      summary: 'Industrial process — explicit state machine with gated branches.',
      risk: 'Higher design cost; every transition must be modeled.',
      glyph: 'graph',
    },
    hyperscalers: ['azure', 'aws', 'gcp', 'ibm', 'on_prem'],
    stage: 'core',
  },
  {
    id: 'crewai',
    name: 'CrewAI',
    vendor: 'crewai',
    philosophy: 'pipeline',
    pattern: {
      summary: 'Role-based crews — supervisor delegates to specialists.',
      risk: 'Linear hand-offs; limited self-correction.',
      glyph: 'pipeline',
    },
    hyperscalers: ['azure', 'aws', 'gcp', 'ibm', 'on_prem'],
    stage: 'core',
  },
  {
    id: 'wxo',
    name: 'watsonx Orchestrate',
    vendor: 'ibm',
    philosophy: 'pipeline',
    pattern: {
      summary: 'Enterprise skills — supervisor routes to typed skills.',
      risk: 'IBM cloud-centric; limited multi-vendor reach.',
      glyph: 'pipeline',
    },
    hyperscalers: ['ibm'],
    stage: 'core',
  },
  {
    id: 'crewflow',
    name: 'CrewAI Flow',
    vendor: 'crewai',
    philosophy: 'graph',
    pattern: {
      summary: 'Event-driven flow with named transitions.',
      risk: 'Newer API; fewer community recipes.',
      glyph: 'graph',
    },
    hyperscalers: ['azure', 'aws', 'gcp', 'on_prem'],
    stage: 'beta',
  },
  {
    id: 'react',
    name: 'ReAct',
    vendor: 'community',
    philosophy: 'brainstorm',
    pattern: {
      summary: 'Reason → Act → Observe loop.',
      risk: 'Loops may stall without explicit termination.',
      glyph: 'brainstorm',
    },
    hyperscalers: ['azure', 'aws', 'gcp', 'ibm', 'on_prem'],
    stage: 'core',
  },
  {
    id: 'llamaidx',
    name: 'LlamaIndex',
    vendor: 'community',
    philosophy: 'graph',
    pattern: {
      summary: 'Data-centric agents over RAG pipelines.',
      risk: 'Best for retrieval; limited multi-step tool use.',
      glyph: 'graph',
    },
    hyperscalers: ['azure', 'aws', 'gcp', 'ibm', 'on_prem'],
    stage: 'beta',
  },
];

export function framework(id: FrameworkId): FrameworkX {
  return FRAMEWORKS_X.find((f) => f.id === id) ?? FRAMEWORKS_X[2]; // default → LangGraph
}

export type ExportTargetId =
  | 'azure-ai'
  | 'bedrock'
  | 'docker'
  | 'hf'
  | 'zip'
  | 'github'
  | 'watsonx';

/** Per-framework whitelist of export targets. `'*'` = all targets allowed
 * (the framework is portable enough that no filtering is necessary). */
export const EXPORT_BY_FW: Record<FrameworkId, '*' | ExportTargetId[]> = {
  autogen:   ['azure-ai', 'docker', 'hf', 'zip', 'github'],
  strands:   ['bedrock', 'docker', 'zip', 'github'],
  langgraph: '*',
  crewai:    '*',
  llamaidx:  '*',
  react:     '*',
  crewflow:  '*',
  wxo:       ['watsonx', 'docker', 'github'],
};
