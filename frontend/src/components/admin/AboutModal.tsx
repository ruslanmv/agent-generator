import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { Pill } from '@/components/primitives/Pill';
import { AgentGeneratorMark } from '@/components/icons/Logo';
import { ABOUT } from '@/lib/settings-data';

interface Props {
  onClose: () => void;
}

export function AboutModal({ onClose }: Props) {
  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="About agent-generator"
      onClick={onClose}
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(22,22,22,.45)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 60,
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          width: 520,
          background: '#fff',
          boxShadow: '0 30px 80px rgba(0,0,0,.3)',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            height: 48,
            borderBottom: `1px solid ${tokens.border}`,
            display: 'flex',
            alignItems: 'center',
            padding: '0 20px',
          }}
        >
          <h3 style={{ margin: 0, fontSize: 15, fontWeight: 500 }}>About</h3>
          <span style={{ flex: 1 }} />
          <button
            type="button"
            aria-label="Close"
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              padding: 4,
              cursor: 'pointer',
              color: tokens.muted,
            }}
          >
            <Icon name="x" size={14} />
          </button>
        </div>

        <div
          style={{
            padding: 28,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            textAlign: 'center',
            gap: 14,
          }}
        >
          <div
            style={{
              width: 64,
              height: 64,
              background: '#fff',
              border: `1px solid ${tokens.border}`,
              padding: 6,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <AgentGeneratorMark size={50} inverse />
          </div>
          <div>
            <div style={{ fontSize: 22, fontWeight: 500 }}>{ABOUT.name}</div>
            <div className="ag-mono ag-small" style={{ color: tokens.muted, marginTop: 2 }}>
              {ABOUT.version} · build {ABOUT.build} · {ABOUT.date}
            </div>
          </div>
          <p
            className="ag-body"
            style={{ color: tokens.ink2, maxWidth: 380, margin: 0, fontSize: 13.5 }}
          >
            {ABOUT.blurb}
          </p>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', justifyContent: 'center' }}>
            {ABOUT.pills.map((p) => (
              <Pill key={p}>{p}</Pill>
            ))}
            <Pill variant="ok">self-hosted</Pill>
          </div>
        </div>

        <div
          style={{
            padding: '14px 20px',
            background: tokens.surface,
            borderTop: `1px solid ${tokens.border}`,
            display: 'flex',
            gap: 16,
            fontSize: 12,
            alignItems: 'center',
          }}
        >
          {ABOUT.links.map((l) => (
            <a
              key={l}
              href="#"
              className="ag-mono"
              style={{ color: tokens.ink2 }}
              onClick={(e) => e.preventDefault()}
            >
              {l}
            </a>
          ))}
          <span style={{ flex: 1 }} />
          <span className="ag-mono" style={{ color: tokens.muted }}>{ABOUT.copyright}</span>
        </div>
      </div>
    </div>
  );
}
