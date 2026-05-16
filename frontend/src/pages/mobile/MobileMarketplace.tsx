// Mobile marketplace — single-column list and detail.
import { useMemo, useState } from 'react';
import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { Button } from '@/components/primitives/Button';
import { Pill } from '@/components/primitives/Pill';
import { TypeBadge } from '@/pages/marketplace/TypeBadge';
import { AHeader, BottomBar } from './MobileChrome';
import { buildManifest, installPlan, MH_ITEMS, MH_TYPES, type AssetType, type MarketplaceItem } from '@/lib/marketplace-data';

export function MobileMarketplace() {
  const [openId, setOpenId] = useState<string | null>(null);
  const item = openId ? MH_ITEMS.find((i) => i.id === openId) ?? null : null;
  if (item) return <Detail item={item} onBack={() => setOpenId(null)} />;
  return <Browse onOpen={setOpenId} />;
}

function Browse({ onOpen }: { onOpen: (id: string) => void }) {
  const [type, setType] = useState<AssetType>('any');
  const [q, setQ] = useState('');
  const filtered = useMemo(() => MH_ITEMS.filter((it) => (type === 'any' || it.type === type) && (q.trim() === '' || it.name.toLowerCase().includes(q.toLowerCase()) || it.summary.toLowerCase().includes(q.toLowerCase()))), [type, q]);
  return (
    <div style={{ background: '#fff', display: 'flex', flexDirection: 'column', minHeight: '100%' }}>
      <AHeader title="Marketplace" sub="Powered by Matrix Hub" sticky />
      <div style={{ padding: '12px 16px 0' }}>
        <div style={{ height: 44, border: `1.5px solid ${tokens.ink}`, display: 'flex', alignItems: 'center', padding: '0 14px', gap: 10, background: '#fff', marginBottom: 12 }}>
          <Icon name="search" size={16} stroke={tokens.ink} />
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Find an agent, tool, or MCP server…" style={{ flex: 1, border: 0, outline: 0, background: 'transparent', font: `15px ${tokens.sans}`, color: tokens.ink }} />
          <span className="ag-mono ag-small" style={{ color: tokens.faint }}>{filtered.length}</span>
        </div>
        <div style={{ display: 'flex', gap: 6, marginBottom: 12, flexWrap: 'wrap' }}>
          {MH_TYPES.map((t) => {
            const on = t.id === type;
            return (
              <button key={t.id} type="button" onClick={() => setType(t.id)} style={{ padding: '6px 12px', fontSize: 12, fontFamily: tokens.mono, background: on ? tokens.ink : '#fff', color: on ? '#fff' : tokens.ink2, border: `1px solid ${on ? tokens.ink : tokens.border}`, cursor: 'pointer' }}>
                {t.label}<span style={{ marginLeft: 6, color: on ? '#fff' : tokens.muted, opacity: 0.7 }}>{t.count}</span>
              </button>
            );
          })}
        </div>
      </div>
      <div style={{ padding: '0 16px 16px', flex: 1 }}>
        {filtered.map((it) => (
          <button key={it.id} type="button" onClick={() => onOpen(it.id)} style={{ border: `1px solid ${tokens.border}`, background: '#fff', padding: 14, cursor: 'pointer', display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 8, width: '100%', textAlign: 'left', fontFamily: 'inherit' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <TypeBadge type={it.type} />
              {it.verified && <Pill variant="ok"><Icon name="check" size={9} stroke={tokens.ok} /> verified</Pill>}
              <span style={{ flex: 1 }} />
              <span className="ag-mono ag-small" style={{ color: tokens.muted }}>★ {it.stars.toLocaleString()}</span>
            </div>
            <div>
              <div style={{ fontSize: 15, fontWeight: 500 }}>{it.name}</div>
              <div className="ag-mono ag-small" style={{ color: tokens.muted }}>{it.org} · v{it.version}</div>
            </div>
            <p className="ag-small" style={{ color: tokens.ink2, lineHeight: 1.5, margin: 0 }}>{it.summary}</p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>{it.capabilities.map((c) => <Pill key={c}>{c}</Pill>)}</div>
          </button>
        ))}
        {filtered.length === 0 && <div className="ag-small" style={{ color: tokens.muted, padding: 24 }}>No matches. Try clearing the type filter or refining the query.</div>}
      </div>
    </div>
  );
}

function Detail({ item, onBack }: { item: MarketplaceItem; onBack: () => void }) {
  const manifest = buildManifest(item);
  const plan = installPlan(item, false);
  return (
    <div style={{ background: '#fff', display: 'flex', flexDirection: 'column', minHeight: '100%' }}>
      <AHeader title={item.name} sub={item.id} back onBack={onBack} sticky />
      <div style={{ padding: '16px 16px 8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
          <TypeBadge type={item.type} size="lg" />
          {item.verified && <Pill variant="ok"><Icon name="check" size={10} stroke={tokens.ok} /> verified</Pill>}
          <span style={{ flex: 1 }} />
          <span className="ag-mono ag-small" style={{ color: tokens.muted }}>★ {item.stars.toLocaleString()}</span>
        </div>
        <p className="ag-body" style={{ color: tokens.ink2 }}>{item.summary}</p>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', border: `1px solid ${tokens.border}`, margin: '0 16px' }}>
        {[['Score', item.score.toFixed(2)], ['Installs', item.installs], ['Stars', item.stars.toLocaleString()], ['Updated', '4 days ago']].map(([k, v], i) => (
          <div key={k} style={{ padding: 12, borderRight: i % 2 === 0 ? `1px solid ${tokens.border}` : 'none', borderBottom: i < 2 ? `1px solid ${tokens.border}` : 'none' }}>
            <div className="ag-cap" style={{ marginBottom: 4 }}>{k}</div>
            <div className="ag-mono" style={{ fontSize: 16, color: tokens.ink }}>{v}</div>
          </div>
        ))}
      </div>
      <div style={{ padding: '20px 16px 0' }}>
        <div className="ag-cap" style={{ marginBottom: 8 }}>Compatibility</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 12 }}>
          {item.frameworks.map((f) => <Pill key={f} variant="accent">{f}</Pill>)}
          {item.providers.map((p) => <Pill key={p}>{p}</Pill>)}
        </div>
      </div>
      <div style={{ padding: '8px 16px 16px', flex: 1 }}>
        <div className="ag-cap" style={{ marginBottom: 8 }}>Install plan</div>
        <div style={{ background: '#fff', border: `1px solid ${tokens.border}`, marginBottom: 16 }}>
          {plan.map((step, i) => (
            <div key={step.key} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 12px', borderBottom: i < plan.length - 1 ? `1px solid ${tokens.border}` : 'none' }}>
              <Icon name={step.status === 'ok' ? 'check' : 'dot'} size={11} stroke={step.status === 'ok' ? tokens.ok : tokens.faint} />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div className="ag-mono" style={{ fontSize: 12 }}>{step.key}</div>
                <div className="ag-small" style={{ color: tokens.muted, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{step.command}</div>
              </div>
            </div>
          ))}
        </div>
        <div className="ag-cap" style={{ marginBottom: 8 }}>Manifest</div>
        <pre className="ag-mono" style={{ background: tokens.termBg, color: tokens.termInk, padding: 12, fontSize: 11, lineHeight: 1.55, margin: 0, overflow: 'auto', maxHeight: 220 }}>{manifest}</pre>
      </div>
      <BottomBar>
        <Button variant="primary" style={{ width: '100%', height: 48, fontSize: 15, justifyContent: 'center' }}>
          <Icon name="download" size={14} stroke="#fff" /> Install to project
        </Button>
      </BottomBar>
    </div>
  );
}
