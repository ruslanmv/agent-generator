// Shortcuts tab — keyboard map. Read-only for now; a future iteration
// will let users rebind keys.

import { tokens } from '@/styles/tokens';
import { Pill } from '@/components/primitives/Pill';
import { SettingSection } from '@/pages/wizard/review/SettingsRow';

interface ShortcutRow {
  keys: string[];
  action: string;
}

const NAVIGATION: ShortcutRow[] = [
  { keys: ['⌘', 'K'], action: 'Open command palette' },
  { keys: ['⌘', 'P'], action: 'Switch project / agent' },
  { keys: ['⌘', ','], action: 'Open settings' },
  { keys: ['G', 'G'], action: 'Go to Generate' },
  { keys: ['G', 'R'], action: 'Go to Run' },
  { keys: ['G', 'T'], action: 'Go to Test' },
  { keys: ['G', 'M'], action: 'Go to Marketplace' },
];

const WIZARD: ShortcutRow[] = [
  { keys: ['⌘', '↵'], action: 'Send / advance to next step' },
  { keys: ['⌘', '⇧', 'G'], action: 'Generate without confirmation' },
  { keys: ['⌘', 'Z'], action: 'Undo last wizard change' },
  { keys: ['Esc'], action: 'Close modal / cancel pending action' },
];

const TEST: ShortcutRow[] = [
  { keys: ['⌘', '↵'], action: 'Send message' },
  { keys: ['⌘', '⇧', '↵'], action: 'Send + run live trace' },
  { keys: ['⌘', '/'], action: 'Toggle the right inspector' },
  { keys: ['⌘', 'L'], action: 'Clear conversation' },
];

export function ShortcutsSettings() {
  return (
    <div>
      <p className="ag-body" style={{ color: tokens.ink3, marginBottom: 24, maxWidth: 720 }}>
        Keyboard map. Custom bindings ship in a follow-up release.
      </p>

      <SettingSection label="Navigation">
        <KeyList rows={NAVIGATION} />
      </SettingSection>
      <SettingSection label="Wizard">
        <KeyList rows={WIZARD} />
      </SettingSection>
      <SettingSection label="Test surface">
        <KeyList rows={TEST} />
      </SettingSection>

      <div
        style={{
          padding: 16,
          background: tokens.surface,
          border: `1px solid ${tokens.border}`,
          marginTop: 8,
        }}
      >
        <div style={{ fontSize: 13, color: tokens.ink2 }}>
          On macOS, <Key>⌘</Key> is the Command key. On Windows and Linux it maps to{' '}
          <Key>Ctrl</Key>; <Key>⇧</Key> is <Key>Shift</Key>, <Key>↵</Key> is{' '}
          <Key>Enter</Key>.
        </div>
      </div>
    </div>
  );
}

function KeyList({ rows }: { rows: ShortcutRow[] }) {
  return (
    <div style={{ border: `1px solid ${tokens.border}`, background: '#fff' }}>
      {rows.map((r, i) => (
        <div
          key={`${r.action}-${i}`}
          style={{
            display: 'flex',
            alignItems: 'center',
            padding: '12px 18px',
            borderBottom: i < rows.length - 1 ? `1px solid ${tokens.border}` : 0,
          }}
        >
          <span style={{ flex: 1, fontSize: 13.5, color: tokens.ink }}>{r.action}</span>
          <span style={{ display: 'inline-flex', gap: 4 }}>
            {r.keys.map((k, j) => (
              <span key={`${k}-${j}`} style={{ display: 'inline-flex', gap: 4 }}>
                <Key>{k}</Key>
                {j < r.keys.length - 1 && (
                  <span style={{ color: tokens.faint, fontSize: 11, alignSelf: 'center' }}>
                    +
                  </span>
                )}
              </span>
            ))}
          </span>
        </div>
      ))}
    </div>
  );
}

function Key({ children }: { children: React.ReactNode }) {
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        minWidth: 22,
        height: 22,
        padding: '0 6px',
        fontFamily: tokens.mono,
        fontSize: 11,
        color: tokens.ink,
        background: '#fff',
        border: `1px solid ${tokens.borderStrong}`,
        boxShadow: '0 1px 0 rgba(0,0,0,.06)',
      }}
    >
      {children}
    </span>
  );
}

function PillRow() {
  return <Pill>shortcuts</Pill>; // keeps Pill import warm for future use
}
void PillRow;
