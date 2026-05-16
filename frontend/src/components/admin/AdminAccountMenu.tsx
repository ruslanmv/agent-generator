// Admin account menu — popover anchored to the rail's profile button.
// Pattern matches ChatGPT/Claude account menus: identity header, item list,
// danger-coloured Log out separated by a divider, version footer.

import { Fragment, useEffect, useRef } from 'react';
import { tokens } from '@/styles/tokens';
import { Icon, type IconName } from '@/components/icons/Icon';
import { Pill } from '@/components/primitives/Pill';
import { ABOUT, ADMIN } from '@/lib/settings-data';

export type AdminMenuAction = 'about' | 'settings' | 'help' | 'logout';

interface MenuItem {
  id: AdminMenuAction;
  icon: IconName;
  label: string;
  shortcut?: string;
  danger?: boolean;
}

const ITEMS: MenuItem[] = [
  { id: 'about',    icon: 'doc',     label: 'About' },
  { id: 'settings', icon: 'cog',     label: 'Settings', shortcut: '⌘,' },
  { id: 'help',     icon: 'doc',     label: 'Help & docs' },
  { id: 'logout',   icon: 'arrow-l', label: 'Log out', danger: true },
];

interface Props {
  onAction: (action: AdminMenuAction) => void;
  onClose: () => void;
}

export function AdminAccountMenu({ onAction, onClose }: Props) {
  const ref = useRef<HTMLDivElement>(null);

  // Close on outside click or Escape — matches the ChatGPT/Claude pattern.
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    }
    function handleKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose();
    }
    document.addEventListener('mousedown', handleClick);
    document.addEventListener('keydown', handleKey);
    return () => {
      document.removeEventListener('mousedown', handleClick);
      document.removeEventListener('keydown', handleKey);
    };
  }, [onClose]);

  return (
    <div
      ref={ref}
      role="menu"
      aria-label="Admin account menu"
      style={{
        position: 'absolute',
        left: 64,
        bottom: 12,
        width: 280,
        background: '#fff',
        border: `1px solid ${tokens.borderStrong}`,
        boxShadow: '0 16px 40px rgba(0,0,0,.18), 0 2px 6px rgba(0,0,0,.08)',
        zIndex: 50,
      }}
    >
      <div
        style={{
          padding: '14px 14px 12px',
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          borderBottom: `1px solid ${tokens.border}`,
        }}
      >
        <div
          style={{
            width: 40,
            height: 40,
            borderRadius: '50%',
            background: tokens.ink,
            color: '#fff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontFamily: tokens.mono,
            fontSize: 13,
            fontWeight: 500,
            flexShrink: 0,
          }}
        >
          {ADMIN.initials}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 13.5, fontWeight: 500, color: tokens.ink }}>{ADMIN.name}</div>
          <div
            className="ag-mono"
            style={{
              fontSize: 11.5,
              color: tokens.muted,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
          >
            {ADMIN.email}
          </div>
        </div>
        <Pill variant="ok">{ADMIN.role}</Pill>
      </div>

      <div style={{ padding: 6 }}>
        {ITEMS.map((it) => (
          <Fragment key={it.id}>
            {it.danger && (
              <div style={{ height: 1, background: tokens.border, margin: '6px 4px' }} />
            )}
            <button
              type="button"
              role="menuitem"
              onClick={() => onAction(it.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '8px 10px',
                cursor: 'pointer',
                color: it.danger ? tokens.err : tokens.ink,
                background: 'transparent',
                border: 'none',
                width: '100%',
                textAlign: 'left',
                fontFamily: 'inherit',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.background = tokens.surface)}
              onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
            >
              <Icon name={it.icon} size={14} stroke={it.danger ? tokens.err : tokens.ink2} />
              <span style={{ flex: 1, fontSize: 13.5 }}>{it.label}</span>
              {it.shortcut && (
                <span className="ag-mono" style={{ fontSize: 11, color: tokens.faint }}>
                  {it.shortcut}
                </span>
              )}
            </button>
          </Fragment>
        ))}
      </div>

      <div
        style={{
          padding: '8px 14px',
          borderTop: `1px solid ${tokens.border}`,
          display: 'flex',
          alignItems: 'center',
          gap: 8,
        }}
      >
        <span className="ag-mono ag-small" style={{ color: tokens.muted }}>{ABOUT.version}</span>
        <span style={{ flex: 1 }} />
        <span className="ag-mono ag-small" style={{ color: tokens.faint }}>self-hosted</span>
      </div>
    </div>
  );
}
