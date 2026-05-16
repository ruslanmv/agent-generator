// Orchestration Pattern card — Supervisor / ReAct picker.
// Renders the per-framework support glyph and trade-off axes.

import { tokens } from '@/styles/tokens';
import {
  ORCHESTRATION_PATTERNS,
  PATTERN_BY_FW,
  type OrchestrationPatternId,
} from '@/lib/orchestration';
import type { FrameworkId } from '@/lib/frameworks';

interface Props {
  framework: FrameworkId;
  value: OrchestrationPatternId;
  onChange: (id: OrchestrationPatternId) => void;
}

const SUPPORT_LABEL = {
  native: 'native',
  adapter: 'via adapter',
  unsupported: 'unsupported',
} as const;

export function PatternCard({ framework, value, onChange }: Props) {
  return (
    <div
      style={{
        border: `1px solid ${tokens.border}`,
        background: '#fff',
      }}
    >
      <div
        style={{
          padding: '10px 16px',
          borderBottom: `1px solid ${tokens.border}`,
          background: tokens.surface,
        }}
      >
        <div className="ag-cap">ORCHESTRATION PATTERN</div>
      </div>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
        }}
      >
        {ORCHESTRATION_PATTERNS.map((p, i) => {
          const support = PATTERN_BY_FW[framework]?.[p.id] ?? 'unsupported';
          const disabled = support === 'unsupported';
          const active = value === p.id && !disabled;
          return (
            <button
              key={p.id}
              type="button"
              disabled={disabled}
              onClick={() => onChange(p.id)}
              aria-pressed={active}
              style={{
                padding: 16,
                background: active ? tokens.surface : '#fff',
                border: 'none',
                borderRight:
                  i === 0 ? `1px solid ${tokens.border}` : 'none',
                cursor: disabled ? 'not-allowed' : 'pointer',
                opacity: disabled ? 0.45 : 1,
                textAlign: 'left',
                fontFamily: 'inherit',
                position: 'relative',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  marginBottom: 8,
                }}
              >
                <span
                  style={{
                    fontSize: 28,
                    lineHeight: 1,
                    fontFamily:
                      'Iosevka, JetBrains Mono, IBM Plex Mono, monospace',
                    color: active ? tokens.ink : tokens.ink2,
                  }}
                >
                  {p.glyph}
                </span>
                <div style={{ flex: 1 }}>
                  <div className="ag-h4">{p.label}</div>
                  <div
                    className="ag-small"
                    style={{
                      color:
                        support === 'native'
                          ? tokens.accent
                          : support === 'adapter'
                            ? '#8a6d00'
                            : tokens.ink3,
                    }}
                  >
                    {SUPPORT_LABEL[support]}
                  </div>
                </div>
              </div>
              <p className="ag-small" style={{ color: tokens.ink2, marginBottom: 8 }}>
                {p.blurb}
              </p>
              <dl style={{ margin: 0, fontSize: 11, color: tokens.ink3 }}>
                <Row k="Flow" v={p.axes.flow} />
                <Row k="Comms" v={p.axes.communication} />
                <Row k="Flex / Pred / Cost" v={`${p.axes.flexibility} / ${p.axes.predictability} / ${p.axes.cost}`} />
              </dl>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div style={{ display: 'flex', gap: 8 }}>
      <dt style={{ width: 110, color: tokens.ink3 }}>{k}</dt>
      <dd style={{ margin: 0 }}>{v}</dd>
    </div>
  );
}
