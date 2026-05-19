// Model access section — promotes OllaBridge to a first-class
// **gateway** choice (default) instead of just a model option, and
// surfaces the OpenAI-compatible aliases the gateway exposes. When
// the user switches to "Direct provider", the existing ModelRow
// below renders the per-vendor model cards (OpenAI / Anthropic /
// watsonx / Ollama / OllaBridge) untouched.

import type { ReactNode } from 'react';
import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { Pill } from '@/components/primitives/Pill';

export type ModelAccess = 'ollabridge' | 'direct';

interface Props {
  access: ModelAccess;
  alias: string;
  onAccessChange: (next: ModelAccess) => void;
  onAliasChange: (next: string) => void;
}

interface AliasOption {
  id: string;
  label: string;
  description: string;
}

export const OLLABRIDGE_ALIASES: AliasOption[] = [
  { id: 'local-private', label: 'local-private', description: 'on-device · private' },
  { id: 'free-best', label: 'free-best', description: 'highest quality · free' },
  { id: 'free-fast', label: 'free-fast', description: 'low latency · free' },
  { id: 'free-flex', label: 'free-flex', description: 'balanced · free' },
  { id: 'cheap-reasoning', label: 'cheap-reasoning', description: 'low $ · reasoning' },
];

export function ModelAccessRow({ access, alias, onAccessChange, onAliasChange }: Props) {
  return (
    <>
      <div className="ag-cap" style={{ marginTop: 28, marginBottom: 10 }}>
        Model access
      </div>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(2, 1fr)',
          gap: 8,
          marginBottom: 14,
        }}
      >
        <AccessCard
          selected={access === 'ollabridge'}
          onSelect={() => onAccessChange('ollabridge')}
          mark={<OllaBridgeMark size={26} />}
          label="OllaBridge"
          subtitle="OpenAI-compatible gateway · MCP-ready"
          showDefault
        />
        <AccessCard
          selected={access === 'direct'}
          onSelect={() => onAccessChange('direct')}
          mark={
            <div
              style={{
                width: 26,
                height: 26,
                background: tokens.surface,
                border: `1px solid ${tokens.border}`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Icon name="llm" size={14} stroke={tokens.ink2} />
            </div>
          }
          label="Direct provider"
          subtitle="OpenAI · Anthropic · watsonx · Ollama"
        />
      </div>

      {access === 'ollabridge' && (
        <>
          <div className="ag-cap" style={{ marginBottom: 10 }}>
            Model alias
          </div>
          <div
            role="radiogroup"
            aria-label="OllaBridge model alias"
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(5, 1fr)',
              gap: 6,
              marginBottom: 24,
            }}
          >
            {OLLABRIDGE_ALIASES.map((a) => {
              const on = a.id === alias;
              return (
                <button
                  key={a.id}
                  type="button"
                  role="radio"
                  aria-checked={on}
                  onClick={() => onAliasChange(a.id)}
                  style={{
                    padding: '8px 10px',
                    border: `${on ? 2 : 1}px solid ${on ? tokens.ink : tokens.border}`,
                    background: on ? tokens.surface : '#fff',
                    cursor: 'pointer',
                    textAlign: 'left',
                    fontFamily: 'inherit',
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 4,
                      marginBottom: 2,
                    }}
                  >
                    <span className="ag-mono" style={{ fontSize: 12, fontWeight: 500 }}>
                      {a.label}
                    </span>
                    {on && <Icon name="check" size={10} stroke={tokens.ink} />}
                  </div>
                  <div
                    className="ag-small"
                    style={{ fontSize: 10.5, color: tokens.muted }}
                  >
                    {a.description}
                  </div>
                </button>
              );
            })}
          </div>
        </>
      )}
    </>
  );
}

interface AccessCardProps {
  selected: boolean;
  onSelect: () => void;
  mark: ReactNode;
  label: string;
  subtitle: string;
  showDefault?: boolean;
}

function AccessCard({ selected, onSelect, mark, label, subtitle, showDefault }: AccessCardProps) {
  return (
    <button
      type="button"
      onClick={onSelect}
      style={{
        position: 'relative',
        padding: 12,
        border: `${selected ? 2 : 1}px solid ${selected ? tokens.ink : tokens.border}`,
        background: selected ? tokens.surface : '#fff',
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        textAlign: 'left',
        cursor: 'pointer',
        fontFamily: 'inherit',
      }}
    >
      {mark}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontSize: 13, fontWeight: 500 }}>{label}</span>
          {showDefault && selected && <Pill variant="accent">default</Pill>}
        </div>
        <div
          className="ag-mono ag-small"
          style={{ fontSize: 10.5, color: tokens.muted, marginTop: 2 }}
        >
          {subtitle}
        </div>
      </div>
      {selected && <Icon name="check" size={12} stroke={tokens.ink} />}
    </button>
  );
}

function OllaBridgeMark({ size = 26 }: { size?: number }) {
  // Geometric arch over two anchor blocks — neutral cobalt mark.
  return (
    <span
      aria-hidden
      style={{
        width: size,
        height: size,
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#fff',
        border: `1px solid ${tokens.border}`,
        flexShrink: 0,
      }}
    >
      <svg width={size - 6} height={size - 6} viewBox="0 0 24 24" fill="none">
        <rect x="3" y="14" width="5" height="6" fill={tokens.accent} />
        <rect x="16" y="14" width="5" height="6" fill={tokens.accent} />
        <path
          d="M5.5 14 A8 8 0 0 1 18.5 14"
          stroke={tokens.accent}
          strokeWidth="2"
          fill="none"
          strokeLinecap="round"
        />
      </svg>
    </span>
  );
}
