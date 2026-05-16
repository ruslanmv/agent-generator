// Design tokens for Agent Generator.
// Aesthetic: clean enterprise light. Sharp corners (0–2px), tight grid,
// neutral palette with a single deep cobalt accent.
//
// These are the source of truth. CSS variables in global.css are derived
// from this object so component code can pick the form that fits best.

export const tokens = {
  // Surfaces
  bg: '#ffffff',
  surface: '#f4f4f4',
  surface2: '#e8e8e8',
  border: '#dcdcdc',
  borderStrong: '#c6c6c6',

  // Ink
  ink: '#161616',
  ink2: '#393939',
  ink3: '#525252',
  muted: '#6f6f6f',
  faint: '#a8a8a8',

  // Accent (cobalt) + supports
  accent: '#0a3df0',
  accentHi: '#dbe4ff',
  accentDim: '#001d6c',

  // Status
  ok: '#198038',
  warn: '#b28600',
  err: '#da1e28',

  // Console
  termBg: '#0d0d0d',
  termInk: '#e6e6e6',
  termDim: '#8d8d8d',
  termOk: '#42be65',
  termAcc: '#78a9ff',
  termWarn: '#f1c21b',
  termErr: '#fa4d56',

  // Type
  sans: '"IBM Plex Sans", "Helvetica Neue", Helvetica, Arial, sans-serif',
  serif: '"IBM Plex Serif", Georgia, serif',
  mono: '"IBM Plex Mono", "JetBrains Mono", ui-monospace, Menlo, monospace',
} as const;

export type Tokens = typeof tokens;

// Curated accents for the theming tweak panel (Batch 8 will wire this up).
export const ACCENTS = [
  { id: 'cobalt', label: 'Cobalt', value: '#0a3df0', dim: '#001d6c', hi: '#dbe4ff' },
  { id: 'teal', label: 'Teal', value: '#007d79', dim: '#004144', hi: '#9ef0f0' },
  { id: 'magenta', label: 'Magenta', value: '#a8327d', dim: '#510224', hi: '#ffd6e8' },
  { id: 'amber', label: 'Amber', value: '#b28600', dim: '#684e00', hi: '#fcf4d6' },
  { id: 'graphite', label: 'Graphite', value: '#393939', dim: '#161616', hi: '#e8e8e8' },
] as const;

export type AccentId = (typeof ACCENTS)[number]['id'];
