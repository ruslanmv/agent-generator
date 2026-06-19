// Batch 8 — derive the pipeline graph from a real ProjectSpec.
//
// The visual editor used to seed from a hard-coded fixture. Now, when the Pipeline page
// is opened against a project (`/pipeline?project={id}`), we fetch the project and build
// the node/edge graph from its spec: one node per agent, per tool, the configured model,
// plus input/output terminals. With no project (or an unreadable one) we fall open to the
// bundled seed so the editor still demonstrates the interaction.

import {
  INITIAL_EDGES,
  INITIAL_NODES,
  type PipelineNode,
} from './pipeline-data';

// Loose shapes — the demo store returns the raw ProjectSpec dump and the full backend
// returns ProjectOut; both carry the same `spec` fields we read here.
interface RawAgent {
  id?: string;
  role?: string;
  goal?: string;
  backstory?: string;
  tools?: string[];
  llm_override?: string | null;
}
interface RawTool {
  id?: string;
  template?: string;
}
interface RawSpec {
  name?: string;
  description?: string;
  framework?: string;
  llm?: { provider?: string; model?: string };
  agents?: RawAgent[];
  tools?: RawTool[];
}
export interface RawProject {
  prompt?: string;
  spec?: RawSpec;
}

export interface DerivedPipeline {
  nodes: PipelineNode[];
  edges: [string, string][];
  /** 'backend' once derived from a real spec; 'seed' for the bundled fixture. */
  source: 'backend' | 'seed';
}

const COL = { input: 40, agent: 260, tool: 480, llm: 700, output: 900 };
const ROW_H = 96;

function centerY(rows: number): number {
  return 60 + (Math.max(rows, 1) - 1) * (ROW_H / 2);
}

export function derivePipeline(project: RawProject | null | undefined): DerivedPipeline {
  const spec = project?.spec;
  const agents = spec?.agents ?? [];
  if (!spec || agents.length === 0) {
    return { nodes: INITIAL_NODES, edges: INITIAL_EDGES, source: 'seed' };
  }

  const nodes: PipelineNode[] = [];
  const edges: [string, string][] = [];

  // Tools — declared in spec.tools, indexed by id for `template` sub-labels.
  const toolTemplate = new Map<string, string>();
  for (const t of spec.tools ?? []) {
    if (t.id) toolTemplate.set(t.id, t.template ?? 'tool');
  }
  // Any tool referenced by an agent but not declared still gets a node.
  const toolIds: string[] = [];
  for (const a of agents) {
    for (const tid of a.tools ?? []) {
      if (!toolIds.includes(tid)) toolIds.push(tid);
    }
  }
  for (const tid of toolTemplate.keys()) {
    if (!toolIds.includes(tid)) toolIds.push(tid);
  }

  const model = spec.llm?.model ?? 'model';
  const provider = spec.llm?.provider ?? 'provider';

  // Terminals + model centred against the tallest column.
  const tallest = Math.max(agents.length, toolIds.length, 1);
  const midY = centerY(tallest);

  nodes.push({ id: 'in', kind: 'input', x: COL.input, y: midY, label: 'User prompt', sub: 'string' });

  agents.forEach((a, i) => {
    const nodeId = `a-${a.id ?? i}`;
    nodes.push({
      id: nodeId,
      kind: 'agent',
      x: COL.agent,
      y: 60 + i * ROW_H,
      label: a.role ?? a.id ?? `agent ${i + 1}`,
      sub: a.goal ? a.goal.slice(0, 28) : 'agent',
      goal: a.goal ?? '',
      backstory: a.backstory ?? '',
      llm: a.llm_override ?? model,
      maxIter: 5,
      tools: a.tools ?? [],
    });
    edges.push(['in', nodeId]);
    edges.push([nodeId, 'llm']);
    for (const tid of a.tools ?? []) {
      edges.push([nodeId, `t-${tid}`]);
    }
  });

  toolIds.forEach((tid, j) => {
    nodes.push({
      id: `t-${tid}`,
      kind: 'tool',
      x: COL.tool,
      y: 60 + j * ROW_H,
      label: tid,
      sub: toolTemplate.get(tid) ?? 'tool',
    });
  });

  nodes.push({ id: 'llm', kind: 'llm', x: COL.llm, y: midY, label: model, sub: provider });

  const outLabel = spec.name ? `${spec.name}` : 'output';
  nodes.push({
    id: 'out',
    kind: 'output',
    x: COL.output,
    y: midY,
    label: outLabel,
    sub: spec.framework ?? 'bundle',
  });
  edges.push(['llm', 'out']);

  return { nodes, edges, source: 'backend' };
}
