// Static catalogues consumed by the Generate wizard. Lifted from the design
// handoff so the frontend matches the prototype 1:1 and can be wired to real
// API responses later without touching the components.

import type { StagePill } from '@/components/primitives/Pill';

export interface Framework {
  id: string;
  name: string;
  tag: string;
  stage: StagePill;
  rationale: string;
  structure: string;
}

export const FRAMEWORKS: Framework[] = [
  {
    id: 'crewai',
    name: 'CrewAI',
    tag: 'role-based crews',
    stage: 'core',
    rationale:
      'Your prompt names multiple specialised agents (researcher, summariser, writer) with explicit handoffs. CrewAI’s role-based crews map cleanly to that pattern.',
    structure: `my_project/
├── agents/
│   ├── researcher.py
│   ├── summarizer.py
│   └── writer.py
├── tasks/
├── tools/
└── crew.py`,
  },
  {
    id: 'langgraph',
    name: 'LangGraph',
    tag: 'state machine graph',
    stage: 'core',
    rationale: 'Pick LangGraph when control flow is the primary concern — branching, retries, human-in-the-loop.',
    structure: `my_project/
├── nodes/
├── edges/
├── state.py
└── graph.py`,
  },
  {
    id: 'react',
    name: 'ReAct',
    tag: 'reason + act loop',
    stage: 'core',
    rationale: 'A single agent that thinks, calls tools, and iterates until a goal is reached.',
    structure: `my_project/
├── tools/
├── prompts/
└── agent.py`,
  },
  {
    id: 'wxo',
    name: 'watsonx Orchestrate',
    tag: 'enterprise skills',
    stage: 'core',
    rationale: 'Best when targeting watsonx Orchestrate skills with enterprise governance.',
    structure: `my_project/
├── skills/
├── flows/
└── orchestrate.yaml`,
  },
  {
    id: 'crewflow',
    name: 'CrewAI Flow',
    tag: 'event-driven flow',
    stage: 'core',
    rationale: 'Event-driven sibling of CrewAI for streaming, async pipelines.',
    structure: `my_project/
├── events/
├── flows/
└── flow.py`,
  },
  {
    id: 'autogen',
    name: 'AutoGen',
    tag: 'conversational',
    stage: 'plugin',
    rationale: 'Conversational multi-agent. Excellent for back-and-forth analyst loops.',
    structure: `my_project/
├── agents/
└── conversation.py`,
  },
  {
    id: 'llamaidx',
    name: 'LlamaIndex',
    tag: 'data-centric agents',
    stage: 'plugin',
    rationale: 'Data-first agents — RAG over your corpus before reasoning.',
    structure: `my_project/
├── data/
├── indices/
└── agent.py`,
  },
  {
    id: 'custom',
    name: 'Custom template',
    tag: 'plug-in',
    stage: 'plugin',
    rationale: 'Bring your own scaffolding via a template manifest.',
    structure: `my_project/
└── (defined by template)`,
  },
];

export interface Tool {
  id: string;
  name: string;
  cat: ToolCategory;
  beta?: boolean;
}

export const TOOL_CATEGORIES = ['Web', 'Files', 'Data', 'Comms', 'Multimodal', 'Cloud', 'System'] as const;
export type ToolCategory = (typeof TOOL_CATEGORIES)[number];

export const TOOLS: Tool[] = [
  { id: 'search', name: 'web_search',     cat: 'Web' },
  { id: 'http',   name: 'http_request',   cat: 'Web' },
  { id: 'pdf',    name: 'pdf_reader',     cat: 'Files' },
  { id: 'fs',     name: 'file_writer',    cat: 'Files' },
  { id: 'sql',    name: 'sql_query',      cat: 'Data' },
  { id: 'vector', name: 'vector_search',  cat: 'Data' },
  { id: 'email',  name: 'email_send',     cat: 'Comms', beta: true },
  { id: 'slack',  name: 'slack_post',     cat: 'Comms', beta: true },
  { id: 'voice',  name: 'speech_to_text', cat: 'Multimodal', beta: true },
  { id: 'vision', name: 'image_analyze',  cat: 'Multimodal', beta: true },
  { id: 's3',     name: 'cloud_storage',  cat: 'Cloud',  beta: true },
  { id: 'shell',  name: 'shell_exec',     cat: 'System' },
];

export const SAMPLE_PROMPT =
  'A research crew that monitors arXiv for new agent-orchestration papers, summarizes the top 5 daily, and emails a digest to the team.';

export const STARTERS: { title: string; blurb: string }[] = [
  { title: 'Customer-support triage', blurb: 'Classify tickets, draft replies, escalate.' },
  { title: 'Daily research digest',   blurb: 'Summarize sources, email the team.' },
  { title: 'SQL analyst',             blurb: 'Translate questions to SQL, explain.' },
];

// Sample agent table shown on Review while the user has no real generation.
export const SAMPLE_AGENTS = [
  {
    role: 'researcher',
    goal: 'Find recent arXiv papers on agent orchestration',
    tools: ['web_search', 'pdf_reader'],
  },
  {
    role: 'summarizer',
    goal: 'Reduce each paper to 3 bullet points',
    tools: ['pdf_reader'],
  },
  {
    role: 'writer',
    goal: 'Compose digest, send via email',
    tools: ['email_send'],
  },
];

// File preview tree — neutral package by default.
export interface TreeNode {
  type: 'd' | 'f';
  name: string;
  depth: number;
  open?: boolean;
  selected?: boolean;
  locked?: boolean;
  diff?: '+' | '-';
  badge?: 'hp';
}

export const NEUTRAL_TREE: TreeNode[] = [
  { type: 'd', name: 'arxiv-digest',         depth: 0, open: true },
  { type: 'd', name: 'agents',               depth: 1, open: true },
  { type: 'f', name: 'researcher.py',        depth: 2, selected: true },
  { type: 'f', name: 'summarizer.py',        depth: 2 },
  { type: 'f', name: 'writer.py',            depth: 2 },
  { type: 'd', name: 'tasks',                depth: 1 },
  { type: 'd', name: 'tools',                depth: 1, open: true },
  { type: 'f', name: 'web_search.py',        depth: 2 },
  { type: 'f', name: 'pdf_reader.py',        depth: 2 },
  { type: 'f', name: 'email_send.py',        depth: 2, locked: true },
  { type: 'd', name: 'tests',                depth: 1, open: true },
  { type: 'f', name: 'test_crew.py',         depth: 2 },
  { type: 'f', name: 'test_dry_run.py',      depth: 2 },
  { type: 'f', name: 'crew.py',              depth: 1 },
  { type: 'f', name: 'agent.manifest.json',  depth: 1 },
  { type: 'f', name: 'pyproject.toml',       depth: 1 },
  { type: 'f', name: 'Dockerfile',           depth: 1 },
  { type: 'f', name: 'README.md',            depth: 1 },
  { type: 'f', name: '.env.template',        depth: 1 },
];

export const HP_DIFF_TREE: TreeNode[] = [
  ...NEUTRAL_TREE.map((n) => ({ ...n, selected: false })),
  { type: 'f', name: 'homepilot.agent.json',         depth: 1, badge: 'hp', diff: '+' },
  { type: 'f', name: 'mcp-catalog.yml',              depth: 1, badge: 'hp', diff: '+' },
  { type: 'f', name: 'docker-compose.homepilot.yml', depth: 1, badge: 'hp', diff: '+' },
];
HP_DIFF_TREE[2].selected = true;

export const SAMPLE_FILE_BODY = `from crewai import Agent, Task
from tools import web_search, pdf_reader
from .base import settings

# ── researcher ───────────────────────────────────────────────
# Finds recent arXiv papers on agent orchestration,
# scoped to the last 7 days, deduplicated by DOI.

researcher = Agent(
    role="researcher",
    goal="Find recent arXiv papers on agent orchestration",
    backstory="A rigorous, terse analyst who cites sources.",
    tools=[web_search, pdf_reader],
    llm=settings.llm,
    allow_delegation=False,
    max_iter=8,
    memory=settings.memory,
)

def task() -> Task:
    return Task(
        description=(
            "Search arXiv for papers from the last 7 days that "
            "match: 'multi-agent orchestration' OR 'agent crew'. "
            "Return the top 5 by relevance."
        ),
        expected_output=(
            "List[Paper] — title, authors, abstract, "
            "arxiv_id, published_at."
        ),
        agent=researcher,
        async_execution=False,
    )`;

// Permission rows + modes (Step 4)
export type PermStatus = 'ok' | 'warn' | 'no';

export interface PermRow {
  status: PermStatus;
  label: string;
  note: string;
}

export const PERM_ROWS: PermRow[] = [
  { status: 'ok',   label: 'Read PDFs',              note: 'pdf_reader' },
  { status: 'ok',   label: 'Search the web',         note: 'web_search · 5 req/min' },
  { status: 'ok',   label: 'Write local files',      note: './out only' },
  { status: 'warn', label: 'Send emails',            note: 'requires SMTP_API_KEY · approval required' },
  { status: 'warn', label: 'Query databases',        note: 'sql_query · read-only' },
  { status: 'no',   label: 'Execute shell commands', note: 'shell_exec · disabled in safe mode' },
];

export type PermissionMode = 'safe' | 'dev' | 'ask';

export const PERM_MODES: { id: PermissionMode; label: string; blurb: string }[] = [
  { id: 'safe', label: 'Safe',              blurb: 'No shell, no email, no external writes.' },
  { id: 'dev',  label: 'Developer',         blurb: 'Local files + tests. Network read.' },
  { id: 'ask',  label: 'Ask before acting', blurb: 'Approve risky actions per call.' },
];

// LLM provider segmented control
export const LLM_PROVIDERS = ['anthropic', 'openai', 'watsonx', 'ollabridge', 'ollama'] as const;
export type LlmProvider = (typeof LLM_PROVIDERS)[number];

// Output checklist (right column on Review)
export const OUTPUT_CHECKLIST: { label: string; value: string }[] = [
  { label: 'Language', value: 'Python 3.11' },
  { label: 'Tests',    value: '8 unit · 2 integration' },
  { label: 'Linting',  value: 'ruff + mypy' },
  { label: 'Docker',   value: 'multi-stage' },
];
