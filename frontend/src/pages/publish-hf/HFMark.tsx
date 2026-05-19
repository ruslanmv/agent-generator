// Hugging Face mark — geometric smiley, single SVG, no network.

import { tokens } from '@/styles/tokens';

interface Props {
  size?: number;
}

export function HFMark({ size = 24 }: Props) {
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
        <circle cx="12" cy="12" r="9" fill="#ffd200" />
        <circle cx="9" cy="11" r="1.2" fill="#161616" />
        <circle cx="15" cy="11" r="1.2" fill="#161616" />
        <path
          d="M8 14 q 4 4 8 0"
          stroke="#161616"
          strokeWidth="1.4"
          fill="none"
          strokeLinecap="round"
        />
      </svg>
    </span>
  );
}
