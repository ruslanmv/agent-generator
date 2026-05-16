import { tokens } from '@/styles/tokens';
import { Icon, type IconName } from '@/components/icons/Icon';

export interface NavItem {
  id: string;
  label: string;
  icon?: IconName;
  count?: number;
}

interface NavProps {
  items: NavItem[];
  value: string;
  onChange?: (id: string) => void;
  vertical?: boolean;
  dense?: boolean;
}

export function Nav({ items, value, onChange, vertical = false, dense = false }: NavProps) {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: vertical ? 'column' : 'row',
        gap: vertical ? 0 : 4,
        borderTop: vertical ? `1px solid ${tokens.border}` : 0,
      }}
    >
      {items.map((it) => {
        const on = value === it.id;
        return (
          <button
            key={it.id}
            type="button"
            onClick={() => onChange?.(it.id)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              padding: dense ? '6px 10px' : '10px 14px',
              cursor: 'pointer',
              borderLeft: vertical ? `2px solid ${on ? tokens.accent : 'transparent'}` : 'none',
              borderBottom: vertical
                ? `1px solid ${tokens.border}`
                : `2px solid ${on ? tokens.ink : 'transparent'}`,
              borderTop: 'none',
              borderRight: 'none',
              background: vertical && on ? tokens.surface : 'transparent',
              color: on ? tokens.ink : tokens.ink3,
              fontSize: 13,
              fontWeight: on ? 500 : 400,
              textAlign: 'left',
              fontFamily: 'inherit',
              width: vertical ? '100%' : 'auto',
            }}
          >
            {it.icon && <Icon name={it.icon} size={14} stroke={on ? tokens.ink : tokens.muted} />}
            <span>{it.label}</span>
            {it.count != null && (
              <span className="ag-num" style={{ marginLeft: 'auto', fontSize: 11, color: tokens.muted }}>
                {it.count}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
