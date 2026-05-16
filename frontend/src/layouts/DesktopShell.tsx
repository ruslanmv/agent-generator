// DesktopShell — top-level chrome shared across screens.
// Side rail (icon nav + admin profile) + top bar + content slot.
// AdminAccountMenu / SettingsModal / AboutModal anchor here so they can
// overlay any page.

import { useState, type ReactNode } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { tokens } from '@/styles/tokens';
import { Icon, type IconName } from '@/components/icons/Icon';
import { AgentGeneratorMark } from '@/components/icons/Logo';
import { Pill } from '@/components/primitives/Pill';
import { AdminAccountMenu, type AdminMenuAction } from '@/components/admin/AdminAccountMenu';
import { AboutModal } from '@/components/admin/AboutModal';
import { SettingsModal } from '@/components/admin/SettingsModal';
import { ADMIN } from '@/lib/settings-data';

interface RailItem {
  id: string;
  label: string;
  path: string;
  icon: IconName;
}

const RAIL: RailItem[] = [
  { id: 'generate',    label: 'Generate',    path: '/generate',    icon: 'spark' },
  { id: 'pipeline',    label: 'Pipeline',    path: '/pipeline',    icon: 'flow' },
  { id: 'run',         label: 'Run',         path: '/run',         icon: 'play' },
  { id: 'projects',    label: 'Projects',    path: '/projects',    icon: 'folder' },
  { id: 'marketplace', label: 'Marketplace', path: '/marketplace', icon: 'cube' },
  { id: 'settings',    label: 'Settings',    path: '/settings',    icon: 'cog' },
];

type Overlay = 'menu' | 'settings' | 'about' | null;

interface DesktopShellProps {
  children: ReactNode;
  projectName?: string;
  running?: { elapsed: string } | null;
}

export function DesktopShell({ children, projectName = 'untitled', running }: DesktopShellProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const [overlay, setOverlay] = useState<Overlay>(null);

  const activeId =
    RAIL.find((r) => location.pathname === r.path || location.pathname.startsWith(r.path + '/'))?.id ??
    'generate';

  const handleMenuAction = (action: AdminMenuAction) => {
    if (action === 'about') setOverlay('about');
    else if (action === 'settings') setOverlay('settings');
    else if (action === 'help') {
      window.open('https://github.com/ruslanmv/agent-generator', '_blank');
      setOverlay(null);
    } else if (action === 'logout') {
      // Wired to a real auth provider in Batch 8.
      setOverlay(null);
    }
  };

  return (
    <div
      style={{
        height: '100vh',
        display: 'flex',
        background: tokens.bg,
        position: 'relative',
        color: tokens.ink,
      }}
    >
      <aside
        style={{
          width: 56,
          background: tokens.ink,
          color: '#fff',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          padding: '12px 0 8px',
          flexShrink: 0,
        }}
      >
        <div
          style={{
            width: 32,
            height: 32,
            marginBottom: 14,
            background: '#fff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            overflow: 'hidden',
            flexShrink: 0,
          }}
        >
          <AgentGeneratorMark size={32} inverse />
        </div>

        <nav style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%' }}>
          {RAIL.map((it) => {
            const on = activeId === it.id;
            return (
              <button
                key={it.id}
                type="button"
                title={it.label}
                aria-label={it.label}
                aria-current={on ? 'page' : undefined}
                onClick={() => navigate(it.path)}
                style={{
                  width: 40,
                  height: 40,
                  marginBottom: 4,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                  background: on ? '#262626' : 'transparent',
                  borderLeft: `2px solid ${on ? tokens.accent : 'transparent'}`,
                  borderTop: 'none',
                  borderRight: 'none',
                  borderBottom: 'none',
                  color: on ? '#fff' : '#a8a8a8',
                  cursor: 'pointer',
                }}
              >
                <Icon name={it.icon} size={18} stroke="currentColor" />
              </button>
            );
          })}
        </nav>

        <div
          style={{
            width: '100%',
            borderTop: '1px solid #2a2a2a',
            paddingTop: 8,
            display: 'flex',
            justifyContent: 'center',
            flexShrink: 0,
          }}
        >
          <button
            type="button"
            title={`${ADMIN.name} — ${ADMIN.email}`}
            aria-label="Account menu"
            aria-expanded={overlay === 'menu'}
            onClick={() => setOverlay(overlay === 'menu' ? null : 'menu')}
            style={{
              width: 36,
              height: 36,
              borderRadius: '50%',
              background: overlay === 'menu' ? '#3d3d3d' : '#525252',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontFamily: tokens.mono,
              fontSize: 12,
              color: '#fff',
              cursor: 'pointer',
              border: overlay === 'menu' ? `2px solid ${tokens.accent}` : '2px solid transparent',
            }}
          >
            {ADMIN.initials}
          </button>
        </div>
      </aside>

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        <header
          style={{
            height: 48,
            borderBottom: `1px solid ${tokens.border}`,
            display: 'flex',
            alignItems: 'center',
            padding: '0 20px',
            gap: 16,
            flexShrink: 0,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span className="ag-mono" style={{ fontSize: 12, color: tokens.muted }}>agent‑generator</span>
            <span style={{ color: tokens.faint }}>/</span>
            <span style={{ fontSize: 13, fontWeight: 500 }}>{projectName}</span>
            <span style={{ marginLeft: 6 }}>
              <Pill>v0.4.2</Pill>
            </span>
          </div>
          <div style={{ flex: 1 }} />
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                padding: '4px 10px',
                border: `1px solid ${tokens.border}`,
              }}
            >
              <Icon name="search" size={13} stroke={tokens.muted} />
              <span className="ag-mono" style={{ fontSize: 12, color: tokens.faint }}>⌘K</span>
            </div>
            {running && (
              <Pill variant="ok">
                <span style={{ width: 6, height: 6, background: tokens.ok, borderRadius: '50%' }} />
                run · {running.elapsed}
              </Pill>
            )}
            <button
              type="button"
              aria-label="Notifications"
              style={{
                width: 32,
                height: 32,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: tokens.ink2,
                background: 'transparent',
                border: 'none',
                cursor: 'pointer',
              }}
            >
              <Icon name="bell" size={16} />
            </button>
          </div>
        </header>

        <main style={{ flex: 1, overflow: 'auto', minHeight: 0 }}>{children}</main>
      </div>

      {overlay === 'menu' && (
        <AdminAccountMenu
          onAction={handleMenuAction}
          onClose={() => setOverlay(null)}
        />
      )}
      {overlay === 'settings' && <SettingsModal onClose={() => setOverlay(null)} />}
      {overlay === 'about' && <AboutModal onClose={() => setOverlay(null)} />}
    </div>
  );
}
