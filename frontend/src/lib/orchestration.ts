// Orchestration patterns — Supervisor vs ReAct.
// Drives the Pattern row + Pattern card on Step 2 and the Orchestration
// row on the Review · Compatibility card.
//
// Pure data — see docs/wizard-orchestration-patterns-design.md for the
// rationale and the brief these axes mirror.

import type { FrameworkId } from './frameworks';

export type OrchestrationPatternId = 'supervisor' | 'react';

export type AxisLevel = 'low' | 'medium' | 'high';

export interface OrchestrationPattern {
  id: OrchestrationPatternId;
  label: string;
  /** ASCII glyph used in cards + the Pattern row tile. */
  glyph: string;
  /** One-line picker tile blurb. */
  blurb: string;
  /** Ordered behaviour rendered in the Pattern card. */
  steps: string[];
  /** Trade-off axes mirroring the comparison table on the brief's
   * second slide. */
  axes: {
    flow:          string;
    communication: string;
    flexibility:   AxisLevel;
    predictability: AxisLevel;
    cost:          AxisLevel;
  };
}

export const ORCHESTRATION_PATTERNS: OrchestrationPattern[] = [
  {
    id: 'supervisor',
    label: 'Supervisor',
    glyph: '⊕',
    blurb: 'One supervisor coordinates multiple workers.',
    steps: [
      'Receive the task from the user.',
      'Pick which specialised agent to call.',
      "Pass one agent's output as input to the next.",
      'Own the overall flow.',
    ],
    axes: {
      flow:           'The chief agent',
      communication:  'Direct, top-down',
      flexibility:    'low',
      predictability: 'high',
      cost:           'low',
    },
  },
  {
    id: 'react',
    label: 'ReAct',
    glyph: '◎',
    blurb: 'Reason → Act → Observe → Re-reason. Optionally over shared state.',
    steps: [
      'Reason about the problem.',
      'Act (call a tool or another agent).',
      'Observe the result.',
      'Re-reason and decide the next step.',
    ],
    axes: {
      flow:           'State + each agent autonomously',
      communication:  'Via shared state (multi-agent)',
      flexibility:    'high',
      predictability: 'low',
      cost:           'high',
    },
  },
];

export type PatternSupport = 'native' | 'adapter' | 'unsupported';

/** Pattern × Framework matrix. `unsupported` rows hide the tile in the
 * picker; `adapter` rows render with a `⚠ via adapter` ribbon. */
export const PATTERN_BY_FW: Record<FrameworkId, Record<OrchestrationPatternId, PatternSupport>> = {
  langgraph: { supervisor: 'native',      react: 'native'      },
  autogen:   { supervisor: 'native',      react: 'adapter'     },
  strands:   { supervisor: 'native',      react: 'unsupported' },
  crewai:    { supervisor: 'native',      react: 'adapter'     },
  crewflow:  { supervisor: 'native',      react: 'adapter'     },
  react:     { supervisor: 'unsupported', react: 'native'      },
  wxo:       { supervisor: 'native',      react: 'unsupported' },
  llamaidx:  { supervisor: 'adapter',     react: 'native'      },
};

export function pattern(id: OrchestrationPatternId): OrchestrationPattern {
  return ORCHESTRATION_PATTERNS.find((p) => p.id === id) ?? ORCHESTRATION_PATTERNS[0];
}
