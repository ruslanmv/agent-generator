// Shared types + helpers for the Agent Projects workspace.
//
// "Stage" is the generator-only lifecycle — there is no production
// runtime in this product, so we deliberately do not surface tokens,
// cost, success rate, or "Last run". The vocabulary table below maps
// the design's recommended language onto the in-memory project shape
// the demo backend exposes at GET /api/projects.

import type { IconName } from '@/components/icons/Icon';
import { tokens } from '@/styles/tokens';

export type ProjectStage =
  | 'draft'
  | 'configured'
  | 'generated'
  | 'needs-setup'
  | 'needs-review'
  | 'exported'
  | 'template';

export interface ProjectVm {
  id: string;
  name: string;
  /** Short, single-line description derived from the source prompt. */
  description: string;
  framework: string;
  /** Compact framework label rendered next to the dot in tables. */
  frameworkShort: string;
  agents: number;
  tools: number;
  files: number;
  /** What the generator emits (Python package, watsonx ADK, Docker bundle…). */
  output: string;
  stage: ProjectStage;
  /** Human-readable relative timestamp ("2m ago", "yesterday"). */
  updated: string;
  visibility: 'private' | 'org' | 'public';
  starred: boolean;
  /** Optional env vars / external deps the generated project will need
   * after the user unpacks it locally. Drives the amber "Setup
   * required" affordance on the Project detail page. */
  setupRequired?: string[];
}

export interface ProjectsSummary {
  total: number;
  generated: number;
  drafts: number;
  templates: number;
  needsReview: number;
  lastGeneratedRel: string | null;
}

/** Brand colour per framework, used for the dot + avatar in the detail header. */
export const FRAMEWORK_COLORS: Record<string, string> = {
  crewai: tokens.accent,
  langgraph: '#0e6027',
  react: '#7c3aed',
  wxo: '#054ada',
  watsonx_orchestrate: '#054ada',
  crewai_flow: '#0a3df0',
  autogen: '#0078d4',
  llamaidx: '#b28600',
  llamaindex: '#b28600',
};

export function frameworkColor(fw: string): string {
  return FRAMEWORK_COLORS[fw] ?? tokens.ink2;
}

/** Compact label rendered in the row + chip — keeps wxo/llamaidx visual mass low. */
export function frameworkShort(fw: string): string {
  switch (fw) {
    case 'watsonx_orchestrate':
      return 'wxo';
    case 'crewai_flow':
      return 'crewai-flow';
    case 'llamaindex':
      return 'llamaidx';
    default:
      return fw;
  }
}

export interface StageMeta {
  label: string;
  bg: string;
  fg: string;
  border: string;
}

export const STAGE_META: Record<ProjectStage, StageMeta> = {
  draft: { label: 'Draft', bg: tokens.surface, fg: tokens.muted, border: tokens.border },
  configured: {
    label: 'Configured',
    bg: tokens.accentHi,
    fg: tokens.accentDim,
    border: 'transparent',
  },
  generated: { label: 'Generated', bg: '#defbe6', fg: '#0e6027', border: 'transparent' },
  'needs-setup': {
    label: 'Needs setup',
    bg: '#fcf4d6',
    fg: '#684e00',
    border: 'transparent',
  },
  'needs-review': {
    label: 'Needs review',
    bg: '#fff1f1',
    fg: tokens.err,
    border: 'transparent',
  },
  exported: { label: 'Exported', bg: '#e5deff', fg: '#3a1a82', border: 'transparent' },
  template: { label: 'Template', bg: tokens.ink, fg: '#fff', border: 'transparent' },
};

export interface QuickView {
  id: 'all' | 'drafts' | 'generated' | 'review' | 'templates' | 'exported';
  label: string;
  icon: IconName;
  matches: (p: ProjectVm) => boolean;
}

export const QUICK_VIEWS: QuickView[] = [
  { id: 'all', label: 'All projects', icon: 'folder', matches: () => true },
  { id: 'drafts', label: 'Drafts', icon: 'doc', matches: (p) => p.stage === 'draft' },
  {
    id: 'generated',
    label: 'Generated',
    icon: 'check',
    matches: (p) => p.stage === 'generated' || p.stage === 'exported',
  },
  {
    id: 'review',
    label: 'Needs review',
    icon: 'x',
    matches: (p) => p.stage === 'needs-review' || p.stage === 'needs-setup',
  },
  { id: 'templates', label: 'Templates', icon: 'cube', matches: (p) => p.stage === 'template' },
  { id: 'exported', label: 'Exported', icon: 'download', matches: (p) => p.stage === 'exported' },
];
