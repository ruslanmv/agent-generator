// Safety — decision-focused page. Mode picker (Safe / Developer /
// Ask) at the top, capabilities × status × requirement table below.

import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { Button } from '@/components/primitives/Button';
import type { PermissionMode } from '@/lib/wizard-data';
import { useWizard } from '../state';
import { ReviewShell } from './ReviewShell';
import { useReviewSub } from './state';

interface ModeOption {
  id: PermissionMode;
  label: string;
  description: string;
}

const MODES: ModeOption[] = [
  { id: 'safe', label: 'Safe mode', description: 'No shell, no email, no external writes.' },
  { id: 'dev', label: 'Developer mode', description: 'Local files + tests. Network read.' },
  { id: 'ask', label: 'Ask before acting', description: 'Approve risky actions per call.' },
];

interface CapabilityRow {
  label: string;
  status: 'allowed' | 'approval' | 'limited' | 'blocked';
  requirement: string;
}

const CAPS: CapabilityRow[] = [
  { label: 'Read PDFs', status: 'allowed', requirement: 'pdf_reader' },
  { label: 'Search the web', status: 'allowed', requirement: 'web_search · 5 req/min' },
  { label: 'Write local files', status: 'allowed', requirement: './out only' },
  {
    label: 'Send emails',
    status: 'approval',
    requirement: 'requires SMTP_API_KEY · approval required',
  },
  { label: 'Query databases', status: 'limited', requirement: 'sql_query · read-only' },
  {
    label: 'Execute shell commands',
    status: 'blocked',
    requirement: 'shell_exec · disabled in safe mode',
  },
];

function statusMeta(s: CapabilityRow['status']) {
  switch (s) {
    case 'allowed':
      return { color: tokens.ok, icon: '✓', label: 'Allowed' };
    case 'approval':
      return { color: tokens.warn, icon: '⚠', label: 'Needs approval' };
    case 'limited':
      return { color: tokens.warn, icon: '⚠', label: 'Limited' };
    case 'blocked':
      return { color: tokens.err, icon: '✕', label: 'Blocked' };
  }
}

export function ReviewSafety() {
  const { state, actions } = useWizard();
  const { go } = useReviewSub();
  const summary = CAPS.reduce(
    (acc, c) => {
      if (c.status === 'allowed') acc.allowed += 1;
      else if (c.status === 'approval') acc.approval += 1;
      return acc;
    },
    { allowed: 0, approval: 0 },
  );

  return (
    <ReviewShell
      title="Safety review"
      subtitle="Choose how much autonomy the agent gets, then review what it can and can't do."
      footer={
        <>
          <Button variant="ghost" onClick={() => go('files')}>
            <Icon name="arrow-l" size={13} /> Files
          </Button>
          <span style={{ flex: 1 }} />
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 4,
              padding: '2px 8px',
              fontSize: 11,
              fontFamily: tokens.mono,
              color: tokens.ok,
              background: '#fff',
              border: `1px solid ${tokens.ok}`,
            }}
          >
            <Icon name="check" size={9} stroke={tokens.ok} /> {summary.allowed} allowed ·{' '}
            {summary.approval} need approval
          </span>
          <Button variant="primary" onClick={() => go('generate')}>
            Generate <Icon name="arrow" size={13} stroke="#fff" />
          </Button>
        </>
      }
    >
      {/* Mode picker */}
      <div className="ag-cap" style={{ marginBottom: 10 }}>
        Mode
      </div>
      <div
        role="radiogroup"
        aria-label="Permission mode"
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: 10,
          marginBottom: 24,
        }}
      >
        {MODES.map((m) => {
          const sel = m.id === state.permissionMode;
          return (
            <button
              key={m.id}
              type="button"
              role="radio"
              aria-checked={sel}
              onClick={() => actions.set('permissionMode', m.id)}
              style={{
                padding: 16,
                border: `${sel ? 2 : 1}px solid ${sel ? tokens.ink : tokens.border}`,
                background: sel ? tokens.surface : '#fff',
                cursor: 'pointer',
                textAlign: 'left',
                fontFamily: 'inherit',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                <span
                  aria-hidden
                  style={{
                    width: 14,
                    height: 14,
                    borderRadius: '50%',
                    border: `1px solid ${sel ? tokens.ink : tokens.borderStrong}`,
                    background: sel ? tokens.ink : '#fff',
                    position: 'relative',
                    flexShrink: 0,
                  }}
                >
                  {sel && (
                    <span
                      style={{
                        position: 'absolute',
                        inset: 4,
                        background: '#fff',
                        borderRadius: '50%',
                      }}
                    />
                  )}
                </span>
                <span style={{ fontSize: 14, fontWeight: 500 }}>{m.label}</span>
              </div>
              <p className="ag-small" style={{ margin: 0, color: tokens.ink2 }}>
                {m.description}
              </p>
            </button>
          );
        })}
      </div>

      {/* Capabilities table */}
      <div className="ag-cap" style={{ marginBottom: 10 }}>
        Capabilities
      </div>
      <div style={{ border: `1px solid ${tokens.border}`, background: '#fff' }}>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1.4fr 1fr 1.6fr',
            padding: '10px 18px',
            borderBottom: `1px solid ${tokens.border}`,
            background: tokens.surface,
            fontSize: 11,
            color: tokens.muted,
            letterSpacing: '.04em',
            textTransform: 'uppercase',
          }}
        >
          <span>Capability</span>
          <span>Status</span>
          <span>Requirement</span>
        </div>
        {CAPS.map((c, i) => {
          const m = statusMeta(c.status);
          return (
            <div
              key={c.label}
              style={{
                display: 'grid',
                gridTemplateColumns: '1.4fr 1fr 1.6fr',
                padding: '13px 18px',
                alignItems: 'center',
                borderBottom: i < CAPS.length - 1 ? `1px solid ${tokens.border}` : 0,
              }}
            >
              <span style={{ fontSize: 13.5, color: tokens.ink }}>{c.label}</span>
              <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span
                  aria-hidden
                  style={{
                    width: 14,
                    textAlign: 'center',
                    fontFamily: tokens.mono,
                    fontWeight: 600,
                    color: m.color,
                  }}
                >
                  {m.icon}
                </span>
                <span style={{ fontSize: 13, color: m.color, fontWeight: 500 }}>
                  {m.label}
                </span>
              </span>
              <span className="ag-mono ag-small" style={{ color: tokens.muted }}>
                {c.requirement}
              </span>
            </div>
          );
        })}
      </div>

      <p className="ag-small" style={{ color: tokens.muted, marginTop: 14 }}>
        Mode applies on generation <b>and</b> on every runtime adapter (HomePilot, Docker,
        watsonx). You can flip modes per environment in{' '}
        <span className="ag-mono">.env.&lt;profile&gt;</span>.
      </p>
    </ReviewShell>
  );
}
