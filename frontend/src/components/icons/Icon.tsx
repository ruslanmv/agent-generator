// Geometric inline icons. Stroke-based, 16x16 grid. Keep them simple — no
// complex artwork, no fills outside the few that need it (play/dot/kebab).

import type { CSSProperties } from 'react';

export type IconName =
  | 'arrow' | 'arrow-l' | 'plus' | 'check' | 'x'
  | 'play' | 'pause' | 'dot' | 'square' | 'grid' | 'list'
  | 'flow' | 'spark' | 'cube' | 'wand' | 'cog'
  | 'folder' | 'doc' | 'download' | 'search' | 'bell'
  | 'kebab' | 'menu' | 'chev-d' | 'chev-r'
  | 'agent' | 'tool' | 'llm' | 'link' | 'send' | 'history' | 'star';

interface IconProps {
  name: IconName;
  size?: number;
  stroke?: string;
  style?: CSSProperties;
  className?: string;
  title?: string;
}

export function Icon({ name, size = 16, stroke = 'currentColor', style, className, title }: IconProps) {
  const sw = 1.4;
  const common = {
    width: size,
    height: size,
    viewBox: '0 0 16 16',
    fill: 'none' as const,
    stroke,
    strokeWidth: sw,
    strokeLinecap: 'round' as const,
    strokeLinejoin: 'round' as const,
    style,
    className,
    role: title ? 'img' : 'presentation',
    'aria-label': title,
  };

  switch (name) {
    case 'arrow':    return <svg {...common}><path d="M3 8h10M9 4l4 4-4 4" /></svg>;
    case 'arrow-l':  return <svg {...common}><path d="M13 8H3M7 4 3 8l4 4" /></svg>;
    case 'plus':     return <svg {...common}><path d="M8 3v10M3 8h10" /></svg>;
    case 'check':    return <svg {...common}><path d="M3 8.5 6.5 12 13 5" /></svg>;
    case 'x':        return <svg {...common}><path d="M4 4l8 8M12 4l-8 8" /></svg>;
    case 'play':     return <svg {...common}><path d="M5 3v10l8-5z" fill={stroke} /></svg>;
    case 'pause':    return <svg {...common}><path d="M5 3v10M11 3v10" /></svg>;
    case 'dot':      return <svg {...common}><circle cx="8" cy="8" r="3" fill={stroke} /></svg>;
    case 'square':   return <svg {...common}><rect x="3" y="3" width="10" height="10" /></svg>;
    case 'grid':     return <svg {...common}><rect x="3" y="3" width="4" height="4" /><rect x="9" y="3" width="4" height="4" /><rect x="3" y="9" width="4" height="4" /><rect x="9" y="9" width="4" height="4" /></svg>;
    case 'list':     return <svg {...common}><path d="M3 4h10M3 8h10M3 12h10" /></svg>;
    case 'flow':     return <svg {...common}><circle cx="3.5" cy="4" r="1.6" /><circle cx="3.5" cy="12" r="1.6" /><circle cx="12.5" cy="8" r="1.6" /><path d="M5 4h2.5a3 3 0 0 1 3 3M5 12h2.5a3 3 0 0 0 3-3" /></svg>;
    case 'spark':    return <svg {...common}><path d="M8 2v4M8 10v4M2 8h4M10 8h4M4 4l2 2M10 10l2 2M12 4l-2 2M4 12l2-2" /></svg>;
    case 'cube':     return <svg {...common}><path d="M8 2 2.5 5v6L8 14l5.5-3V5L8 2zM2.5 5 8 8l5.5-3M8 8v6" /></svg>;
    case 'wand':     return <svg {...common}><path d="M3 13 12 4M11 3l2 2" /></svg>;
    case 'cog':      return <svg {...common}><circle cx="8" cy="8" r="2.2" /><path d="M8 2v2M8 12v2M2 8h2M12 8h2M3.8 3.8l1.4 1.4M10.8 10.8l1.4 1.4M3.8 12.2l1.4-1.4M10.8 5.2l1.4-1.4" /></svg>;
    case 'folder':   return <svg {...common}><path d="M2 5a1 1 0 0 1 1-1h3l1.5 1.5H13a1 1 0 0 1 1 1V12a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V5z" /></svg>;
    case 'doc':      return <svg {...common}><path d="M4 2h6l3 3v9H4V2zM10 2v3h3" /></svg>;
    case 'download': return <svg {...common}><path d="M8 2v8M4 7l4 4 4-4M3 13h10" /></svg>;
    case 'search':   return <svg {...common}><circle cx="7" cy="7" r="4" /><path d="m13 13-3-3" /></svg>;
    case 'bell':     return <svg {...common}><path d="M4 11V8a4 4 0 1 1 8 0v3l1 1.5H3L4 11zM6.5 13.5a1.5 1.5 0 0 0 3 0" /></svg>;
    case 'kebab':    return <svg {...common}><circle cx="8" cy="3.5" r=".8" fill={stroke} /><circle cx="8" cy="8" r=".8" fill={stroke} /><circle cx="8" cy="12.5" r=".8" fill={stroke} /></svg>;
    case 'menu':     return <svg {...common}><path d="M2 4h12M2 8h12M2 12h12" /></svg>;
    case 'chev-d':   return <svg {...common}><path d="m4 6 4 4 4-4" /></svg>;
    case 'chev-r':   return <svg {...common}><path d="m6 4 4 4-4 4" /></svg>;
    case 'agent':    return <svg {...common}><circle cx="8" cy="6" r="2.5" /><path d="M3 14c0-2.8 2.2-5 5-5s5 2.2 5 5" /></svg>;
    case 'tool':     return <svg {...common}><path d="m3 13 5-5M11 5l2 2M9 4l3 3-2 2-3-3 2-2zM3 13v1h1l1-1" /></svg>;
    case 'llm':      return <svg {...common}><circle cx="8" cy="8" r="5" /><path d="M3 8h10M8 3c1.7 1.5 1.7 8.5 0 10M8 3c-1.7 1.5-1.7 8.5 0 10" /></svg>;
    case 'link':     return <svg {...common}><path d="M7 5h-2a3 3 0 0 0 0 6h2M9 11h2a3 3 0 0 0 0-6H9M5.5 8h5" /></svg>;
    case 'send':     return <svg {...common}><path d="m13 3-10 5 4 1.5L9 13l4-10zM7 9.5 13 3" /></svg>;
    case 'history':  return <svg {...common}><path d="M2 8a6 6 0 1 0 1.8-4.3M2 2v3h3M8 5v3l2 2" /></svg>;
    case 'star':     return <svg {...common}><path d="M8 2.5 9.7 6l3.8.5-2.7 2.6.6 3.8L8 11.1 4.6 13l.6-3.8L2.5 6.5 6.3 6 8 2.5z" /></svg>;
  }
}
