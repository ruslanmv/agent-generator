import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { Button } from '@/components/primitives/Button';
import { Pill, StagePillBadge } from '@/components/primitives/Pill';
import { PUBLISH_SECONDARY, RUN_SUMMARY } from '@/lib/export-data';

interface Props {
  onPublish: () => void;
}

export function PublishCard({ onPublish }: Props) {
  return (
    <div>
      <div className="ag-cap" style={{ marginBottom: 10 }}>Publish · Share</div>

      <div
        style={{
          border: `2px solid ${tokens.ink}`,
          background: '#fff',
          padding: 18,
          marginBottom: 10,
          position: 'relative',
        }}
      >
        <span style={{ position: 'absolute', top: -10, left: 14 }}>
          <Pill variant="accent">recommended</Pill>
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
          <Icon name="cube" size={18} stroke={tokens.ink} />
          <h3 className="ag-h3" style={{ margin: 0, fontSize: 17 }}>MatrixHub Community</h3>
        </div>
        <div className="ag-small" style={{ color: tokens.ink3, marginBottom: 14 }}>
          Publish for anyone to discover, install, fork, and improve. Validation runs first —
          manifest, license, secret scan, permissions.
        </div>
        <Button
          variant="primary"
          onClick={onPublish}
          style={{ width: '100%', justifyContent: 'center' }}
        >
          <Icon name="send" size={13} stroke="#fff" /> Publish to MatrixHub
        </Button>
      </div>

      {PUBLISH_SECONDARY.map((p) => (
        <div
          key={p.id}
          style={{
            padding: '12px 14px',
            border: `1px solid ${tokens.border}`,
            background: '#fff',
            marginBottom: 6,
            display: 'flex',
            alignItems: 'center',
            gap: 12,
          }}
        >
          <Icon name={p.icon} size={14} stroke={tokens.ink2} />
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ fontSize: 13, fontWeight: 500 }}>{p.label}</span>
              {p.stage !== 'core' && <StagePillBadge stage={p.stage} />}
            </div>
            <div className="ag-mono" style={{ fontSize: 11, color: tokens.muted, marginTop: 2 }}>
              {p.sub}
            </div>
          </div>
          <Icon name="chev-r" size={13} stroke={tokens.muted} />
        </div>
      ))}

      <div className="ag-cap" style={{ margin: '24px 0 8px' }}>Run summary</div>
      <div style={{ border: `1px solid ${tokens.border}`, background: '#fff' }}>
        {RUN_SUMMARY.map((row, i) => (
          <div
            key={row.key}
            style={{
              display: 'flex',
              padding: '8px 14px',
              borderBottom: i < RUN_SUMMARY.length - 1 ? `1px solid ${tokens.border}` : 'none',
            }}
          >
            <span style={{ flex: 1, fontSize: 13, color: tokens.ink2 }}>{row.key}</span>
            <span
              className="ag-mono"
              style={{
                fontSize: 12,
                color:
                  row.color === 'ok'
                    ? tokens.ok
                    : row.color === 'warn'
                      ? tokens.warn
                      : row.color === 'err'
                        ? tokens.err
                        : tokens.ink,
                fontWeight: row.color ? 500 : 400,
              }}
            >
              {row.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
