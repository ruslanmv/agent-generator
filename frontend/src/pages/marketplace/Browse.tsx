import { useMemo, useState } from 'react';
import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { Button } from '@/components/primitives/Button';
import { Pill } from '@/components/primitives/Pill';
import { Checkbox } from '@/components/primitives/Input';
import { Nav } from '@/components/primitives/Nav';
import { TypeBadge } from './TypeBadge';
import {
  MH_CAPABILITIES,
  MH_FRAMEWORKS,
  MH_ITEMS,
  MH_SEARCH_HINTS,
  MH_TYPES,
  SEARCH_MODES,
  type AssetType,
  type MarketplaceItem,
  type SearchMode,
} from '@/lib/marketplace-data';

interface BrowseProps {
  onOpen: (id: string) => void;
}

export function MarketplaceBrowse({ onOpen }: BrowseProps) {
  const [type, setType] = useState<AssetType>('any');
  const [q, setQ] = useState('summarize pdfs');
  const [caps, setCaps] = useState<string[]>(['pdf']);
  const [frameworks, setFrameworks] = useState<string[]>([]);
  const [mode, setMode] = useState<SearchMode>('hybrid');

  const filtered = useMemo<MarketplaceItem[]>(
    () =>
      MH_ITEMS.filter(
        (it) =>
          (type === 'any' || it.type === type) &&
          (caps.length === 0 || caps.some((c) => it.capabilities.includes(c))) &&
          (frameworks.length === 0 ||
            it.frameworks.includes('*') ||
            frameworks.some((f) => it.frameworks.includes(f))) &&
          (q.trim() === '' ||
            it.name.toLowerCase().includes(q.toLowerCase()) ||
            it.summary.toLowerCase().includes(q.toLowerCase())),
      ),
    [type, q, caps, frameworks],
  );

  const toggle = (arr: string[], setArr: (v: string[]) => void, v: string) =>
    setArr(arr.includes(v) ? arr.filter((x) => x !== v) : [...arr, v]);

  return (
    <div style={{ display: 'flex', height: '100%', minHeight: 0 }}>
      <FacetRail
        type={type}
        onType={setType}
        caps={caps}
        onToggleCap={(c) => toggle(caps, setCaps, c)}
        frameworks={frameworks}
        onToggleFramework={(f) => toggle(frameworks, setFrameworks, f)}
        mode={mode}
        onMode={setMode}
      />

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        <SearchHeader
          q={q}
          onQ={setQ}
          mode={mode}
          resultCount={filtered.length}
          onTryHint={(h) => setQ(h)}
        />

        <div style={{ flex: 1, overflow: 'auto', padding: '20px 36px 36px' }}>
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: 14, gap: 12 }}>
            <span className="ag-cap">Top matches</span>
            <span style={{ flex: 1 }} />
            <span className="ag-small" style={{ color: tokens.muted }}>Sort</span>
            <span
              className="ag-mono ag-small"
              style={{
                padding: '3px 8px',
                border: `1px solid ${tokens.border}`,
              }}
            >
              relevance ▾
            </span>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(2, 1fr)',
              gap: 12,
            }}
          >
            {filtered.map((it) => (
              <ResultCard key={it.id} item={it} onOpen={() => onOpen(it.id)} />
            ))}
            {filtered.length === 0 && (
              <div className="ag-small" style={{ color: tokens.muted, padding: 24 }}>
                No matches for the current filters. Try clearing capabilities or
                widening the asset type.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

interface FacetRailProps {
  type: AssetType;
  onType: (t: AssetType) => void;
  caps: string[];
  onToggleCap: (c: string) => void;
  frameworks: string[];
  onToggleFramework: (f: string) => void;
  mode: SearchMode;
  onMode: (m: SearchMode) => void;
}

function FacetRail({
  type, onType,
  caps, onToggleCap,
  frameworks, onToggleFramework,
  mode, onMode,
}: FacetRailProps) {
  return (
    <aside
      style={{
        width: 240,
        borderRight: `1px solid ${tokens.border}`,
        padding: '24px 20px',
        flexShrink: 0,
        overflow: 'auto',
      }}
    >
      <div className="ag-cap" style={{ marginBottom: 10 }}>Type</div>
      <Nav
        vertical
        dense
        items={MH_TYPES.map((t) => ({ id: t.id, label: t.label, icon: t.icon, count: t.count }))}
        value={type}
        onChange={(id) => onType(id as AssetType)}
      />

      <div className="ag-cap" style={{ margin: '24px 0 10px' }}>Capabilities</div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
        {MH_CAPABILITIES.map((c) => {
          const on = caps.includes(c);
          return (
            <button
              key={c}
              type="button"
              onClick={() => onToggleCap(c)}
              className="ag-mono"
              style={{
                padding: '3px 8px',
                fontSize: 11,
                border: `1px solid ${on ? tokens.ink : tokens.border}`,
                background: on ? tokens.ink : '#fff',
                color: on ? '#fff' : tokens.ink2,
                cursor: 'pointer',
              }}
            >
              {c}
            </button>
          );
        })}
      </div>

      <div className="ag-cap" style={{ margin: '24px 0 10px' }}>Framework</div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {MH_FRAMEWORKS.map((f) => (
          <label
            key={f}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              fontSize: 12.5,
              color: tokens.ink2,
              cursor: 'pointer',
            }}
          >
            <Checkbox
              checked={frameworks.includes(f)}
              onChange={() => onToggleFramework(f)}
            />
            <span className="ag-mono">{f}</span>
          </label>
        ))}
      </div>

      <div className="ag-cap" style={{ margin: '24px 0 10px' }}>Search mode</div>
      <div style={{ display: 'inline-flex', border: `1px solid ${tokens.border}` }}>
        {SEARCH_MODES.map((m, i) => {
          const on = mode === m;
          return (
            <button
              key={m}
              type="button"
              onClick={() => onMode(m)}
              style={{
                padding: '5px 9px',
                fontSize: 11,
                fontFamily: tokens.mono,
                background: on ? tokens.ink : '#fff',
                color: on ? '#fff' : tokens.ink2,
                cursor: 'pointer',
                border: 'none',
                borderRight: i < SEARCH_MODES.length - 1 ? `1px solid ${tokens.border}` : 'none',
              }}
            >
              {m}
            </button>
          );
        })}
      </div>

      <div
        style={{
          marginTop: 24,
          padding: 12,
          background: tokens.surface,
          border: `1px solid ${tokens.border}`,
        }}
      >
        <div className="ag-cap" style={{ marginBottom: 6 }}>Catalog</div>
        <div className="ag-mono ag-small" style={{ color: tokens.muted, lineHeight: 1.5 }}>
          api.matrixhub.io
          <br />
          indexed 4 min ago
          <br />
          <span style={{ color: tokens.ok }}>● connected</span>
        </div>
      </div>
    </aside>
  );
}

interface SearchHeaderProps {
  q: string;
  onQ: (v: string) => void;
  mode: SearchMode;
  resultCount: number;
  onTryHint: (h: string) => void;
}

function SearchHeader({ q, onQ, mode, resultCount, onTryHint }: SearchHeaderProps) {
  return (
    <div
      style={{
        padding: '24px 36px 16px',
        borderBottom: `1px solid ${tokens.border}`,
        flexShrink: 0,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, marginBottom: 14 }}>
        <h2 className="ag-h2">Marketplace</h2>
        <span className="ag-mono ag-small" style={{ color: tokens.muted }}>
          powered by <b style={{ color: tokens.ink }}>Matrix Hub</b>
        </span>
      </div>
      <div style={{ display: 'flex', gap: 8 }}>
        <div
          style={{
            flex: 1,
            height: 44,
            border: `1.5px solid ${tokens.ink}`,
            display: 'flex',
            alignItems: 'center',
            padding: '0 14px',
            gap: 10,
            background: '#fff',
          }}
        >
          <Icon name="search" size={16} stroke={tokens.ink} />
          <input
            value={q}
            onChange={(e) => onQ(e.target.value)}
            placeholder="Find an agent, tool, or MCP server…"
            style={{
              flex: 1,
              border: 0,
              outline: 0,
              background: 'transparent',
              font: `15px ${tokens.sans}`,
              color: tokens.ink,
            }}
          />
          <span className="ag-mono ag-small" style={{ color: tokens.faint }}>
            {resultCount} results · {mode}
          </span>
        </div>
        <Button variant="ghost">
          <Icon name="download" size={13} /> Publish
        </Button>
      </div>
      <div style={{ display: 'flex', gap: 6, marginTop: 12, alignItems: 'center', flexWrap: 'wrap' }}>
        <span className="ag-small" style={{ color: tokens.muted, marginRight: 4 }}>try:</span>
        {MH_SEARCH_HINTS.map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => onTryHint(s)}
            style={{ background: 'transparent', border: 'none', padding: 0, cursor: 'pointer' }}
          >
            <Pill>{s}</Pill>
          </button>
        ))}
      </div>
    </div>
  );
}

interface ResultCardProps {
  item: MarketplaceItem;
  onOpen: () => void;
}

function ResultCard({ item, onOpen }: ResultCardProps) {
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onOpen}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onOpen();
        }
      }}
      style={{
        border: `1px solid ${tokens.border}`,
        background: '#fff',
        padding: 16,
        cursor: 'pointer',
        display: 'flex',
        flexDirection: 'column',
        gap: 10,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <TypeBadge type={item.type} />
        {item.verified && (
          <Pill variant="ok">
            <Icon name="check" size={9} stroke={tokens.ok} /> verified
          </Pill>
        )}
        <span style={{ flex: 1 }} />
        <span className="ag-mono ag-small" style={{ color: tokens.muted }}>
          ★ {item.stars.toLocaleString()}
        </span>
      </div>
      <div>
        <div style={{ fontSize: 16, fontWeight: 500, marginBottom: 2 }}>{item.name}</div>
        <div className="ag-mono ag-small" style={{ color: tokens.muted }}>
          {item.org} · v{item.version}
        </div>
      </div>
      <p className="ag-small" style={{ color: tokens.ink2, lineHeight: 1.5, margin: 0 }}>
        {item.summary}
      </p>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
        {item.capabilities.map((c) => (
          <Pill key={c}>{c}</Pill>
        ))}
      </div>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          marginTop: 'auto',
          paddingTop: 8,
          borderTop: `1px dashed ${tokens.border}`,
        }}
      >
        <span className="ag-mono ag-small" style={{ color: tokens.muted }}>
          score <b style={{ color: tokens.ink }}>{item.score.toFixed(2)}</b>
        </span>
        <span className="ag-mono ag-small" style={{ color: tokens.muted }}>
          ↓ {item.installs}
        </span>
        <span style={{ flex: 1 }} />
        <Button
          variant="ghost"
          size="sm"
          onClick={(e) => {
            e.stopPropagation();
            onOpen();
          }}
        >
          <Icon name="download" size={12} /> Install
        </Button>
      </div>
    </div>
  );
}
