// Sample data for the live Run console — agent activity, streaming events,
// trace tree. Kept here so the page components can stay pure presentation
// and be wired to real telemetry later without changing prop shapes.

export type AgentRunStatus = 'idle' | 'queued' | 'running' | 'done' | 'failed';

export interface AgentRow {
  role: string;
  status: AgentRunStatus;
  progress: number;
  tokens: number;
}

export const AGENT_ROWS: AgentRow[] = [
  { role: 'researcher', status: 'done',    progress: 100, tokens: 4820 },
  { role: 'summarizer', status: 'running', progress: 64,  tokens: 2104 },
  { role: 'writer',     status: 'queued',  progress: 0,   tokens: 0    },
];

export type EventKind = 'sys' | 'thought' | 'tool' | 'result' | 'msg';

export interface RunEvent {
  ts: string;
  actor: string;
  kind: EventKind;
  message: string;
}

export const RUN_EVENTS: RunEvent[] = [
  { ts: '00.0', actor: 'system',     kind: 'sys',     message: 'crew.kickoff() · inputs={topic: "agent orchestration"}' },
  { ts: '00.4', actor: 'researcher', kind: 'thought', message: 'thinking …' },
  { ts: '01.2', actor: 'researcher', kind: 'tool',    message: 'tool web_search(query="agent orchestration arXiv 2026")' },
  { ts: '03.7', actor: 'web_search', kind: 'result',  message: '12 results · top 5 retained' },
  { ts: '04.0', actor: 'researcher', kind: 'tool',    message: 'tool pdf_reader(url="arxiv.org/abs/2604.01928")' },
  { ts: '06.2', actor: 'pdf_reader', kind: 'result',  message: '4,120 tokens extracted' },
  { ts: '08.1', actor: 'summarizer', kind: 'thought', message: 'thinking …' },
  { ts: '09.6', actor: 'summarizer', kind: 'msg',     message: 'output: "• graph-based handoff …"' },
  { ts: '12.0', actor: 'writer',     kind: 'tool',    message: 'tool email_send(to="team@…", subject="Agent digest …")' },
  { ts: '13.4', actor: 'email_send', kind: 'result',  message: 'sent · message_id=m-8e2c' },
];

export const RUN_FILTERS = ['All', 'Thoughts', 'Tools', 'Messages'] as const;
export type RunFilter = (typeof RUN_FILTERS)[number];

export type TraceStatus = 'queued' | 'running' | 'done' | 'failed';

export interface TraceRow {
  depth: number;
  label: string;
  duration: string;
  status: TraceStatus;
}

export const TRACE_ROWS: TraceRow[] = [
  { depth: 0, label: 'crew.kickoff',     duration: '13.4s', status: 'running' },
  { depth: 1, label: 'task: research',   duration: '7.1s',  status: 'done' },
  { depth: 2, label: 'web_search',       duration: '2.4s',  status: 'done' },
  { depth: 2, label: 'pdf_reader · ×3',  duration: '4.0s',  status: 'done' },
  { depth: 1, label: 'task: summarize',  duration: '5.3s',  status: 'running' },
  { depth: 2, label: 'pdf_reader',       duration: '2.1s',  status: 'done' },
  { depth: 2, label: 'llm.call',         duration: '3.0s',  status: 'running' },
  { depth: 1, label: 'task: write',      duration: '—',     status: 'queued' },
];

export const RUN_MODEL = { id: 'claude-opus-4', costPer1k: 0.025 };
