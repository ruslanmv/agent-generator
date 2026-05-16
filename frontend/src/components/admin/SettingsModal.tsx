// Settings modal — Claude/ChatGPT-style: left tab rail with the admin
// identity at the bottom, right content area. Reuses the same SettingsBody
// the full /settings page uses, so adding a new tab updates both surfaces.

import { useState } from 'react';
import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { ABOUT, ADMIN, SETTINGS_TABS } from '@/lib/settings-data';
import { SettingsBody } from '@/pages/settings/SettingsBody';

interface Props {
  initialTab?: string;
  onClose: () => void;
}

export function SettingsModal({ initialTab = 'general', onClose }: Props) {
  const [tab, setTab] = useState(initialTab);
  const active = SETTINGS_TABS.find((t) => t.id === tab) ?? SETTINGS_TABS[0];

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Settings"
      onClick={onClose}
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(22,22,22,.45)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 60,
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          width: 920,
          height: 620,
          background: '#fff',
          boxShadow: '0 30px 80px rgba(0,0,0,.3)',
          display: 'flex',
          overflow: 'hidden',
        }}
      >
        <TabRail value={tab} onChange={setTab} />

        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
          <div
            style={{
              height: 48,
              borderBottom: `1px solid ${tokens.border}`,
              display: 'flex',
              alignItems: 'center',
              padding: '0 20px',
              flexShrink: 0,
            }}
          >
            <h3 style={{ margin: 0, fontSize: 15, fontWeight: 500 }}>{active.label}</h3>
            <span style={{ flex: 1 }} />
            <button
              type="button"
              aria-label="Close"
              onClick={onClose}
              style={{
                width: 28,
                height: 28,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: tokens.muted,
                cursor: 'pointer',
                background: 'transparent',
                border: 'none',
              }}
            >
              <Icon name="x" size={14} />
            </button>
          </div>
          <div style={{ flex: 1, padding: '24px 28px', overflow: 'auto' }}>
            <SettingsBody tabId={tab} />
          </div>
        </div>
      </div>
    </div>
  );
}

function TabRail({ value, onChange }: { value: string; onChange: (id: string) => void }) {
  return (
    <div
      style={{
        width: 220,
        background: tokens.surface,
        borderRight: `1px solid ${tokens.border}`,
        padding: '20px 0',
        display: 'flex',
        flexDirection: 'column',
        flexShrink: 0,
      }}
    >
      <div className="ag-cap" style={{ padding: '0 20px 12px' }}>Settings</div>
      {SETTINGS_TABS.map((t) => {
        const on = value === t.id;
        return (
          <button
            key={t.id}
            type="button"
            onClick={() => onChange(t.id)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              padding: '8px 20px',
              fontSize: 13,
              background: on ? '#fff' : 'transparent',
              borderLeft: `2px solid ${on ? tokens.accent : 'transparent'}`,
              borderTop: 'none',
              borderRight: 'none',
              borderBottom: 'none',
              fontWeight: on ? 500 : 400,
              color: on ? tokens.ink : tokens.ink2,
              cursor: 'pointer',
              fontFamily: 'inherit',
              textAlign: 'left',
            }}
          >
            <Icon name={t.icon} size={13} stroke={on ? tokens.ink : tokens.muted} />
            <span>{t.label}</span>
          </button>
        );
      })}
      <span style={{ flex: 1 }} />
      <div style={{ padding: '12px 20px', borderTop: `1px solid ${tokens.border}` }}>
        <div className="ag-mono ag-small" style={{ color: tokens.muted }}>{ADMIN.email}</div>
        <div className="ag-mono ag-small" style={{ color: tokens.faint, marginTop: 2 }}>
          {ABOUT.version} · self-hosted
        </div>
      </div>
    </div>
  );
}
