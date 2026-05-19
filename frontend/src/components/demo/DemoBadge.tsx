// "DEMO" pill rendered in the top bar when the SPA is built for the
// Hugging Face Space. Visible to users so they understand persistence
// and auth are intentionally off.
//
// The component renders nothing in non-demo builds, so callers can
// drop it inline without an `if` at every call site.

import { IS_DEMO } from '@/lib/build-channel';
import { tokens } from '@/styles/tokens';

interface Props {
  /** Tooltip override. Defaults to a self-explanatory message. */
  title?: string;
}

const DEFAULT_TITLE =
  'Running on Hugging Face Spaces. Sign-in and project history are disabled in demo mode.';

export function DemoBadge({ title = DEFAULT_TITLE }: Props) {
  if (!IS_DEMO) return null;
  return (
    <span
      title={title}
      aria-label="Demo mode"
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        height: 20,
        padding: '0 8px',
        fontFamily: tokens.mono,
        fontSize: 10,
        fontWeight: 600,
        letterSpacing: '.08em',
        textTransform: 'uppercase',
        color: '#fff',
        background: tokens.accent,
        borderRadius: 0,
      }}
    >
      Demo
    </span>
  );
}
