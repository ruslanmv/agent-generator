import { useState } from 'react';
import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { Button } from '@/components/primitives/Button';
import { Pill } from '@/components/primitives/Pill';
import { TypeBadge } from './TypeBadge';
import {
  buildManifest,
  installPlan,
  packageName,
  type MarketplaceItem,
} from '@/lib/marketplace-data';

const TABS = [
  { id: 'manifest', label: 'Manifest' },
  { id: 'tools',    label: 'Tools · 4' },
  { id: 'install',  label: 'Install plan' },
  { id: 'readme',   label: 'README' },
  { id: 'versions', label: 'Versions · 18' },
] as const;
type TabId = (typeof TABS)[number]['id'];

interface DetailProps {
  item: MarketplaceItem;
  onBack: () => void;
}

export function MarketplaceDetail({ item, onBack }: DetailProps) {
  const [tab, setTab] = useState<TabId>('manifest');
  const [installing, setInstalling] = useState(false);

  const manifest = buildManifest(item);
  const plan = installPlan(item, installing);

  return (
    <div style={{ display: 'flex', height: '100%', minHeight: 0 }}>
      <div style={{ flex: 1, padding: '24px 36px 36px', overflow: 'auto' }}>
        <Breadcrumb item={item} onBack={onBack} />

        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 20, marginBottom: 28 }}>
          <div
            style={{
              width: 64,
              height: 64,
              background: tokens.surface,
              border: `1px solid ${tokens.border}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontFamily: tokens.mono,
              fontSize: 22,
              color: tokens.ink,
              flexShrink: 0,
            }}
          >
            {item.name.split(' ').map((w) => w[0]).join('').slice(0, 2)}
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
              <TypeBadge type={item.type} size="lg" />
              {item.verified && (
                <Pill variant="ok">
                  <Icon name="check" size={10} stroke={tokens.ok} /> verified by Matrix Hub
                </Pill>
              )}
            </div>
            <h1 className="ag-h1" style={{ fontSize: 32, marginBottom: 4 }}>{item.name}</h1>
            <div className="ag-mono ag-small" style={{ color: tokens.muted, marginBottom: 10 }}>
              {item.id}
            </div>
            <p className="ag-body" style={{ color: tokens.ink2, maxWidth: 620 }}>
              {item.summary}
            </p>
          </div>
        </div>

        <StatStrip item={item} />

        <div
          role="tablist"
          style={{
            display: 'flex',
            gap: 24,
            borderBottom: `1px solid ${tokens.border}`,
            marginBottom: 18,
          }}
        >
          {TABS.map((t) => {
            const on = t.id === tab;
            return (
              <button
                key={t.id}
                type="button"
                role="tab"
                aria-selected={on}
                onClick={() => setTab(t.id)}
                style={{
                  padding: '0 0 12px',
                  fontSize: 13,
                  fontWeight: on ? 500 : 400,
                  color: on ? tokens.ink : tokens.muted,
                  borderBottom: `2px solid ${on ? tokens.accent : 'transparent'}`,
                  borderTop: 'none',
                  borderLeft: 'none',
                  borderRight: 'none',
                  background: 'transparent',
                  marginBottom: -1,
                  cursor: 'pointer',
                  fontFamily: 'inherit',
                }}
              >
                {t.label}
              </button>
            );
          })}
        </div>

        {tab === 'manifest' && <ManifestPanel manifest={manifest} />}
        {tab === 'install' && <InstallPanel item={item} plan={plan} />}
        {tab === 'readme' && (
          <div className="ag-body" style={{ color: tokens.ink2, lineHeight: 1.6, maxWidth: 720 }}>
            README rendering arrives in a follow-up batch — see Manifest for the canonical
            metadata.
          </div>
        )}
        {tab === 'tools' && (
          <div className="ag-body" style={{ color: tokens.ink2 }}>
            Tool surface inspection lands in Batch 8 (depends on the live catalog API).
          </div>
        )}
        {tab === 'versions' && (
          <div className="ag-body" style={{ color: tokens.ink2 }}>
            Version timeline lands in Batch 8.
          </div>
        )}
      </div>

      <RightRail
        item={item}
        plan={plan}
        installing={installing}
        onInstall={() => setInstalling(true)}
      />
    </div>
  );
}

function Breadcrumb({ item, onBack }: { item: MarketplaceItem; onBack: () => void }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 18 }}>
      <button
        type="button"
        onClick={onBack}
        className="ag-mono ag-small"
        style={{
          color: tokens.muted,
          background: 'transparent',
          border: 'none',
          padding: 0,
          cursor: 'pointer',
        }}
      >
        ← Marketplace
      </button>
      <span style={{ color: tokens.faint }}>/</span>
      <span className="ag-mono ag-small" style={{ color: tokens.muted }}>{item.type}</span>
      <span style={{ color: tokens.faint }}>/</span>
      <span className="ag-mono ag-small">{item.name}</span>
    </div>
  );
}

function StatStrip({ item }: { item: MarketplaceItem }) {
  const stats: [string, string, string][] = [
    ['Score',    item.score.toFixed(2),         'final · hybrid'],
    ['Installs', item.installs,                 'last 30 days'],
    ['Stars',    item.stars.toLocaleString(),   'GitHub'],
    ['Updated',  '4 days ago',                  `v${item.version}`],
  ];
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        border: `1px solid ${tokens.border}`,
        marginBottom: 28,
      }}
    >
      {stats.map(([k, v, sub], i) => (
        <div
          key={k}
          style={{ padding: 16, borderRight: i < 3 ? `1px solid ${tokens.border}` : 'none' }}
        >
          <div className="ag-cap" style={{ marginBottom: 6 }}>{k}</div>
          <div className="ag-mono" style={{ fontSize: 20, color: tokens.ink }}>{v}</div>
          <div className="ag-small" style={{ color: tokens.muted, marginTop: 2 }}>{sub}</div>
        </div>
      ))}
    </div>
  );
}

function ManifestPanel({ manifest }: { manifest: string }) {
  return (
    <>
      <div className="ag-cap" style={{ marginBottom: 8 }}>Manifest</div>
      <pre
        className="ag-mono"
        style={{
          background: tokens.termBg,
          color: tokens.termInk,
          padding: 18,
          fontSize: 12,
          lineHeight: 1.55,
          margin: 0,
          overflow: 'auto',
        }}
      >
        {manifest}
      </pre>
    </>
  );
}

function InstallPanel({
  item,
  plan,
}: {
  item: MarketplaceItem;
  plan: ReturnType<typeof installPlan>;
}) {
  return (
    <>
      <div className="ag-cap" style={{ marginBottom: 8 }}>CLI</div>
      <pre
        className="ag-mono"
        style={{
          background: tokens.termBg,
          color: tokens.termInk,
          padding: 18,
          fontSize: 12,
          lineHeight: 1.55,
          margin: '0 0 24px',
          overflow: 'auto',
        }}
      >
        {`$ ag install \\\n  ${item.id} \\\n  --target ./apps/${packageName(item.id)}`}
      </pre>
      <div className="ag-cap" style={{ marginBottom: 8 }}>Plan</div>
      <PlanList plan={plan} />
    </>
  );
}

function PlanList({ plan }: { plan: ReturnType<typeof installPlan> }) {
  return (
    <div style={{ background: '#fff', border: `1px solid ${tokens.border}` }}>
      {plan.map((step, i) => (
        <div
          key={step.key}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            padding: '10px 12px',
            borderBottom: i < plan.length - 1 ? `1px solid ${tokens.border}` : 'none',
          }}
        >
          <Icon
            name={step.status === 'ok' ? 'check' : step.status === 'run' ? 'spark' : 'dot'}
            size={11}
            stroke={
              step.status === 'ok'
                ? tokens.ok
                : step.status === 'run'
                  ? tokens.accent
                  : tokens.faint
            }
          />
          <div style={{ flex: 1, minWidth: 0 }}>
            <div className="ag-mono" style={{ fontSize: 12 }}>{step.key}</div>
            <div
              className="ag-small"
              style={{
                color: tokens.muted,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
            >
              {step.command}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

interface RightRailProps {
  item: MarketplaceItem;
  plan: ReturnType<typeof installPlan>;
  installing: boolean;
  onInstall: () => void;
}

function RightRail({ item, plan, installing, onInstall }: RightRailProps) {
  return (
    <aside
      style={{
        width: 340,
        borderLeft: `1px solid ${tokens.border}`,
        padding: '24px 24px',
        background: tokens.surface,
        flexShrink: 0,
        overflow: 'auto',
      }}
    >
      <Button
        variant="primary"
        onClick={onInstall}
        disabled={installing}
        style={{ width: '100%', justifyContent: 'center', height: 44, fontSize: 14 }}
      >
        <Icon name="download" size={14} stroke="#fff" />
        {installing ? 'Installing…' : 'Install to project'}
      </Button>
      <div className="ag-small" style={{ color: tokens.muted, marginTop: 8, textAlign: 'center' }}>
        installs into <span className="ag-mono" style={{ color: tokens.ink }}>./apps/arxiv-digest</span>
      </div>

      <div className="ag-cap" style={{ margin: '24px 0 8px' }}>Install plan</div>
      <PlanList plan={plan} />

      <div className="ag-cap" style={{ margin: '24px 0 8px' }}>Compatibility</div>
      <div style={{ background: '#fff', border: `1px solid ${tokens.border}`, padding: 12 }}>
        <div className="ag-small" style={{ color: tokens.muted, marginBottom: 4 }}>Frameworks</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 12 }}>
          {item.frameworks.map((f) => (
            <Pill key={f} variant="accent">{f}</Pill>
          ))}
        </div>
        <div className="ag-small" style={{ color: tokens.muted, marginBottom: 4 }}>Providers</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 12 }}>
          {item.providers.map((p) => (
            <Pill key={p}>{p}</Pill>
          ))}
        </div>
        <div className="ag-small" style={{ color: tokens.muted, marginBottom: 4 }}>Capabilities</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
          {item.capabilities.map((c) => (
            <Pill key={c}>{c}</Pill>
          ))}
        </div>
      </div>

      <div className="ag-cap" style={{ margin: '24px 0 8px' }}>CLI</div>
      <pre
        className="ag-mono"
        style={{
          background: tokens.termBg,
          color: tokens.termInk,
          padding: 12,
          fontSize: 11.5,
          lineHeight: 1.55,
          margin: 0,
          overflow: 'auto',
        }}
      >
        {`$ ag install \\\n  ${item.id} \\\n  --target ./apps/arxiv-digest`}
      </pre>
    </aside>
  );
}
