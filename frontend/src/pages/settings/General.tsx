import { useState } from 'react';
import { tokens, ACCENTS, type AccentId } from '@/styles/tokens';
import { Toggle } from '@/components/primitives/Toggle';
import { Segmented } from '@/pages/wizard/components/Segmented';
import { useAccent } from '@/lib/accent';

export function GeneralSettings() {
  const [theme, setTheme] = useState<'light' | 'dark' | 'system'>('light');
  const [density, setDensity] = useState<'compact' | 'comfortable'>('comfortable');
  const [language, setLanguage] = useState('English (US)');
  const [workspace, setWorkspace] = useState('./apps');
  const [autoUpdate, setAutoUpdate] = useState(true);
  const [telemetry, setTelemetry] = useState(false);
  const [beta, setBeta] = useState(true);
  const { accent, setAccent } = useAccent();

  return (
    <div>
      <Row
        label="Theme"
        hint="Light is recommended for the enterprise palette."
        control={
          <Segmented<'light' | 'dark' | 'system'>
            value={theme}
            options={['light', 'dark', 'system']}
            onChange={setTheme}
          />
        }
      />
      <Row
        label="Accent"
        hint="Picks the cobalt-strength colour used for primary buttons, focus rings, and selection highlights."
        control={<AccentPicker value={accent} onChange={setAccent} />}
      />
      <Row
        label="Density"
        control={
          <Segmented<'compact' | 'comfortable'>
            value={density}
            options={['compact', 'comfortable']}
            onChange={setDensity}
          />
        }
      />
      <Row
        label="Language"
        control={<TextField value={language} onChange={setLanguage} width={220} />}
      />
      <Row
        label="Default workspace"
        control={<TextField value={workspace} onChange={setWorkspace} width={260} mono />}
      />
      <Row
        label="Auto-update generated projects"
        hint="Pulls minor versions of installed Marketplace items weekly."
        control={<Toggle checked={autoUpdate} onChange={setAutoUpdate} label="Auto-update" />}
      />
      <Row
        label="Telemetry"
        hint="Anonymous usage events. Off by default for self-hosted."
        control={<Toggle checked={telemetry} onChange={setTelemetry} label="Telemetry" />}
      />
      <Row
        label="Beta features"
        hint="Visual pipeline editor v2, voice prompts, AutoGen plugin."
        control={<Toggle checked={beta} onChange={setBeta} label="Beta features" />}
        last
      />
    </div>
  );
}

function AccentPicker({ value, onChange }: { value: AccentId; onChange: (id: AccentId) => void }) {
  return (
    <div role="radiogroup" aria-label="Accent" style={{ display: 'flex', gap: 8 }}>
      {ACCENTS.map((a) => {
        const on = a.id === value;
        return (
          <button
            key={a.id}
            type="button"
            role="radio"
            aria-checked={on}
            aria-label={a.label}
            title={a.label}
            onClick={() => onChange(a.id)}
            style={{
              width: 28,
              height: 28,
              padding: 0,
              border: `2px solid ${on ? tokens.ink : 'transparent'}`,
              boxShadow: on ? `0 0 0 1px #fff inset, 0 0 0 2px ${a.value} inset` : 'none',
              background: a.value,
              cursor: 'pointer',
              borderRadius: 0,
            }}
          />
        );
      })}
    </div>
  );
}

function Row({
  label,
  hint,
  control,
  last,
}: {
  label: string;
  hint?: string;
  control: React.ReactNode;
  last?: boolean;
}) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'flex-start',
        padding: '14px 0',
        borderBottom: last ? 'none' : `1px solid ${tokens.border}`,
        gap: 16,
      }}
    >
      <div style={{ flex: 1, paddingTop: 4 }}>
        <div style={{ fontSize: 13.5, color: tokens.ink, fontWeight: 500, marginBottom: 4 }}>
          {label}
        </div>
        {hint && (
          <div className="ag-small" style={{ color: tokens.muted, lineHeight: 1.5 }}>
            {hint}
          </div>
        )}
      </div>
      <div style={{ flexShrink: 0 }}>{control}</div>
    </div>
  );
}

function TextField({
  value,
  onChange,
  width,
  mono,
}: {
  value: string;
  onChange: (v: string) => void;
  width: number;
  mono?: boolean;
}) {
  return (
    <input
      value={value}
      onChange={(e) => onChange(e.target.value)}
      style={{
        height: 30,
        padding: '0 10px',
        border: `1px solid ${tokens.border}`,
        background: '#fff',
        fontFamily: mono ? tokens.mono : tokens.sans,
        fontSize: 13,
        color: tokens.ink,
        outline: 'none',
        width,
        borderRadius: 0,
      }}
      onFocus={(e) => (e.currentTarget.style.borderColor = tokens.ink)}
      onBlur={(e) => (e.currentTarget.style.borderColor = tokens.border)}
    />
  );
}
