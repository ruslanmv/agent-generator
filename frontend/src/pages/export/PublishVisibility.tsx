import { useState } from 'react';
import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { Button } from '@/components/primitives/Button';
import { Pill, StagePillBadge } from '@/components/primitives/Pill';
import { PublishHeader } from './PublishHeader';
import { VISIBILITY_OPTIONS, type VisibilityOption } from '@/lib/export-data';

interface Props {
  onBack: () => void;
  onPublish: () => void;
}

export function PublishVisibility({ onBack, onPublish }: Props) {
  const [selected, setSelected] = useState<VisibilityOption['id']>('public');

  return (
    <>
      <PublishHeader step={2} />
      <div style={{ padding: '0 80px 40px', maxWidth: 1280, margin: '0 auto' }}>
        <h2 className="ag-h2" style={{ marginBottom: 8 }}>Who can see this?</h2>
        <p className="ag-body" style={{ marginBottom: 24, color: tokens.ink3 }}>
          You can change visibility later. Public listings are indexed by Marketplace search.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12 }}>
          {VISIBILITY_OPTIONS.map((v) => {
            const on = v.id === selected;
            return (
              <button
                key={v.id}
                type="button"
                role="radio"
                aria-checked={on}
                onClick={() => setSelected(v.id)}
                style={{
                  padding: 18,
                  border: `${on ? 2 : 1}px solid ${on ? tokens.ink : tokens.border}`,
                  background: '#fff',
                  textAlign: 'left',
                  cursor: 'pointer',
                  fontFamily: 'inherit',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span
                    style={{
                      width: 16,
                      height: 16,
                      borderRadius: '50%',
                      border: `1px solid ${on ? tokens.ink : tokens.borderStrong}`,
                      background: on ? tokens.ink : '#fff',
                      position: 'relative',
                      flexShrink: 0,
                    }}
                  >
                    {on && (
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
                  <Icon name={v.icon} size={15} stroke={tokens.ink} />
                  <h3 className="ag-h3" style={{ margin: 0, fontSize: 16, flex: 1 }}>{v.label}</h3>
                  {v.stage && <StagePillBadge stage={v.stage} />}
                </div>
                <div className="ag-body" style={{ marginTop: 8, fontSize: 13 }}>{v.blurb}</div>
                <div className="ag-mono ag-small" style={{ marginTop: 12, color: tokens.muted }}>
                  {v.meta}
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 12 }}>
                  {v.counts.map((c) => (
                    <Pill key={c}>{c}</Pill>
                  ))}
                </div>
              </button>
            );
          })}
        </div>

        <div
          style={{
            marginTop: 24,
            padding: 16,
            border: `1px solid ${tokens.border}`,
            background: tokens.surface,
            display: 'flex',
            alignItems: 'center',
            gap: 12,
          }}
        >
          <Icon name="cog" size={14} stroke={tokens.muted} />
          <span style={{ fontSize: 13, color: tokens.ink2, flex: 1 }}>
            License will be set to <b>Apache-2.0</b>. Risk level <b>medium</b> will be shown on
            the listing. <span className="ag-mono">email_send</span> requires user approval; shell
            access disabled by default.
          </span>
          <span className="ag-mono ag-small" style={{ color: tokens.muted }}>
            per matrixhub.manifest.json
          </span>
        </div>

        <div style={{ marginTop: 28, display: 'flex', gap: 12 }}>
          <Button variant="ghost" onClick={onBack}>
            <Icon name="arrow-l" size={13} /> Back
          </Button>
          <span style={{ flex: 1 }} />
          <Button variant="primary" onClick={onPublish}>
            <Icon name="send" size={13} stroke="#fff" /> Publish to MatrixHub
          </Button>
        </div>
      </div>
    </>
  );
}
