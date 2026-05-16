import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { Button } from '@/components/primitives/Button';
import { NODE_META, type PipelineNode } from '@/lib/pipeline-data';

interface InspectorProps {
  node: PipelineNode | null;
  onRemoveTool?: (nodeId: string, tool: string) => void;
}

export function Inspector({ node, onRemoveTool }: InspectorProps) {
  return (
    <aside
      style={{
        width: 280,
        borderLeft: `1px solid ${tokens.border}`,
        padding: 16,
        overflow: 'auto',
        background: '#fff',
        flexShrink: 0,
      }}
    >
      {!node ? (
        <Empty />
      ) : node.kind === 'agent' ? (
        <AgentInspector node={node} onRemoveTool={onRemoveTool} />
      ) : (
        <GenericInspector node={node} />
      )}
    </aside>
  );
}

function Empty() {
  return (
    <div className="ag-small" style={{ color: tokens.muted, paddingTop: 24 }}>
      Select a node on the canvas to inspect it.
    </div>
  );
}

function GenericInspector({ node }: { node: PipelineNode }) {
  const meta = NODE_META[node.kind];
  return (
    <>
      <div className="ag-eyebrow" style={{ marginBottom: 6 }}>
        {meta.label.toUpperCase()}  ·  selected
      </div>
      <div className="ag-h3" style={{ marginBottom: 4 }}>{node.label}</div>
      <div className="ag-small" style={{ marginBottom: 18 }}>{node.sub}</div>
      <Field label="Kind" value={meta.label} mono />
      <Field label="ID" value={node.id} mono />
      <Field label="Position" value={`x=${node.x} y=${node.y}`} mono />
    </>
  );
}

function AgentInspector({ node, onRemoveTool }: { node: PipelineNode; onRemoveTool?: (id: string, t: string) => void }) {
  return (
    <>
      <div className="ag-eyebrow" style={{ marginBottom: 6 }}>AGENT  ·  selected</div>
      <div className="ag-h3" style={{ marginBottom: 4 }}>{node.label}</div>
      <div className="ag-small" style={{ marginBottom: 18 }}>{node.sub}</div>

      {node.goal && <Field label="Goal" value={node.goal} />}
      {node.backstory && <Field label="Backstory" value={node.backstory} />}
      {node.llm && <Field label="LLM" value={node.llm} mono />}
      {node.maxIter != null && <Field label="Max iterations" value={String(node.maxIter)} mono />}

      <div className="ag-cap" style={{ margin: '20px 0 8px' }}>Tools</div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {(node.tools ?? []).map((t) => (
          <div
            key={t}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '6px 8px',
              border: `1px solid ${tokens.border}`,
            }}
          >
            <Icon name="tool" size={12} stroke={tokens.muted} />
            <span className="ag-mono" style={{ fontSize: 12 }}>{t}</span>
            <span style={{ flex: 1 }} />
            <button
              type="button"
              aria-label={`Remove ${t}`}
              onClick={() => onRemoveTool?.(node.id, t)}
              style={{ background: 'transparent', border: 'none', cursor: 'pointer', padding: 0 }}
            >
              <Icon name="x" size={11} stroke={tokens.muted} />
            </button>
          </div>
        ))}
        <Button variant="ghost" size="sm" style={{ alignSelf: 'flex-start' }}>
          <Icon name="plus" size={12} /> Add tool
        </Button>
      </div>

      <div className="ag-cap" style={{ margin: '20px 0 8px' }}>Last test run</div>
      <div
        style={{
          background: tokens.termBg,
          color: tokens.termInk,
          fontFamily: tokens.mono,
          fontSize: 11,
          padding: 10,
          lineHeight: 1.5,
        }}
      >
        <div style={{ color: tokens.termDim }}>$ test {node.label}</div>
        <div style={{ color: tokens.termOk }}>✓ 3 bullets · 142 tokens</div>
        <div style={{ color: tokens.termDim }}>elapsed 1.4s</div>
      </div>
    </>
  );
}

function Field({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div style={{ marginBottom: 10 }}>
      <div className="ag-cap" style={{ marginBottom: 4 }}>{label}</div>
      <div
        style={{
          minHeight: 30,
          padding: '6px 10px',
          border: `1px solid ${tokens.border}`,
          display: 'flex',
          alignItems: 'center',
          fontSize: 13,
          fontFamily: mono ? tokens.mono : tokens.sans,
          color: tokens.ink2,
        }}
      >
        {value}
      </div>
    </div>
  );
}
