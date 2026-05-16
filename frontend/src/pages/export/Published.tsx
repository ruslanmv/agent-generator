import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { Button } from '@/components/primitives/Button';
import { Pill, StagePillBadge } from '@/components/primitives/Pill';
import { PublishHeader } from './PublishHeader';
import { PUBLISHED_NEXT, PUBLISHED_STATS, PUBLISHED_TAGS } from '@/lib/export-data';

interface Props {
  onBackToProject: () => void;
  onOpenMarketplace: () => void;
}

export function Published({ onBackToProject, onOpenMarketplace }: Props) {
  return (
    <>
      <PublishHeader step={3} />
      <div style={{ padding: '0 80px 40px', maxWidth: 1280, margin: '0 auto' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 24 }}>
          <span
            style={{
              width: 40,
              height: 40,
              background: tokens.ok,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Icon name="check" size={18} stroke="#fff" />
          </span>
          <div>
            <h2 className="ag-h2" style={{ margin: 0 }}>Published.</h2>
            <span className="ag-mono ag-small" style={{ color: tokens.muted }}>
              matrixhub.com/agents/daily-research-digest · v0.1.0
            </span>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: 24 }}>
          <Listing />
          <Next />
        </div>

        <div style={{ marginTop: 28, display: 'flex', gap: 12 }}>
          <span style={{ flex: 1 }} />
          <Button variant="ghost" onClick={onBackToProject}>Back to project</Button>
          <Button variant="primary" onClick={onOpenMarketplace}>
            <Icon name="cube" size={13} stroke="#fff" /> Open in Marketplace
          </Button>
        </div>
      </div>
    </>
  );
}

function Listing() {
  return (
    <div>
      <div className="ag-cap" style={{ marginBottom: 8 }}>Public listing</div>
      <div style={{ border: `1px solid ${tokens.border}`, background: '#fff', padding: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
          <div
            style={{
              width: 38,
              height: 38,
              background: tokens.ink,
              color: '#fff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontFamily: tokens.mono,
              fontSize: 13,
            }}
          >
            RM
          </div>
          <div style={{ flex: 1 }}>
            <h3 className="ag-h3" style={{ margin: 0 }}>Daily Research Digest</h3>
            <div className="ag-mono ag-small" style={{ color: tokens.muted, marginTop: 2 }}>
              by Ruslan Magana · just now
            </div>
          </div>
          <StagePillBadge stage="verified" />
        </div>
        <p className="ag-body" style={{ margin: '12px 0 14px' }}>
          A multi-agent crew that monitors arXiv, summarizes papers, and prepares a daily digest.
        </p>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 14 }}>
          {PUBLISHED_TAGS.map((t) => (
            <Pill key={t}>{t}</Pill>
          ))}
        </div>
        <div
          style={{
            display: 'flex',
            gap: 24,
            paddingTop: 12,
            borderTop: `1px solid ${tokens.border}`,
          }}
        >
          {PUBLISHED_STATS.map(([k, v]) => (
            <div key={k}>
              <div className="ag-cap" style={{ fontSize: 10 }}>{k}</div>
              <div className="ag-mono" style={{ fontSize: 13, marginTop: 2 }}>{v}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function Next() {
  return (
    <div>
      <div className="ag-cap" style={{ marginBottom: 8 }}>Next</div>
      <div style={{ border: `1px solid ${tokens.border}`, background: '#fff' }}>
        {PUBLISHED_NEXT.map((a, i) => (
          <button
            key={a.label}
            type="button"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '12px 14px',
              borderTop: 'none',
              borderLeft: 'none',
              borderRight: 'none',
              borderBottom:
                i < PUBLISHED_NEXT.length - 1 ? `1px solid ${tokens.border}` : 'none',
              background: 'transparent',
              cursor: 'pointer',
              fontFamily: 'inherit',
              textAlign: 'left',
              width: '100%',
            }}
          >
            <Icon name={a.icon} size={14} stroke={tokens.ink2} />
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 13, fontWeight: 500 }}>{a.label}</div>
              <div
                className={a.mono ? 'ag-mono ag-small' : 'ag-small'}
                style={{ marginTop: 2, color: tokens.muted }}
              >
                {a.sub}
              </div>
            </div>
            <Icon name="chev-r" size={13} stroke={tokens.muted} />
          </button>
        ))}
      </div>

      <div className="ag-cap" style={{ margin: '20px 0 8px' }}>Tip</div>
      <div
        style={{
          border: `1px solid ${tokens.border}`,
          background: tokens.surface,
          padding: 14,
          fontSize: 12.5,
          color: tokens.ink2,
          lineHeight: 1.5,
        }}
      >
        MatrixHub will email you when this listing crosses 10 installs or receives the first
        1-star rating. Adjust in <span className="ag-mono">Settings · Notifications</span>.
      </div>
    </div>
  );
}
