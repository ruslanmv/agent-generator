// File preview pane used on the Review step.
// Left = sticky tree, right = file content with tabs and line numbers.
// Two views: "neutral" (the package every framework gets) and "hp-diff"
// (HomePilot-specific files added on top, highlighted as additions).

import { useState } from 'react';
import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { HomePilotMark } from '@/components/icons/Logo';
import { NEUTRAL_TREE, HP_DIFF_TREE, SAMPLE_FILE_BODY, type TreeNode } from '@/lib/wizard-data';

type View = 'neutral' | 'hp-diff';

interface Props {
  height?: number;
}

export function FilePreviewPane({ height = 360 }: Props) {
  const [view, setView] = useState<View>('neutral');
  const tree: TreeNode[] = view === 'hp-diff' ? HP_DIFF_TREE : NEUTRAL_TREE;
  const fileCount = tree.filter((n) => n.type === 'f').length;
  const lines = SAMPLE_FILE_BODY.split('\n');

  const tabs = ['researcher.py', 'crew.py', 'homepilot.agent.json'];

  return (
    <div style={{ border: `1px solid ${tokens.border}`, background: '#fff' }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          borderBottom: `1px solid ${tokens.border}`,
          background: tokens.surface,
        }}
      >
        {(
          [
            { id: 'neutral' as const, label: 'Neutral package', sub: 'agent.manifest.json' },
            { id: 'hp-diff' as const, label: 'HomePilot diff', sub: '+ 3 files', mark: true },
          ]
        ).map((v, i) => {
          const on = v.id === view;
          return (
            <button
              key={v.id}
              type="button"
              onClick={() => setView(v.id)}
              style={{
                padding: '8px 14px',
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                background: on ? '#fff' : 'transparent',
                borderRight: i === 0 ? `1px solid ${tokens.border}` : 'none',
                borderTop: on ? `2px solid ${tokens.accent}` : '2px solid transparent',
                borderBottom: on ? '1px solid #fff' : 'none',
                borderLeft: 'none',
                marginBottom: -1,
                cursor: 'pointer',
              }}
            >
              {v.mark && <HomePilotMark size={14} />}
              <span
                style={{
                  fontSize: 12.5,
                  fontWeight: on ? 500 : 400,
                  color: on ? tokens.ink : tokens.muted,
                }}
              >
                {v.label}
              </span>
              <span className="ag-mono ag-small" style={{ color: tokens.muted, fontSize: 11 }}>
                {v.sub}
              </span>
            </button>
          );
        })}
        <span style={{ flex: 1 }} />
        <span className="ag-mono ag-small" style={{ padding: '0 12px', color: tokens.muted }}>
          {fileCount} files · regenerate · lock · diff
        </span>
      </div>

      <div style={{ display: 'flex', height }}>
        <Tree tree={tree} fileCount={fileCount} />
        <Code tabs={tabs} lines={lines} />
      </div>
    </div>
  );
}

function Tree({ tree, fileCount }: { tree: TreeNode[]; fileCount: number }) {
  return (
    <div
      style={{
        width: 240,
        borderRight: `1px solid ${tokens.border}`,
        display: 'flex',
        flexDirection: 'column',
        minHeight: 0,
      }}
    >
      <div
        style={{
          padding: '8px 10px',
          borderBottom: `1px solid ${tokens.border}`,
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          background: tokens.surface,
        }}
      >
        <Icon name="folder" size={12} stroke={tokens.muted} />
        <span
          className="ag-mono"
          style={{
            fontSize: 11,
            color: tokens.muted,
            letterSpacing: '.04em',
            textTransform: 'uppercase',
            flex: 1,
          }}
        >
          files · {fileCount}
        </span>
        <Icon name="search" size={11} stroke={tokens.muted} />
      </div>
      <div style={{ flex: 1, overflow: 'auto', padding: '4px 0' }}>
        {tree.map((n, i) => (
          <div
            key={`${n.name}-${i}`}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              padding: `3px ${10 + n.depth * 12}px 3px 10px`,
              background: n.selected ? tokens.accentHi : n.diff ? '#defbe6' : 'transparent',
              color: n.selected ? tokens.accentDim : n.type === 'd' ? tokens.ink : tokens.ink2,
              fontFamily: tokens.mono,
              fontSize: 12,
              lineHeight: 1.5,
              borderLeft: n.selected
                ? `2px solid ${tokens.accent}`
                : n.diff
                  ? `2px solid ${tokens.ok}`
                  : '2px solid transparent',
            }}
          >
            {n.diff && <span style={{ width: 8, color: tokens.ok, fontWeight: 700 }}>{n.diff}</span>}
            {n.type === 'd' ? (
              <Icon
                name={n.open ? 'chev-d' : 'chev-r'}
                size={10}
                stroke={n.selected ? tokens.accentDim : tokens.muted}
              />
            ) : (
              !n.diff && <span style={{ width: 10, display: 'inline-block' }} />
            )}
            <Icon
              name={n.type === 'd' ? 'folder' : 'doc'}
              size={11}
              stroke={n.selected ? tokens.accentDim : tokens.muted}
            />
            <span
              style={{
                flex: 1,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
            >
              {n.name}
              {n.type === 'd' ? '/' : ''}
            </span>
            {n.badge === 'hp' && <HomePilotMark size={14} />}
            {n.locked && (
              <span
                title="locked"
                style={{ width: 4, height: 4, background: tokens.warn, borderRadius: '50%' }}
              />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function Code({ tabs, lines }: { tabs: string[]; lines: string[] }) {
  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
      <div
        style={{
          display: 'flex',
          borderBottom: `1px solid ${tokens.border}`,
          background: tokens.surface,
          alignItems: 'center',
          flexShrink: 0,
        }}
      >
        {tabs.map((t, i) => {
          const on = i === 0;
          return (
            <div
              key={t}
              style={{
                padding: '8px 14px',
                fontFamily: tokens.mono,
                fontSize: 12,
                background: on ? '#fff' : 'transparent',
                color: on ? tokens.ink : tokens.muted,
                borderTop: on ? `2px solid ${tokens.accent}` : '2px solid transparent',
                borderRight: `1px solid ${tokens.border}`,
                display: 'flex',
                alignItems: 'center',
                gap: 6,
              }}
            >
              <Icon name="doc" size={11} stroke={on ? tokens.ink : tokens.muted} />
              {t}
              {on && (
                <span
                  style={{
                    width: 4,
                    height: 4,
                    background: tokens.accent,
                    borderRadius: '50%',
                    marginLeft: 4,
                  }}
                />
              )}
            </div>
          );
        })}
        <span style={{ flex: 1 }} />
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '0 10px' }}>
          <span className="ag-mono" style={{ fontSize: 11, color: tokens.muted }}>
            agents/researcher.py · {lines.length} lines
          </span>
          <span style={{ width: 1, height: 14, background: tokens.border }} />
          <Icon name="wand" size={12} stroke={tokens.muted} />
          <span className="ag-mono" style={{ fontSize: 11, color: tokens.ink2 }}>regen</span>
          <span style={{ width: 1, height: 14, background: tokens.border }} />
          <Icon name="cog" size={12} stroke={tokens.muted} />
          <span className="ag-mono" style={{ fontSize: 11, color: tokens.ink2 }}>lock</span>
        </div>
      </div>

      <div style={{ flex: 1, overflow: 'auto', display: 'flex', minHeight: 0 }}>
        <div
          style={{
            padding: '12px 0',
            textAlign: 'right',
            fontFamily: tokens.mono,
            fontSize: 11.5,
            color: tokens.faint,
            lineHeight: 1.6,
            borderRight: `1px solid ${tokens.border}`,
            minWidth: 36,
            flexShrink: 0,
          }}
        >
          {lines.map((_, i) => (
            <div key={i} style={{ padding: '0 8px' }}>
              {i + 1}
            </div>
          ))}
        </div>
        <pre
          className="ag-mono"
          style={{
            flex: 1,
            margin: 0,
            padding: '12px 14px',
            fontSize: 11.5,
            lineHeight: 1.6,
            color: tokens.ink2,
            whiteSpace: 'pre',
          }}
        >
          {SAMPLE_FILE_BODY}
          <span className="ag-cursor" />
        </pre>
      </div>
    </div>
  );
}
