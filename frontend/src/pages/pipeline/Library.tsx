import { useMemo, useState } from 'react';
import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { Input } from '@/components/primitives/Input';
import { LIBRARY, NODE_META, type NodeKind } from '@/lib/pipeline-data';

interface LibraryProps {
  onPickItem?: (kind: NodeKind, label: string) => void;
}

export function Library({ onPickItem }: LibraryProps) {
  const [q, setQ] = useState('');

  const groups = useMemo(() => {
    const needle = q.toLowerCase();
    return LIBRARY.map((g) => ({
      ...g,
      items: g.items.filter((it) => it.toLowerCase().includes(needle)),
    })).filter((g) => g.items.length > 0);
  }, [q]);

  return (
    <aside
      style={{
        width: 240,
        borderRight: `1px solid ${tokens.border}`,
        padding: 16,
        overflow: 'auto',
        flexShrink: 0,
      }}
    >
      <div className="ag-cap" style={{ marginBottom: 10 }}>Library</div>
      <Input
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder="Search…"
        style={{ marginBottom: 14 }}
      />
      {groups.map((g) => (
        <div key={g.heading} style={{ marginBottom: 18 }}>
          <div className="ag-cap" style={{ marginBottom: 6, color: tokens.ink3 }}>{g.heading}</div>
          {g.items.map((it) => (
            <button
              key={it}
              type="button"
              onClick={() => onPickItem?.(g.kind, it)}
              draggable
              onDragStart={(e) => {
                e.dataTransfer.setData('application/x-ag-node', JSON.stringify({ kind: g.kind, label: it }));
                e.dataTransfer.effectAllowed = 'copy';
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                padding: '7px 8px',
                border: `1px solid ${tokens.border}`,
                marginBottom: 4,
                background: '#fff',
                cursor: 'grab',
                width: '100%',
                textAlign: 'left',
                fontFamily: 'inherit',
              }}
            >
              <Icon name={NODE_META[g.kind].icon} size={13} stroke={NODE_META[g.kind].color} />
              <span className="ag-mono" style={{ fontSize: 12 }}>{it}</span>
            </button>
          ))}
        </div>
      ))}
    </aside>
  );
}
