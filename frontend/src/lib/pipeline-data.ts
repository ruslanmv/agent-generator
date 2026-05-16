// Initial pipeline graph + library taxonomy. The PipelineEditor owns a
// mutable copy in component state so users can drag nodes around and
// (later) add/remove them; this module is just the seed.

import type { IconName } from '@/components/icons/Icon';

export type NodeKind = 'input' | 'agent' | 'tool' | 'llm' | 'output';

export interface PipelineNode {
  id: string;
  kind: NodeKind;
  x: number;
  y: number;
  label: string;
  sub: string;
  goal?: string;
  backstory?: string;
  llm?: string;
  maxIter?: number;
  tools?: string[];
}

export const NODE_W = 156;
export const NODE_H = 56;

export const INITIAL_NODES: PipelineNode[] = [
  { id: 'in',  kind: 'input',  x: 40,  y: 200, label: 'User prompt',     sub: 'string' },
  { id: 'r',   kind: 'agent',  x: 240, y: 80,  label: 'researcher',      sub: 'arXiv crawl',
    goal: 'Find recent arXiv papers on agent orchestration',
    backstory: 'A rigorous, terse analyst who cites sources.',
    llm: 'claude-opus-4', maxIter: 8, tools: ['web_search', 'pdf_reader'] },
  { id: 's',   kind: 'agent',  x: 240, y: 220, label: 'summarizer',      sub: 'top-5 distil',
    goal: 'Reduce each paper to 3 bullet points',
    backstory: 'A precise, ruthless editor.',
    llm: 'claude-opus-4', maxIter: 5, tools: ['pdf_reader', 'web_search'] },
  { id: 'w',   kind: 'agent',  x: 240, y: 360, label: 'writer',          sub: 'compose digest',
    goal: 'Compose digest, send via email',
    backstory: 'A house style strict copywriter.',
    llm: 'claude-opus-4', maxIter: 3, tools: ['email_send'] },
  { id: 't1',  kind: 'tool',   x: 460, y: 60,  label: 'web_search',      sub: 'tavily' },
  { id: 't2',  kind: 'tool',   x: 460, y: 200, label: 'pdf_reader',      sub: 'pypdf' },
  { id: 't3',  kind: 'tool',   x: 460, y: 340, label: 'email_send',      sub: 'sendgrid' },
  { id: 'llm', kind: 'llm',    x: 680, y: 200, label: 'claude-opus-4',   sub: 'anthropic' },
  { id: 'out', kind: 'output', x: 880, y: 200, label: 'digest.md',       sub: 'file + email' },
];

export const INITIAL_EDGES: [string, string][] = [
  ['in', 'r'], ['in', 's'], ['in', 'w'],
  ['r', 't1'], ['s', 't2'], ['w', 't3'],
  ['r', 'llm'], ['s', 'llm'], ['w', 'llm'],
  ['llm', 'out'],
];

export const NODE_META: Record<NodeKind, { color: string; icon: IconName; label: string }> = {
  input:  { color: '#393939', icon: 'send',     label: 'input' },
  agent:  { color: '#0a3df0', icon: 'agent',    label: 'agent' },
  tool:   { color: '#161616', icon: 'tool',     label: 'tool' },
  llm:    { color: '#7c3aed', icon: 'llm',      label: 'llm' },
  output: { color: '#198038', icon: 'download', label: 'output' },
};

export interface LibraryGroup {
  heading: string;
  kind: NodeKind;
  items: string[];
}

export const LIBRARY: LibraryGroup[] = [
  { heading: 'Agents',  kind: 'agent', items: ['researcher', 'summarizer', 'writer', 'critic', 'router'] },
  { heading: 'Tools',   kind: 'tool',  items: ['web_search', 'pdf_reader', 'sql_query', 'http_request', 'email_send', 'image_analyze'] },
  { heading: 'Models',  kind: 'llm',   items: ['claude-opus-4', 'claude-haiku-4', 'gpt-4.1', 'llama-3.1-70b'] },
  { heading: 'Control', kind: 'agent', items: ['if / else', 'parallel', 'loop', 'human review'] },
];

export type CanvasTool = 'select' | 'move' | 'connect';
