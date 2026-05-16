import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { StagePillBadge } from '@/components/primitives/Pill';
import { PERM_MODES, PERM_ROWS, type PermissionMode } from '@/lib/wizard-data';

interface Props {
  mode: PermissionMode;
  onChange?: (mode: PermissionMode) => void;
}

export function PermissionCard({ mode, onChange }: Props) {
  const colorFor = (s: 'ok' | 'warn' | 'no') =>
    s === 'ok' ? tokens.ok : s === 'warn' ? tokens.warn : tokens.err;
  const glyphFor = (s: 'ok' | 'warn' | 'no') => (s === 'ok' ? '✓' : s === 'warn' ? '⚠' : '✕');

  return (
    <div style={{ border: `1px solid ${tokens.border}`, background: '#fff' }}>
      <div
        style={{
          padding: '10px 14px',
          borderBottom: `1px solid ${tokens.border}`,
          display: 'flex',
          alignItems: 'center',
          gap: 8,
        }}
      >
        <Icon name="cog" size={13} stroke={tokens.ink2} />
        <span className="ag-cap" style={{ flex: 1 }}>Permissions</span>
        <StagePillBadge stage="core" />
      </div>

      <div
        role="radiogroup"
        style={{
          padding: 10,
          borderBottom: `1px solid ${tokens.border}`,
          display: 'flex',
          gap: 6,
        }}
      >
        {PERM_MODES.map((m) => {
          const on = m.id === mode;
          return (
            <button
              key={m.id}
              type="button"
              role="radio"
              aria-checked={on}
              onClick={() => onChange?.(m.id)}
              style={{
                flex: 1,
                padding: 10,
                border: `1px solid ${on ? tokens.ink : tokens.border}`,
                background: on ? tokens.surface : '#fff',
                textAlign: 'left',
                cursor: 'pointer',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span
                  style={{
                    width: 12,
                    height: 12,
                    borderRadius: '50%',
                    border: `1px solid ${on ? tokens.ink : tokens.borderStrong}`,
                    background: on ? tokens.ink : '#fff',
                    position: 'relative',
                  }}
                >
                  {on && (
                    <span
                      style={{
                        position: 'absolute',
                        inset: 3,
                        background: '#fff',
                        borderRadius: '50%',
                      }}
                    />
                  )}
                </span>
                <span style={{ fontSize: 12.5, fontWeight: 500 }}>{m.label}</span>
              </div>
              <div
                className="ag-small"
                style={{
                  marginTop: 4,
                  fontSize: 11,
                  color: tokens.muted,
                  lineHeight: 1.4,
                }}
              >
                {m.blurb}
              </div>
            </button>
          );
        })}
      </div>

      {PERM_ROWS.map((p, i) => (
        <div
          key={p.label}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            padding: '9px 14px',
            borderBottom: i < PERM_ROWS.length - 1 ? `1px solid ${tokens.border}` : 'none',
          }}
        >
          <span
            style={{
              width: 14,
              textAlign: 'center',
              color: colorFor(p.status),
              fontFamily: tokens.mono,
              fontSize: 13,
              fontWeight: 600,
            }}
          >
            {glyphFor(p.status)}
          </span>
          <span style={{ fontSize: 13, color: tokens.ink }}>{p.label}</span>
          <span style={{ flex: 1 }} />
          <span className="ag-mono" style={{ fontSize: 11, color: tokens.muted }}>{p.note}</span>
        </div>
      ))}
    </div>
  );
}
