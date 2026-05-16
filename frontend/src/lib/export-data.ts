// Export & Publish — neutral export grid + MatrixHub publish flow + runtime
// adapter preview. The export catalogue lives here so adapters/visibility
// options/validation rows can be regenerated from a real backend later
// without rewriting the page components.

import type { IconName } from '@/components/icons/Icon';
import type { StagePill } from '@/components/primitives/Pill';

export interface ExportAdapter {
  id: string;
  label: string;
  /** Tertiary subline shown under the label. */
  sub: string;
  /** Optional Icon name. HomePilot uses its own brand mark and leaves this
   * undefined so the renderer knows to swap to <HomePilotMark>. */
  icon?: IconName;
  stage: StagePill;
  /** Set to true for HomePilot — drives the brand mark + opens the
   * runtime adapter preview modal when clicked. */
  homepilot?: boolean;
}

export interface ExportGroup {
  category: string;
  items: ExportAdapter[];
}

export const EXPORT_GROUPS: ExportGroup[] = [
  {
    category: 'Repository',
    items: [
      { id: 'github', label: 'GitHub', sub: 'ruslanmv/arxiv-digest', icon: 'cube',   stage: 'core' },
      { id: 'gitlab', label: 'GitLab', sub: 'group / project',       icon: 'cube',   stage: 'core' },
    ],
  },
  {
    category: 'Runtime / demo',
    items: [
      { id: 'docker', label: 'Docker',                  sub: 'multi-stage image',  icon: 'cog',    stage: 'core' },
      { id: 'hf',     label: 'Hugging Face Spaces',     sub: 'gradio · sdk',       icon: 'folder', stage: 'core' },
      { id: 'colab',  label: 'Google Colab',            sub: 'agent_demo.ipynb',   icon: 'doc',    stage: 'beta' },
      { id: 'vscode', label: 'VS Code workspace',       sub: '.code-workspace',    icon: 'doc',    stage: 'beta' },
    ],
  },
  {
    category: 'Cloud',
    items: [
      { id: 's3',    label: 'AWS S3',                   sub: 'signed upload',      icon: 'folder', stage: 'beta' },
      { id: 'azure', label: 'Azure Blob',               sub: 'storage account',    icon: 'folder', stage: 'beta' },
      { id: 'gcs',   label: 'Google Cloud Storage',     sub: 'bucket',             icon: 'folder', stage: 'coming-soon' },
    ],
  },
  {
    category: 'Enterprise / runtime',
    items: [
      { id: 'watsonx',   label: 'IBM watsonx Orchestrate', sub: 'agent.yaml + skills', icon: 'cube', stage: 'beta' },
      { id: 'azureai',   label: 'Azure AI / Microsoft',    sub: 'AI Foundry agent',    icon: 'cube', stage: 'coming-soon' },
      { id: 'homepilot', label: 'HomePilot',               sub: 'local-first runtime', stage: 'beta', homepilot: true },
    ],
  },
  {
    category: 'Local',
    items: [
      { id: 'zip', label: 'ZIP archive', sub: 'arxiv-digest.zip', icon: 'download', stage: 'core' },
    ],
  },
];

export const EXPORT_ADAPTER_COUNT = EXPORT_GROUPS.reduce((sum, g) => sum + g.items.length, 0);

// Right rail — featured MatrixHub publish target + secondary destinations
export interface PublishTarget {
  id: string;
  label: string;
  sub: string;
  icon: IconName;
  stage: StagePill;
}

export const PUBLISH_SECONDARY: PublishTarget[] = [
  { id: 'workspace', label: 'Private MatrixHub workspace', sub: 'selfrepair-dev / agents', icon: 'folder', stage: 'core' },
  { id: 'org',       label: 'Organization marketplace',   sub: 'selfrepair · 12 members', icon: 'agent',  stage: 'beta' },
];

// Run summary table
export interface RunSummaryRow {
  key: string;
  value: string;
  color?: 'ok' | 'warn' | 'err';
}

export const RUN_SUMMARY: RunSummaryRow[] = [
  { key: 'Framework',       value: 'CrewAI 0.74' },
  { key: 'LLM',             value: 'Claude Opus 4' },
  { key: 'Tokens',          value: '7,210' },
  { key: 'Latency',         value: '18.4 s' },
  { key: 'Tests',           value: '8/8 passing', color: 'ok' },
  { key: 'Permission mode', value: 'Safe' },
  { key: 'Risk level',      value: 'Medium', color: 'warn' },
];

// Runtime adapter presets — the modal's source data. HomePilot is the
// canonical example; anything else just slots into the same template.
export interface AdapterPreset {
  id: string;
  name: string;
  schema: string;
  /** "hp" tells the modal to render <HomePilotMark> instead of a generic
   * cube. */
  mark: 'hp' | 'generic';
  runtime: string;
  location: string;
  /** Whether to show the autonomy radio (Ask / Auto / Plan only). */
  autonomy: boolean;
}

export const ADAPTER_PRESETS: Record<string, AdapterPreset> = {
  homepilot: {
    id: 'homepilot',
    name: 'HomePilot',
    schema: 'homepilot.agent.v1',
    mark: 'hp',
    runtime: 'MCP · local-first',
    location: '~/Library/HomePilot/agents/arxiv-digest',
    autonomy: true,
  },
  watsonx: {
    id: 'watsonx',
    name: 'IBM watsonx Orchestrate',
    schema: 'watsonx.agent.v1',
    mark: 'generic',
    runtime: 'Cloud · enterprise',
    location: 'orchestrate://workspace/agents/arxiv-digest',
    autonomy: false,
  },
};

export type DependencyStatus = 'ok' | 'warn' | 'no';

export interface DependencyRow {
  status: DependencyStatus;
  label: string;
  note: string;
}

export const ADAPTER_DEPENDENCIES: DependencyRow[] = [
  { status: 'ok',   label: 'web_search',      note: 'available · MCP catalog' },
  { status: 'ok',   label: 'pdf_reader',      note: 'available · MCP catalog' },
  { status: 'ok',   label: 'file_writer',     note: 'sandbox' },
  { status: 'warn', label: 'email_send',      note: 'needs SMTP_API_KEY' },
  { status: 'no',   label: 'arxiv connector', note: 'will install on import' },
];

export type AutonomyMode = 'ask' | 'auto' | 'plan';

export const AUTONOMY_OPTIONS: { id: AutonomyMode; label: string; blurb: string }[] = [
  { id: 'ask',  label: 'Ask before acting', blurb: 'Approve risky tool calls.' },
  { id: 'auto', label: 'Auto',              blurb: 'Run end-to-end without prompts.' },
  { id: 'plan', label: 'Plan only',         blurb: 'Show steps; never execute.' },
];

export interface AdapterPermission {
  label: string;
  value: string;
  status: DependencyStatus;
}

export const ADAPTER_PERMISSIONS: AdapterPermission[] = [
  { label: 'Network',          value: 'allow',              status: 'ok' },
  { label: 'Filesystem write', value: 'sandbox',            status: 'ok' },
  { label: 'Email send',       value: 'requires_approval',  status: 'warn' },
  { label: 'Shell exec',       value: 'denied',             status: 'no' },
];

// MatrixHub publish — validation rows
export interface ValidationRow {
  status: 'ok' | 'warn' | 'no';
  label: string;
  note: string;
}

export const VALIDATION_ROWS: ValidationRow[] = [
  { status: 'ok',   label: 'Manifest schema valid',       note: 'agent.manifest.json · v1' },
  { status: 'ok',   label: 'README exists',               note: '6 KB · sections detected' },
  { status: 'ok',   label: 'License exists',              note: 'Apache-2.0' },
  { status: 'ok',   label: 'SECURITY.md exists',          note: 'disclosure policy present' },
  { status: 'ok',   label: 'No secrets detected',         note: 'gitleaks · 0 findings' },
  { status: 'ok',   label: 'Required env vars documented', note: '2 / 2 in .env.example' },
  { status: 'ok',   label: 'Tests included',              note: '8 unit · 2 dry-run' },
  { status: 'ok',   label: 'Dry-run works',               note: 'mock tools · all green' },
  { status: 'ok',   label: 'Permission manifest present', note: '4 capabilities declared' },
  { status: 'warn', label: 'No unsafe shell access',      note: 'shell_exec disabled by default · ✓' },
];

export const VALIDATION_PASSING = VALIDATION_ROWS.filter((r) => r.status === 'ok').length;

// Package preview tree on the Validation step
export interface PackageNode {
  name: string;
  depth: number;
  folder: boolean;
  badge?: 'pkg' | 'mh';
}

export const PACKAGE_TREE: PackageNode[] = [
  { name: 'agent-package/',          depth: 0, folder: true },
  { name: 'agent.manifest.json',     depth: 1, folder: false, badge: 'pkg' },
  { name: 'matrixhub.manifest.json', depth: 1, folder: false, badge: 'mh' },
  { name: 'agents/',                 depth: 1, folder: true },
  { name: 'tools/',                  depth: 1, folder: true },
  { name: 'prompts/',                depth: 1, folder: true },
  { name: 'knowledge/',              depth: 1, folder: true },
  { name: 'examples/',               depth: 1, folder: true },
  { name: 'tests/',                  depth: 1, folder: true },
  { name: 'screenshots/',            depth: 1, folder: true },
  { name: 'README.md',               depth: 1, folder: false },
  { name: 'LICENSE',                 depth: 1, folder: false },
  { name: 'SECURITY.md',             depth: 1, folder: false },
  { name: '.env.example',            depth: 1, folder: false },
];

export interface MetadataRow {
  key: string;
  value: string;
  mono?: boolean;
}

export const METADATA_ROWS: MetadataRow[] = [
  { key: 'Name',       value: 'Daily Research Digest' },
  { key: 'Slug',       value: 'daily-research-digest', mono: true },
  { key: 'Category',   value: 'Research' },
  { key: 'Tags',       value: 'research · arxiv · summarization · digest' },
  { key: 'Maintainer', value: 'Ruslan Magana' },
  { key: 'License',    value: 'Apache-2.0', mono: true },
];

export const MATRIXHUB_MANIFEST = `{
  "schema": "matrixhub.agent.v1",
  "name": "Daily Research Digest",
  "slug": "daily-research-digest",
  "category": "research",
  "asset_type": "agent_template",
  "frameworks": ["crewai", "langgraph"],
  "runtimes": ["docker", "homepilot", "watsonx_orchestrate"],
  "license": "Apache-2.0",
  "safety": { "risk_level": "medium",
              "requires_human_approval": ["email_send"],
              "disallowed_by_default": ["shell_exec"] }
}`;

// Visibility options
export interface VisibilityOption {
  id: 'public' | 'unlisted' | 'private' | 'org';
  icon: IconName;
  label: string;
  blurb: string;
  meta: string;
  counts: string[];
  stage?: StagePill;
}

export const VISIBILITY_OPTIONS: VisibilityOption[] = [
  {
    id: 'public',
    icon: 'cube',
    label: 'Public community',
    blurb: 'Anyone can discover, install, and fork. Indexed by Marketplace.',
    meta: 'matrixhub.com/agents/daily-research-digest',
    counts: ['unlimited installs', 'community ratings', 'community fork'],
  },
  {
    id: 'unlisted',
    icon: 'link',
    label: 'Unlisted link',
    blurb: 'Only people with the link can install.',
    meta: 'matrixhub.com/u/7b3f-4a2e',
    counts: ['hidden from search', 'no ratings'],
  },
  {
    id: 'private',
    icon: 'folder',
    label: 'Private workspace',
    blurb: 'Only you and people you invite to selfrepair-dev.',
    meta: 'workspace · selfrepair-dev / agents',
    counts: ['12 members', 'SSO required'],
  },
  {
    id: 'org',
    icon: 'agent',
    label: 'Organization marketplace',
    blurb: 'Visible to everyone in selfrepair (not public).',
    meta: 'org · selfrepair',
    stage: 'beta',
    counts: ['org-wide', 'maintainer review'],
  },
];

// Step 3 (Published) — listing tags + next-actions
export const PUBLISHED_TAGS = [
  'Apache-2.0', 'CrewAI', 'LangGraph', 'docker', 'homepilot', 'watsonx',
  'requires API key', 'no shell access', 'medium risk',
];

export const PUBLISHED_STATS: [string, string][] = [
  ['Installs', '0'],
  ['Stars',    '0'],
  ['Forks',    '0'],
  ['Version',  'v0.1.0'],
  ['Updated',  'just now'],
];

export interface NextAction {
  icon: IconName;
  label: string;
  sub: string;
  mono?: boolean;
}

export const PUBLISHED_NEXT: NextAction[] = [
  { icon: 'link',    label: 'Copy install command',  sub: 'matrixhub install daily-research-digest', mono: true },
  { icon: 'arrow',   label: 'View listing',          sub: 'matrixhub.com/agents/daily-research-digest', mono: true },
  { icon: 'send',    label: 'Share link',            sub: 'X · LinkedIn · Slack' },
  { icon: 'cube',    label: 'Mirror to GitHub',      sub: 'ruslanmv/daily-research-digest' },
  { icon: 'history', label: 'View version history',  sub: '1 version' },
];
