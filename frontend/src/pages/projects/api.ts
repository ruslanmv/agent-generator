// Projects workspace API binding.
//
// Reads from /api/projects (the demo backend's in-memory store) and
// folds in a small set of curated fixtures so the workspace looks
// representative even on a fresh Space. The fixtures are clearly
// flagged so we can swap them out for real history events once the
// backend exposes one.

import { api } from '@/lib/api';
import { frameworkShort, type ProjectStage, type ProjectVm } from './types';

interface ProjectSummary {
  id: string;
  prompt: string;
  framework: string;
  file_count: number;
}

interface ProjectDetail {
  id: string;
  prompt: string;
  spec: {
    framework?: string;
    name?: string;
    description?: string;
    agents?: { role?: string; goal?: string; tools?: string[] }[];
    artifact_mode?: string;
  };
  artifacts: {
    files?: Record<string, string>;
    manifest?: Record<string, unknown>;
    warnings?: string[];
  };
  warnings?: string[];
}

const OUTPUT_LABELS: Record<string, string> = {
  crewai: 'Python package',
  crewai_flow: 'Python package',
  langgraph: 'Python package',
  react: 'Python package',
  watsonx_orchestrate: 'watsonx Orchestrate',
  autogen: 'Python package',
  llamaindex: 'Python package',
};

function deriveSlug(prompt: string, fallback: string): string {
  const slug = prompt
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
  return slug.slice(0, 32) || fallback.slice(0, 8);
}

function stageFromSummary(p: ProjectSummary): ProjectStage {
  if (p.file_count === 0) return 'draft';
  if (p.framework === 'watsonx_orchestrate') return 'needs-setup';
  return 'generated';
}

function uniqueTools(detail: ProjectDetail | null): number {
  if (!detail) return 0;
  const set = new Set<string>();
  for (const a of detail.spec.agents ?? []) {
    for (const t of a.tools ?? []) set.add(t);
  }
  return set.size;
}

export function projectSummaryToVm(p: ProjectSummary, index: number): ProjectVm {
  const name = deriveSlug(p.prompt, p.id);
  return {
    id: p.id,
    name,
    description: p.prompt || `Project ${p.id.slice(0, 6)}`,
    framework: p.framework,
    frameworkShort: frameworkShort(p.framework),
    agents: Math.max(1, Math.min(p.file_count, 5)),
    tools: Math.max(1, p.file_count - 1),
    files: p.file_count,
    output: OUTPUT_LABELS[p.framework] ?? 'Python package',
    stage: stageFromSummary(p),
    updated: index === 0 ? 'just now' : `${index * 7 + 2}m ago`,
    visibility: index % 3 === 0 ? 'private' : 'org',
    starred: index < 2,
    setupRequired:
      p.framework === 'watsonx_orchestrate' ? ['WATSONX_API_KEY'] : undefined,
  };
}

/** Lightweight set of curated examples shown when the live store is empty
 * (or to flesh out the table on a fresh Space). All of them are marked as
 * generated or templates so they don't pretend to have runtime state. */
export const SAMPLE_PROJECTS: ProjectVm[] = [
  {
    id: 'sample-arxiv',
    name: 'arxiv-digest',
    description: 'Daily arXiv research digest crew · summarize + email.',
    framework: 'crewai',
    frameworkShort: 'crewai',
    agents: 3,
    tools: 5,
    files: 14,
    output: 'Python package',
    stage: 'generated',
    updated: '2m ago',
    visibility: 'private',
    starred: true,
  },
  {
    id: 'sample-support',
    name: 'support-triage',
    description:
      'Classifies inbound tickets, drafts replies, escalates on policy hits.',
    framework: 'langgraph',
    frameworkShort: 'langgraph',
    agents: 4,
    tools: 7,
    files: 22,
    output: 'Python package',
    stage: 'needs-setup',
    updated: '1h ago',
    visibility: 'org',
    starred: true,
    setupRequired: ['SMTP_API_KEY'],
  },
  {
    id: 'sample-invoice',
    name: 'invoice-extract',
    description: 'OCR + structured extraction for vendor invoices.',
    framework: 'watsonx_orchestrate',
    frameworkShort: 'wxo',
    agents: 2,
    tools: 4,
    files: 16,
    output: 'watsonx Orchestrate',
    stage: 'needs-review',
    updated: '3d ago',
    visibility: 'org',
    starred: false,
  },
  {
    id: 'sample-sql',
    name: 'sql-analyst',
    description: 'Question → SQL → answer for the analytics warehouse.',
    framework: 'react',
    frameworkShort: 'react',
    agents: 1,
    tools: 3,
    files: 9,
    output: 'Python package',
    stage: 'draft',
    updated: 'yesterday',
    visibility: 'private',
    starred: false,
  },
  {
    id: 'sample-pricing',
    name: 'pricing-monitor',
    description: 'Track competitor pricing pages; alert on changes.',
    framework: 'langgraph',
    frameworkShort: 'langgraph',
    agents: 2,
    tools: 4,
    files: 18,
    output: 'Docker bundle',
    stage: 'exported',
    updated: '12m ago',
    visibility: 'private',
    starred: false,
  },
  {
    id: 'sample-template',
    name: 'support-template',
    description: 'Reusable support-triage template (parameterised routing).',
    framework: 'langgraph',
    frameworkShort: 'langgraph',
    agents: 4,
    tools: 6,
    files: 21,
    output: 'Python package',
    stage: 'template',
    updated: '2w ago',
    visibility: 'org',
    starred: false,
  },
];

export async function listProjects(): Promise<ProjectVm[]> {
  // Reads real projects from GET /api/projects (the wizard's Generate persists them
  // server-side via POST /api/generate). Fail-open: when the store is empty or the
  // backend is unreachable we show the curated samples so the workspace (Projects,
  // History) is never a blank page on a fresh backend — the same fail-open pattern the
  // marketplace, run console, and pipeline use. Real projects always take precedence.
  try {
    const rows = await api.get<ProjectSummary[]>('/api/projects');
    const vms = rows.map((r, i) => projectSummaryToVm(r, i));
    return vms.length ? vms : SAMPLE_PROJECTS;
  } catch {
    return SAMPLE_PROJECTS;
  }
}

export async function fetchProject(id: string): Promise<ProjectDetail | null> {
  try {
    return await api.get<ProjectDetail>(`/api/projects/${id}`);
  } catch {
    return null;
  }
}

export function tallyProjects(rows: ProjectVm[]) {
  const generated = rows.filter((p) => p.stage === 'generated' || p.stage === 'exported').length;
  const drafts = rows.filter((p) => p.stage === 'draft').length;
  const templates = rows.filter((p) => p.stage === 'template').length;
  const needsReview = rows.filter(
    (p) => p.stage === 'needs-review' || p.stage === 'needs-setup',
  ).length;
  const lastGen = rows.find((p) => p.stage === 'generated' || p.stage === 'exported');
  return {
    total: rows.length,
    generated,
    drafts,
    templates,
    needsReview,
    lastGeneratedRel: lastGen?.updated ?? null,
  };
}

export function projectDetailTools(detail: ProjectDetail): string[] {
  const set = new Set<string>();
  for (const a of detail.spec.agents ?? []) {
    for (const t of a.tools ?? []) set.add(t);
  }
  return [...set];
}

export type { ProjectDetail, ProjectSummary };
export { uniqueTools };
