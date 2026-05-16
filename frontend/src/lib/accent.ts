// Theme accent — exposes the curated swatch list from `tokens.ts` and lets
// any component read or change the active accent. The active value is
// mirrored to:
//   1. CSS variables (`--ag-accent`, `--ag-accent-dim`, `--ag-accent-hi`)
//      so global stylesheets and future components can pick it up.
//   2. The `tokens` object's accent fields, so existing inline-style
//      consumers (the bulk of the app) stay in sync.
//   3. `localStorage` under `ag.accent`, so a refresh keeps the choice.

import { useCallback, useEffect, useState } from 'react';
import { ACCENTS, tokens, type AccentId } from '@/styles/tokens';

const STORAGE_KEY = 'ag.accent';

function applyAccent(id: AccentId) {
  const swatch = ACCENTS.find((a) => a.id === id) ?? ACCENTS[0];
  // Mutate the shared tokens object so existing inline styles see the
  // new accent on the next render.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (tokens as any).accent = swatch.value;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (tokens as any).accentDim = swatch.dim;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (tokens as any).accentHi = swatch.hi;

  if (typeof document !== 'undefined') {
    document.documentElement.style.setProperty('--ag-accent', swatch.value);
    document.documentElement.style.setProperty('--ag-accent-dim', swatch.dim);
    document.documentElement.style.setProperty('--ag-accent-hi', swatch.hi);
  }
}

/** Read the persisted accent (or the default cobalt) and apply it before
 * React boots — eliminates the flash of the default accent on first load. */
export function bootAccent(): void {
  if (typeof window === 'undefined') return;
  const stored = window.localStorage.getItem(STORAGE_KEY) as AccentId | null;
  const id =
    stored && ACCENTS.some((a) => a.id === stored) ? stored : ACCENTS[0].id;
  applyAccent(id);
}

export function useAccent(): {
  accent: AccentId;
  setAccent: (id: AccentId) => void;
} {
  const [accent, setAccentState] = useState<AccentId>(() => {
    if (typeof window === 'undefined') return ACCENTS[0].id;
    const stored = window.localStorage.getItem(STORAGE_KEY) as AccentId | null;
    return stored && ACCENTS.some((a) => a.id === stored) ? stored : ACCENTS[0].id;
  });

  useEffect(() => {
    applyAccent(accent);
  }, [accent]);

  const setAccent = useCallback((id: AccentId) => {
    setAccentState(id);
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(STORAGE_KEY, id);
    }
  }, []);

  return { accent, setAccent };
}
