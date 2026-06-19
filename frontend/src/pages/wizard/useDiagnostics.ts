// Batch 2 — incompatible combos flagged by the BACKEND.
//
// Posts the wizard's compatibility state to `/api/compatibility/diagnose` and renders the
// diagnostics the backend returns (its `Diagnostic` shape is identical to the card's). The
// local `compatibilityFor()` result is shown instantly and as a fail-open fallback so the
// card never blocks on the network.

import { useEffect, useRef, useState } from 'react';

import { endpoints } from '@/lib/endpoints';
import {
  compatibilityFor,
  type Diagnostic,
  type WizardCompatibilityState,
} from '@/lib/compatibility';

export interface DiagnosticsResult {
  rows: Diagnostic[];
  /** Where the rows came from — useful for a small "checked by backend" hint. */
  source: 'backend' | 'local';
}

export function useDiagnostics(state: WizardCompatibilityState): DiagnosticsResult {
  const [rows, setRows] = useState<Diagnostic[]>(() => compatibilityFor(state));
  const [source, setSource] = useState<'backend' | 'local'>('local');
  const key = JSON.stringify(state);
  const keyRef = useRef(key);
  keyRef.current = key;

  useEffect(() => {
    // Instant local result, then upgrade to the backend's verdict when it answers.
    setRows(compatibilityFor(state));
    setSource('local');
    let active = true;
    endpoints.compatibility
      .diagnose(state as unknown as Record<string, unknown>)
      .then((d) => {
        if (active && keyRef.current === key && Array.isArray(d) && d.length) {
          setRows(d as Diagnostic[]);
          setSource('backend');
        }
      })
      .catch(() => {
        /* fail-open: keep the local diagnostics */
      });
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  return { rows, source };
}
