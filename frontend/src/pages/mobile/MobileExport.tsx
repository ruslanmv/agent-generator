// Mobile Export — condensed Done + single-page MatrixHub publish + success.
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { Button } from '@/components/primitives/Button';
import { Pill, StagePillBadge } from '@/components/primitives/Pill';
import { HomePilotMark } from '@/components/icons/Logo';
import { AHeader, BottomBar } from './MobileChrome';
import { EXPORT_GROUPS, RUN_SUMMARY, VALIDATION_PASSING, VALIDATION_ROWS, VISIBILITY_OPTIONS, type VisibilityOption } from '@/lib/export-data';

type Phase = 'done' | 'publish' | 'published';

export function MobileExport() {
  const navigate = useNavigate();
  const [phase, setPhase] = useState<Phase>('done');
  if (phase === 'publish') return <PublishStep onBack={() => setPhase('done')} onPublish={() => setPhase('published')} />;
  if (phase === 'published') return <PublishedStep onBack={() => setPhase('done')} onMarketplace={() => navigate('/marketplace')} />;
  return <DoneStep onPublish={() => setPhase('publish')} />;
}

function DoneStep({ onPublish }: { onPublish: () => void }) {
  return (
    <div style={{ background: '#fff', display: 'flex', flexDirection: 'column', minHeight: '100%' }}>
      <AHeader title="Project ready" sub="22 files · 1.4 MB · 18.4s" sticky />
      <div style={{ padding: '0 16px', flex: 1 }}>
        <div className="ag-cap" style={{ marginTop: 12, marginBottom: 8 }}>Publish · Share</div>
        <button type="button" onClick={onPublish} style={{ border: `2px solid ${tokens.ink}`, padding: 14, marginBottom: 8, position: 'relative', display: 'flex', alignItems: 'center', gap: 12, background: '#fff', cursor: 'pointer', width: '100%', textAlign: 'left', fontFamily: 'inherit' }}>
          <span style={{ position: 'absolute', top: -10, left: 12 }}><Pill variant="accent">recommended</Pill></span>
          <Icon name="cube" size={22} stroke={tokens.ink} />
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 14, fontWeight: 600 }}>Publish to MatrixHub</div>
            <div className="ag-small" style={{ marginTop: 2, fontSize: 11 }}>Validate · choose visibility · publish</div>
          </div>
          <Icon name="chev-r" size={14} stroke={tokens.ink} />
        </button>
        <div className="ag-cap" style={{ margin: '20px 0 8px' }}>Export · Deploy</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 6 }}>
          {EXPORT_GROUPS.flatMap((g) => g.items).map((a) => (
            <div key={a.id} style={{ padding: '12px 10px', border: `1px solid ${tokens.border}`, display: 'flex', alignItems: 'center', gap: 8 }}>
              {a.homepilot ? <HomePilotMark size={20} /> : <Icon name={a.icon ?? 'cube'} size={13} stroke={tokens.ink2} />}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  <span style={{ fontSize: 12.5, fontWeight: 500 }}>{a.label}</span>
                  {a.stage !== 'core' && <StagePillBadge stage={a.stage} />}
                </div>
                <div className="ag-mono" style={{ fontSize: 10.5, color: tokens.muted, marginTop: 2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{a.sub}</div>
              </div>
            </div>
          ))}
        </div>
        <div className="ag-cap" style={{ margin: '20px 0 8px' }}>Run summary</div>
        <div style={{ border: `1px solid ${tokens.border}`, marginBottom: 24 }}>
          {RUN_SUMMARY.map((row, i) => (
            <div key={row.key} style={{ display: 'flex', padding: '10px 14px', borderBottom: i < RUN_SUMMARY.length - 1 ? `1px solid ${tokens.border}` : 'none' }}>
              <span style={{ flex: 1, fontSize: 12.5, color: tokens.ink2 }}>{row.key}</span>
              <span className="ag-mono" style={{ fontSize: 12, color: row.color === 'ok' ? tokens.ok : row.color === 'warn' ? tokens.warn : row.color === 'err' ? tokens.err : tokens.ink, fontWeight: row.color ? 500 : 400 }}>{row.value}</span>
            </div>
          ))}
        </div>
      </div>
      <BottomBar>
        <Button variant="primary" onClick={onPublish} style={{ width: '100%', height: 48, fontSize: 15, justifyContent: 'center' }}>
          <Icon name="send" size={14} stroke="#fff" /> Publish to MatrixHub
        </Button>
      </BottomBar>
    </div>
  );
}

function PublishStep({ onBack, onPublish }: { onBack: () => void; onPublish: () => void }) {
  const [visibility, setVisibility] = useState<VisibilityOption['id']>('public');
  return (
    <div style={{ background: '#fff', display: 'flex', flexDirection: 'column', minHeight: '100%' }}>
      <AHeader title="Publish to MatrixHub" sub="Validation · visibility · publish" back onBack={onBack} sticky />
      <div style={{ padding: '12px 16px 0' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
          <Pill variant="ok">{VALIDATION_PASSING} / {VALIDATION_ROWS.length} passing</Pill>
          <span className="ag-mono ag-small" style={{ color: tokens.muted }}>matrixhub.agent.v1</span>
        </div>
        <div style={{ border: `1px solid ${tokens.border}` }}>
          {VALIDATION_ROWS.slice(0, 6).map((row, i, arr) => (
            <div key={row.label} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '11px 12px', borderBottom: i < arr.length - 1 ? `1px solid ${tokens.border}` : 'none' }}>
              <span style={{ width: 14, textAlign: 'center', fontFamily: tokens.mono, fontSize: 13, fontWeight: 600, color: row.status === 'ok' ? tokens.ok : tokens.warn }}>{row.status === 'ok' ? '✓' : '⚠'}</span>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 13, fontWeight: 500 }}>{row.label}</div>
                <div className="ag-mono ag-small" style={{ fontSize: 11, marginTop: 2, color: tokens.muted }}>{row.note}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
      <div style={{ padding: '20px 16px 16px', flex: 1 }}>
        <div className="ag-cap" style={{ marginBottom: 8 }}>Visibility</div>
        {VISIBILITY_OPTIONS.map((v) => {
          const on = v.id === visibility;
          return (
            <button key={v.id} type="button" role="radio" aria-checked={on} onClick={() => setVisibility(v.id)} style={{ padding: 12, marginBottom: 6, border: `${on ? 2 : 1}px solid ${on ? tokens.ink : tokens.border}`, display: 'flex', alignItems: 'center', gap: 10, background: '#fff', cursor: 'pointer', width: '100%', textAlign: 'left', fontFamily: 'inherit' }}>
              <span style={{ width: 16, height: 16, borderRadius: '50%', border: `1px solid ${on ? tokens.ink : tokens.borderStrong}`, background: on ? tokens.ink : '#fff', position: 'relative', flexShrink: 0 }}>
                {on && <span style={{ position: 'absolute', inset: 4, background: '#fff', borderRadius: '50%' }} />}
              </span>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 13, fontWeight: 500 }}>{v.label}</div>
                <div className="ag-mono ag-small" style={{ fontSize: 11, marginTop: 2, color: tokens.muted }}>{v.blurb}</div>
              </div>
            </button>
          );
        })}
      </div>
      <BottomBar>
        <Button variant="primary" onClick={onPublish} style={{ width: '100%', height: 48, fontSize: 15, justifyContent: 'center' }}>
          <Icon name="send" size={14} stroke="#fff" /> Publish to MatrixHub
        </Button>
      </BottomBar>
    </div>
  );
}

function PublishedStep({ onBack, onMarketplace }: { onBack: () => void; onMarketplace: () => void }) {
  return (
    <div style={{ background: '#fff', display: 'flex', flexDirection: 'column', minHeight: '100%' }}>
      <AHeader title="Published" back onBack={onBack} sticky />
      <div style={{ padding: '24px 16px', flex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 18 }}>
          <span style={{ width: 40, height: 40, background: tokens.ok, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Icon name="check" size={18} stroke="#fff" />
          </span>
          <div>
            <div className="ag-h2" style={{ margin: 0 }}>Published.</div>
            <span className="ag-mono ag-small" style={{ color: tokens.muted }}>v0.1.0 · just now</span>
          </div>
        </div>
        <div className="ag-cap" style={{ marginBottom: 8 }}>Public listing</div>
        <div style={{ border: `1px solid ${tokens.border}`, padding: 16, marginBottom: 16 }}>
          <h3 className="ag-h3" style={{ margin: '0 0 4px' }}>Daily Research Digest</h3>
          <div className="ag-mono ag-small" style={{ color: tokens.muted, marginBottom: 12 }}>matrixhub.com/agents/daily-research-digest</div>
          <p className="ag-small" style={{ color: tokens.ink2, margin: 0 }}>A multi-agent crew that monitors arXiv, summarizes papers, and prepares a daily digest.</p>
        </div>
      </div>
      <BottomBar>
        <Button variant="ghost" onClick={onBack} style={{ flex: 1, height: 48, justifyContent: 'center' }}>Back</Button>
        <Button variant="primary" onClick={onMarketplace} style={{ flex: 2, height: 48, fontSize: 15, justifyContent: 'center' }}>
          <Icon name="cube" size={13} stroke="#fff" /> Open in Marketplace
        </Button>
      </BottomBar>
    </div>
  );
}
