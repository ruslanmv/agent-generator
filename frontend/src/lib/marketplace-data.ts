// Matrix Hub catalog — sample fixture mirroring the prototype. The shape
// matches the public catalog API (agents, tools, mcp_servers, hybrid
// search, capability/framework/provider facets, install plans) so the
// frontend can swap to live data later without component rewrites.

import type { IconName } from '@/components/icons/Icon';

export type AssetType = 'any' | 'agent' | 'tool' | 'mcp_server';
export type SearchMode = 'keyword' | 'semantic' | 'hybrid';
export type ArtifactKind = 'pip' | 'docker' | 'git' | 'zip';

export interface MarketplaceItem {
  id: string;
  type: Exclude<AssetType, 'any'>;
  name: string;
  org: string;
  version: string;
  stars: number;
  installs: string;
  summary: string;
  capabilities: string[];
  frameworks: string[];
  providers: string[];
  score: number;
  verified: boolean;
  kind: ArtifactKind;
}

export interface AssetTypeMeta {
  id: AssetType;
  label: string;
  icon: IconName;
  count: number;
}

export const MH_TYPES: AssetTypeMeta[] = [
  { id: 'any',        label: 'All',         icon: 'cube',  count: 1284 },
  { id: 'agent',      label: 'Agents',      icon: 'agent', count: 412  },
  { id: 'tool',       label: 'Tools',       icon: 'tool',  count: 631  },
  { id: 'mcp_server', label: 'MCP servers', icon: 'flow',  count: 241  },
];

export const MH_CAPABILITIES = [
  'pdf', 'summarize', 'web_search', 'sql', 'vector', 'email',
  'calendar', 'browser', 'voice', 'vision', 'crm', 'rag', 'translate',
];

export const MH_FRAMEWORKS = [
  'crewai', 'langgraph', 'watsonx_orchestrate', 'autogen',
  'llamaindex', 'react', 'crewflow',
];

export const MH_PROVIDERS = [
  'anthropic', 'openai', 'watsonx', 'ollabridge', 'ollama', 'mistral',
];

export const SEARCH_MODES: SearchMode[] = ['keyword', 'semantic', 'hybrid'];

export const MH_SEARCH_HINTS = [
  'watsonx orchestrate skills',
  'browser automation',
  'docling',
  'crm sync',
  'voice agent',
];

export const MH_ITEMS: MarketplaceItem[] = [
  {
    id: 'agent:pdf-summarizer@1.4.2',
    type: 'agent',
    name: 'PDF Summarizer',
    org: 'agent-matrix',
    version: '1.4.2',
    stars: 842,
    installs: '12.4k',
    summary: 'Summarizes long PDF documents into concise points with citations.',
    capabilities: ['pdf', 'summarize'],
    frameworks: ['langgraph'],
    providers: ['watsonx', 'anthropic'],
    score: 0.83,
    verified: true,
    kind: 'pip',
  },
  {
    id: 'mcp_server:browser-use@0.7.1',
    type: 'mcp_server',
    name: 'Browser Use',
    org: 'browser-use',
    version: '0.7.1',
    stars: 5210,
    installs: '48.1k',
    summary: 'Headless Chrome MCP server. Click, type, scroll, screenshot. 14 tools.',
    capabilities: ['browser', 'web'],
    frameworks: ['*'],
    providers: ['*'],
    score: 0.91,
    verified: true,
    kind: 'docker',
  },
  {
    id: 'tool:docling@2.1.0',
    type: 'tool',
    name: 'Docling',
    org: 'IBM',
    version: '2.1.0',
    stars: 18900,
    installs: '210k',
    summary: 'High-fidelity document parsing — PDF, DOCX, XLSX, HTML → structured JSON.',
    capabilities: ['pdf', 'parse'],
    frameworks: ['*'],
    providers: ['*'],
    score: 0.88,
    verified: true,
    kind: 'pip',
  },
  {
    id: 'mcp_server:gcal@1.2.0',
    type: 'mcp_server',
    name: 'Google Calendar',
    org: 'google',
    version: '1.2.0',
    stars: 1240,
    installs: '9.8k',
    summary: 'Read/write events, free-busy, attendee invites. OAuth scoped.',
    capabilities: ['calendar'],
    frameworks: ['*'],
    providers: ['*'],
    score: 0.79,
    verified: true,
    kind: 'docker',
  },
  {
    id: 'agent:research-crew@2.0.0',
    type: 'agent',
    name: 'Research Crew',
    org: 'crewai-examples',
    version: '2.0.0',
    stars: 612,
    installs: '4.1k',
    summary: 'Three-agent crew: planner → researcher → writer. arXiv + web.',
    capabilities: ['web_search', 'rag'],
    frameworks: ['crewai'],
    providers: ['anthropic', 'openai'],
    score: 0.77,
    verified: false,
    kind: 'git',
  },
  {
    id: 'tool:postgres-sql@0.9.4',
    type: 'tool',
    name: 'Postgres SQL',
    org: 'community',
    version: '0.9.4',
    stars: 318,
    installs: '6.7k',
    summary: 'Typed read-only SQL tool. Schema introspection + safe parameter binding.',
    capabilities: ['sql'],
    frameworks: ['*'],
    providers: ['*'],
    score: 0.74,
    verified: false,
    kind: 'pip',
  },
  {
    id: 'mcp_server:slack@1.5.0',
    type: 'mcp_server',
    name: 'Slack',
    org: 'slack',
    version: '1.5.0',
    stars: 2104,
    installs: '18.3k',
    summary: 'Send messages, search channels, manage threads. 22 tools.',
    capabilities: ['comms'],
    frameworks: ['*'],
    providers: ['*'],
    score: 0.81,
    verified: true,
    kind: 'docker',
  },
  {
    id: 'agent:legal-redliner@0.6.1',
    type: 'agent',
    name: 'Legal Redliner',
    org: 'lawless-ai',
    version: '0.6.1',
    stars: 207,
    installs: '1.8k',
    summary: 'Diff two contracts, surface clause-level changes with risk scoring.',
    capabilities: ['pdf', 'compare'],
    frameworks: ['langgraph'],
    providers: ['anthropic'],
    score: 0.72,
    verified: false,
    kind: 'pip',
  },
];

// Helpers used by Detail to derive sub-fields without re-parsing on every
// render.

export function packageName(id: string): string {
  return id.split(':')[1].split('@')[0];
}

export function snakeName(id: string): string {
  return packageName(id).replace(/-/g, '_');
}

export function buildManifest(item: MarketplaceItem): string {
  const pkg = packageName(item.id);
  return `schema_version: 1
type: ${item.type}
id: ${pkg}
name: ${item.name}
version: ${item.version}
description: ${item.summary}
capabilities: [${item.capabilities.join(', ')}]
compatibility:
  frameworks: [${item.frameworks.join(', ')}]
  providers:  [${item.providers.join(', ')}]
artifacts:
  - kind: ${item.kind}
    spec: { package: ${pkg}, version: "==${item.version}" }
adapters:
  - framework: ${item.frameworks[0] === '*' ? 'crewai' : item.frameworks[0] || 'crewai'}
    template_key: ${item.frameworks[0] === '*' ? 'crewai' : item.frameworks[0] || 'crewai'}-node
mcp_registration:
  tool:
    name: ${snakeName(item.id)}
    integration_type: REST
    request_type: POST`;
}

export interface InstallStep {
  key: 'pip' | 'adapters' | 'gateway' | 'lockfile';
  command: string;
  status: 'ok' | 'run' | 'pending';
}

export function installPlan(item: MarketplaceItem, installing: boolean): InstallStep[] {
  const pkg = packageName(item.id);
  const fw = item.frameworks[0] === '*' ? 'crewai' : item.frameworks[0] || 'crewai';
  return [
    { key: 'pip',      command: `uv pip install ${pkg}==${item.version}`, status: 'ok' },
    { key: 'adapters', command: `write ${fw}-node`,                       status: 'ok' },
    { key: 'gateway',  command: 'register tool · MCP gateway',            status: installing ? 'run' : 'pending' },
    { key: 'lockfile', command: 'matrix.lock.json',                       status: 'pending' },
  ];
}
