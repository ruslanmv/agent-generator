// Runtime adapter preview — generic template that renders for any export
// target. HomePilot is the canonical example (autonomy radio + brand mark);
// other adapters (e.g. watsonx) reuse the same shell with different presets.

import { useState } from 'react';
import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { Button } from '@/components/primitives/Button';
import { StagePillBadge } from '@/components/primitives/Pill';
import { HomePilotMark } from '@/components/icons/Logo';
import {
  ADAPTER_DEPENDENCIES,
  ADAPTER_PERMISSIONS,
  ADAPTER_PRESETS,
  AUTONOMY_OPTIONS,
  type AdapterPreset,
  type AutonomyMode,
  type DependencyStatus,
} from '@/lib/export-data';

interface Props {
  adapterId: string;
  onClose: () => void;
  onInstall: () => void;
}

export function RuntimeAdapterModal({ adapterId, onClose, onInstall }: Props) {
  const preset: AdapterPreset = ADAPTER_PRESETS[adapterId] ?? ADAPTER_PRESETS.homepilot;
  const [autonomy, setAutonomy] = useState<AutonomyMode>('ask');

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={`Install via ${preset.name} adapter`}
      onClick={onClose}
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(22,22,22,.45)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 60,
        padding: 24,
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          width: 840,
          maxHeight: '100%',
          background: '#fff',
          boxShadow: '0 30px 80px rgba(0,0,0,.3)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
      >
        <Header preset={preset} onClose={onClose} />

        <div style={{ flex: 1, overflow: 'auto', padding: 24 }}>
          <Identity preset={preset} />

          <SectionTitle>Dependency status</SectionTitle>
          <DependencyList />

          {preset.autonomy && (
            <>
              <SectionTitle>Autonomy</SectionTitle>
              <AutonomyPicker value={autonomy} onChange={setAutonomy} />
            </>
          )}

          <SectionTitle>Permissions</SectionTitle>
          <PermissionList />
        </div>

        <Footer preset={preset} onClose={onClose} onInstall={onInstall} />
      </div>
    </div>
  );
}

function Header({ preset, onClose }: { preset: AdapterPreset; onClose: () => void }) {
  return (
    <div
      style={{
        padding: '18px 24px',
        borderBottom: `1px solid ${tokens.border}`,
        display: 'flex',
        alignItems: 'center',
        gap: 14,
        flexShrink: 0,
      }}
    >
      {preset.mark === 'hp' ? (
        <HomePilotMark size={40} />
      ) : (
        <div
          style={{
            width: 40,
            height: 40,
            border: `1px solid ${tokens.border}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Icon name="cube" size={18} stroke={tokens.ink} />
        </div>
      )}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <h3 style={{ margin: 0, fontSize: 16, fontWeight: 500 }}>
            Install via {preset.name} adapter
          </h3>
          <StagePillBadge stage="beta" />
          <span className="ag-mono ag-small" style={{ color: tokens.muted }}>{preset.schema}</span>
        </div>
        <div className="ag-small" style={{ marginTop: 2 }}>
          Runtime adapter preview · same template renders for any export target.
        </div>
      </div>
      <button
        type="button"
        aria-label="Close"
        onClick={onClose}
        style={{
          background: 'transparent',
          border: 'none',
          padding: 4,
          cursor: 'pointer',
          color: tokens.muted,
        }}
      >
        <Icon name="x" size={14} />
      </button>
    </div>
  );
}

function Identity({ preset }: { preset: AdapterPreset }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 22 }}>
      <div>
        <div className="ag-cap" style={{ marginBottom: 6 }}>Agent</div>
        <div style={{ fontSize: 17, fontWeight: 500 }}>Daily Research Digest</div>
        <div className="ag-small" style={{ marginTop: 4 }}>
          Monitors arXiv, summarizes papers, prepares a daily digest.
        </div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        <Field label="Runtime"   value={preset.runtime} />
        <Field label="Framework" value="CrewAI 0.74" />
        <Field label="Language"  value="Python 3.11" />
        <Field label="License"   value="Apache-2.0" />
      </div>
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="ag-cap" style={{ marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 13, fontWeight: 500, color: tokens.ink }}>{value}</div>
    </div>
  );
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return <div className="ag-cap" style={{ marginBottom: 8, marginTop: 18 }}>{children}</div>;
}

function statusColor(s: DependencyStatus): string {
  if (s === 'ok') return tokens.ok;
  if (s === 'warn') return tokens.warn;
  return tokens.err;
}

function statusGlyph(s: DependencyStatus): string {
  if (s === 'ok') return '✓';
  if (s === 'warn') return '⚠';
  return '✕';
}

function DependencyList() {
  return (
    <div style={{ border: `1px solid ${tokens.border}`, marginBottom: 4 }}>
      {ADAPTER_DEPENDENCIES.map((d, i) => (
        <div
          key={d.label}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '9px 14px',
            borderBottom:
              i < ADAPTER_DEPENDENCIES.length - 1 ? `1px solid ${tokens.border}` : 'none',
          }}
        >
          <span
            style={{
              width: 16,
              textAlign: 'center',
              fontFamily: tokens.mono,
              fontSize: 13,
              fontWeight: 600,
              color: statusColor(d.status),
            }}
          >
            {statusGlyph(d.status)}
          </span>
          <span className="ag-mono" style={{ fontSize: 13, fontWeight: 500 }}>{d.label}</span>
          <span style={{ flex: 1 }} />
          <span className="ag-small" style={{ color: tokens.muted }}>{d.note}</span>
        </div>
      ))}
    </div>
  );
}

function AutonomyPicker({ value, onChange }: { value: AutonomyMode; onChange: (m: AutonomyMode) => void }) {
  return (
    <div
      role="radiogroup"
      style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8, marginBottom: 4 }}
    >
      {AUTONOMY_OPTIONS.map((o) => {
        const on = o.id === value;
        return (
          <button
            key={o.id}
            type="button"
            role="radio"
            aria-checked={on}
            onClick={() => onChange(o.id)}
            style={{
              padding: 12,
              border: `1px solid ${on ? tokens.ink : tokens.border}`,
              background: on ? tokens.surface : '#fff',
              textAlign: 'left',
              cursor: 'pointer',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span
                style={{
                  width: 12,
                  height: 12,
                  borderRadius: '50%',
                  border: `1px solid ${on ? tokens.ink : tokens.borderStrong}`,
                  background: on ? tokens.ink : '#fff',
                  position: 'relative',
                }}
              >
                {on && (
                  <span
                    style={{
                      position: 'absolute',
                      inset: 3,
                      background: '#fff',
                      borderRadius: '50%',
                    }}
                  />
                )}
              </span>
              <span style={{ fontSize: 13, fontWeight: 500 }}>{o.label}</span>
            </div>
            <div className="ag-small" style={{ marginTop: 6 }}>{o.blurb}</div>
          </button>
        );
      })}
    </div>
  );
}

function PermissionList() {
  return (
    <div style={{ border: `1px solid ${tokens.border}` }}>
      {ADAPTER_PERMISSIONS.map((p, i) => (
        <div
          key={p.label}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '9px 14px',
            borderBottom:
              i < ADAPTER_PERMISSIONS.length - 1 ? `1px solid ${tokens.border}` : 'none',
          }}
        >
          <span
            style={{
              width: 14,
              textAlign: 'center',
              fontFamily: tokens.mono,
              fontSize: 13,
              fontWeight: 600,
              color: statusColor(p.status),
            }}
          >
            {statusGlyph(p.status)}
          </span>
          <span style={{ flex: 1, fontSize: 13 }}>{p.label}</span>
          <span
            className="ag-mono"
            style={{
              padding: '3px 8px',
              fontSize: 11,
              background:
                p.status === 'no' ? '#fdecee' : p.status === 'warn' ? '#fcf4d6' : '#defbe6',
              color:
                p.status === 'no'
                  ? '#a2191f'
                  : p.status === 'warn'
                    ? '#684e00'
                    : '#0e6027',
            }}
          >
            {p.value}
          </span>
        </div>
      ))}
    </div>
  );
}

function Footer({
  preset,
  onClose,
  onInstall,
}: {
  preset: AdapterPreset;
  onClose: () => void;
  onInstall: () => void;
}) {
  return (
    <div
      style={{
        padding: '14px 24px',
        borderTop: `1px solid ${tokens.border}`,
        background: tokens.surface,
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        flexShrink: 0,
      }}
    >
      <Icon name="cog" size={13} stroke={tokens.muted} />
      <span className="ag-mono ag-small" style={{ color: tokens.muted, overflow: 'hidden', textOverflow: 'ellipsis' }}>
        {preset.location}
      </span>
      <span style={{ flex: 1 }} />
      <Button variant="ghost" size="sm">
        <Icon name="play" size={13} /> Dry-run first
      </Button>
      <Button variant="ghost" size="sm" onClick={onClose}>
        Cancel
      </Button>
      <Button variant="primary" size="sm" onClick={onInstall}>
        <Icon name="check" size={13} stroke="#fff" /> Install
      </Button>
    </div>
  );
}
