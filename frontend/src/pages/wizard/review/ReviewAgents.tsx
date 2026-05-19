// Agents — one card per agent. Replaces the dense table in the
// legacy Review screen with role/goal/backstory/tools + per-card
// actions (Edit, Tools, Duplicate, Delete) and a topology hint at the
// bottom linking to the pipeline editor.

import { useNavigate } from 'react-router-dom';
import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { Button } from '@/components/primitives/Button';
import { Pill } from '@/components/primitives/Pill';
import { SAMPLE_AGENTS } from '@/lib/wizard-data';
import { ReviewShell } from './ReviewShell';
import { useReviewSub } from './state';

// Top-bar accent per agent. Cycles through the cobalt accent and two
// supplementary brand-safe colours from the design.
const AGENT_COLORS = [tokens.accent, '#0e6027', '#7c3aed'] as const;
const AGENT_ACTIONS = ['Edit', 'Tools', 'Duplicate', 'Delete'] as const;

export function ReviewAgents() {
  const { go } = useReviewSub();
  const navigate = useNavigate();
  const agents = SAMPLE_AGENTS;

  return (
    <ReviewShell
      title="Agents"
      subtitle={`${agents.length} specialised agents working in sequence. Edit roles, goals, and tool access per card.`}
      footer={
        <>
          <Button variant="ghost" onClick={() => go('overview')}>
            <Icon name="arrow-l" size={13} /> Overview
          </Button>
          <span style={{ flex: 1 }} />
          <Button variant="ghost">
            <Icon name="plus" size={13} /> Add agent
          </Button>
          <Button variant="primary" onClick={() => go('config')}>
            Configuration <Icon name="arrow" size={13} stroke="#fff" />
          </Button>
        </>
      }
    >
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
        {agents.map((a, i) => {
          const color = AGENT_COLORS[i % AGENT_COLORS.length];
          return (
            <div
              key={a.role}
              style={{ border: `1px solid ${tokens.border}`, background: '#fff' }}
            >
              <div aria-hidden style={{ height: 4, background: color }} />
              <div style={{ padding: 18 }}>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    marginBottom: 12,
                  }}
                >
                  <Icon name="agent" size={16} stroke={color} />
                  <span className="ag-mono" style={{ fontSize: 15, fontWeight: 600 }}>
                    {a.role}
                  </span>
                  <span style={{ flex: 1 }} />
                  <span className="ag-mono ag-small" style={{ color: tokens.muted }}>
                    {i + 1}/{agents.length}
                  </span>
                </div>

                <div className="ag-cap" style={{ marginBottom: 6 }}>
                  Goal
                </div>
                <p
                  className="ag-body"
                  style={{ margin: '0 0 14px', fontSize: 13, color: tokens.ink }}
                >
                  {a.goal}
                </p>

                <div className="ag-cap" style={{ marginBottom: 6 }}>
                  Tools · {a.tools.length}
                </div>
                <div
                  style={{
                    display: 'flex',
                    flexWrap: 'wrap',
                    gap: 4,
                    marginBottom: 14,
                  }}
                >
                  {a.tools.map((t) => (
                    <Pill key={t}>{t}</Pill>
                  ))}
                </div>

                <div
                  style={{
                    display: 'flex',
                    gap: 18,
                    paddingTop: 12,
                    borderTop: `1px solid ${tokens.border}`,
                  }}
                >
                  <div>
                    <div className="ag-cap" style={{ fontSize: 10 }}>
                      Max iter
                    </div>
                    <div className="ag-mono" style={{ fontSize: 13 }}>
                      8
                    </div>
                  </div>
                  <div>
                    <div className="ag-cap" style={{ fontSize: 10 }}>
                      Memory
                    </div>
                    <div className="ag-mono" style={{ fontSize: 13 }}>
                      vector
                    </div>
                  </div>
                </div>
              </div>

              <div
                role="group"
                aria-label={`Actions for ${a.role}`}
                style={{
                  display: 'flex',
                  borderTop: `1px solid ${tokens.border}`,
                  background: tokens.surface,
                }}
              >
                {AGENT_ACTIONS.map((act, j) => (
                  <button
                    key={act}
                    type="button"
                    title="Inline agent editing lands in the next wizard iteration."
                    style={{
                      flex: 1,
                      padding: '10px 8px',
                      textAlign: 'center',
                      fontSize: 12,
                      fontFamily: tokens.mono,
                      color: act === 'Delete' ? tokens.err : tokens.ink2,
                      borderTop: 'none',
                      borderLeft: 'none',
                      borderBottom: 'none',
                      borderRight:
                        j < AGENT_ACTIONS.length - 1 ? `1px solid ${tokens.border}` : 0,
                      background: 'transparent',
                      cursor: 'not-allowed',
                      opacity: 0.6,
                    }}
                  >
                    {act}
                  </button>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {/* Topology hint */}
      <div
        style={{
          marginTop: 20,
          padding: 16,
          background: tokens.surface,
          border: `1px solid ${tokens.border}`,
          display: 'flex',
          alignItems: 'center',
          gap: 14,
        }}
      >
        <Icon name="flow" size={16} stroke={tokens.ink2} />
        <span style={{ fontSize: 13, color: tokens.ink2 }}>
          Pattern: <b>supervisor</b> · {agents.map((a) => a.role).join(' → ')} (sequential)
        </span>
        <span style={{ flex: 1 }} />
        <button
          type="button"
          onClick={() => navigate('/pipeline')}
          className="ag-mono ag-small"
          style={{
            color: tokens.accent,
            background: 'transparent',
            border: 'none',
            cursor: 'pointer',
            fontFamily: tokens.mono,
          }}
        >
          Open in pipeline editor →
        </button>
      </div>
    </ReviewShell>
  );
}
