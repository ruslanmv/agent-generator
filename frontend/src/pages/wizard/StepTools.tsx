import { useMemo, useState } from 'react';
import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { Button } from '@/components/primitives/Button';
import { Pill } from '@/components/primitives/Pill';
import { Checkbox } from '@/components/primitives/Input';
import { Nav } from '@/components/primitives/Nav';
import { useWizard } from './state';
import { TOOLS, TOOL_CATEGORIES, type Tool } from '@/lib/wizard-data';

export function StepTools() {
  const { state, actions, setStep } = useWizard();
  const [cat, setCat] = useState<'All' | (typeof TOOL_CATEGORIES)[number]>('All');
  const [q, setQ] = useState('');

  const filtered = useMemo(
    () =>
      TOOLS.filter(
        (t) =>
          (cat === 'All' || t.cat === cat) &&
          t.name.toLowerCase().includes(q.toLowerCase()),
      ),
    [cat, q],
  );

  const navItems = [
    { id: 'All', label: 'All', count: TOOLS.length },
    ...TOOL_CATEGORIES.map((c) => ({
      id: c,
      label: c,
      count: TOOLS.filter((t) => t.cat === c).length,
    })),
  ];

  return (
    <div style={{ padding: '40px 80px', maxWidth: 1240, margin: '0 auto' }}>
      <div className="ag-eyebrow" style={{ marginBottom: 12 }}>STEP 3 / 4 · TOOLS</div>
      <h2 className="ag-h2" style={{ marginBottom: 8 }}>Pick the tools your agents can call.</h2>
      <p className="ag-body" style={{ marginBottom: 24, color: tokens.ink3 }}>
        Selected tools become typed Python functions in <span className="ag-mono">tools/</span>.
        Beta tools require provider keys you&rsquo;ll set in <b>Settings</b>.
      </p>

      <div style={{ display: 'flex', gap: 24, alignItems: 'flex-start' }}>
        <div style={{ width: 200, flexShrink: 0 }}>
          <div className="ag-cap" style={{ marginBottom: 10 }}>Category</div>
          <Nav vertical dense items={navItems} value={cat} onChange={(id) => setCat(id as typeof cat)} />
        </div>

        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
            <div
              style={{
                flex: 1,
                height: 36,
                border: `1px solid ${tokens.border}`,
                display: 'flex',
                alignItems: 'center',
                padding: '0 12px',
                gap: 8,
                background: '#fff',
              }}
            >
              <Icon name="search" size={14} stroke={tokens.muted} />
              <input
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Search tools…"
                style={{
                  flex: 1,
                  border: 0,
                  outline: 0,
                  background: 'transparent',
                  font: `14px ${tokens.sans}`,
                  color: tokens.ink,
                }}
              />
              <span className="ag-mono" style={{ fontSize: 11, color: tokens.faint }}>
                {filtered.length}
              </span>
            </div>
            <Button variant="ghost" size="sm">
              <Icon name="cube" size={13} /> Browse Matrix Hub
            </Button>
            <Button variant="ghost" size="sm">
              <Icon name="plus" size={13} /> Custom tool
            </Button>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 8 }}>
            {filtered.map((t) => (
              <ToolCard
                key={t.id}
                tool={t}
                selected={state.tools.includes(t.id)}
                onToggle={() => actions.toggleTool(t.id)}
              />
            ))}
          </div>
        </div>

        <div style={{ width: 260, flexShrink: 0 }}>
          <div style={{ position: 'sticky', top: 0 }}>
            <div className="ag-cap" style={{ marginBottom: 10 }}>
              Selected · {state.tools.length}
            </div>
            <div style={{ border: `1px solid ${tokens.border}`, background: '#fff' }}>
              {state.tools.length === 0 && (
                <div className="ag-small" style={{ padding: 16, color: tokens.faint }}>
                  None yet — pick at least one tool.
                </div>
              )}
              {state.tools.map((id) => {
                const t = TOOLS.find((x) => x.id === id);
                if (!t) return null;
                return (
                  <div
                    key={id}
                    style={{
                      padding: '8px 12px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                      borderBottom: `1px solid ${tokens.border}`,
                    }}
                  >
                    <Icon name="dot" size={10} stroke={tokens.accent} />
                    <span className="ag-mono" style={{ fontSize: 12 }}>{t.name}</span>
                    <span style={{ flex: 1 }} />
                    <button
                      type="button"
                      aria-label={`Remove ${t.name}`}
                      onClick={() => actions.toggleTool(id)}
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: tokens.muted,
                        cursor: 'pointer',
                        padding: 0,
                      }}
                    >
                      <Icon name="x" size={11} />
                    </button>
                  </div>
                );
              })}
            </div>
            <div className="ag-small" style={{ marginTop: 10, color: tokens.muted }}>
              Tools are wired into the generated <span className="ag-mono">crew.py</span> and exposed
              to every agent.
            </div>
          </div>
        </div>
      </div>

      <div style={{ marginTop: 32, display: 'flex', alignItems: 'center' }}>
        <Button variant="ghost" onClick={() => setStep(1)}>
          <Icon name="arrow-l" size={13} /> Back
        </Button>
        <span style={{ flex: 1 }} />
        <Button variant="primary" onClick={() => setStep(3)}>
          Review project <Icon name="arrow" size={13} stroke="#fff" />
        </Button>
      </div>
    </div>
  );
}

interface ToolCardProps {
  tool: Tool;
  selected: boolean;
  onToggle: () => void;
}

function ToolCard({ tool, selected, onToggle }: ToolCardProps) {
  return (
    <button
      type="button"
      onClick={onToggle}
      aria-pressed={selected}
      style={{
        padding: '12px 14px',
        border: `1px solid ${selected ? tokens.ink : tokens.border}`,
        background: selected ? tokens.surface : '#fff',
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        cursor: 'pointer',
        textAlign: 'left',
        fontFamily: 'inherit',
      }}
    >
      <Checkbox checked={selected} />
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span
            className="ag-mono"
            style={{ fontSize: 13, color: tokens.ink, fontWeight: 500 }}
          >
            {tool.name}
          </span>
          {tool.beta && <Pill variant="warn">beta</Pill>}
        </div>
        <div className="ag-small" style={{ marginTop: 2 }}>{tool.cat}</div>
      </div>
      <Icon name="tool" size={14} stroke={tokens.muted} />
    </button>
  );
}
