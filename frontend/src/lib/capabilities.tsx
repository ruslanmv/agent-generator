// Batch 9 — de-demo: replace the compile-time `IS_DEMO` constant with a runtime
// capability check.
//
// The SPA can be served by either the demo Space backend (`space_app`, no auth / volatile
// store) or the full self-hosted backend. Rather than hard-coding "demo" from the build
// channel, we probe the backend once on boot and decide:
//
//   * the demo backend stamps every response with `x-agent-generator-channel: hf-space`;
//   * the demo has no `/api/auth/*`, so `/api/auth/me` returns 404 there;
//   * a real backend answers `/api/auth/me` with 200 (signed in) or 401 (anon).
//
// So: demo === (channel header is hf-space) OR (auth route is missing). When the probe
// can't reach the backend we keep the compile-time default to avoid a misleading flip.

import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react';
import { apiUrl } from './api';
import { IS_DEMO as COMPILE_IS_DEMO } from './build-channel';

export interface Capabilities {
  /** True when the backend is the reduced public demo. */
  demo: boolean;
  /** True once the runtime probe has resolved. */
  ready: boolean;
}

const CapabilitiesContext = createContext<Capabilities>({
  demo: COMPILE_IS_DEMO,
  ready: false,
});

export function CapabilitiesProvider({ children }: { children: ReactNode }) {
  // Seed with the compile-time guess so the first paint matches the most likely
  // outcome (demo build → demo, web build → real) and rarely needs to flip.
  const [caps, setCaps] = useState<Capabilities>({ demo: COMPILE_IS_DEMO, ready: false });

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const res = await fetch(apiUrl('/api/auth/me'), { credentials: 'include' });
        const channel = res.headers.get('x-agent-generator-channel');
        const demo = channel === 'hf-space' || res.status === 404;
        if (active) setCaps({ demo, ready: true });
      } catch {
        // Backend unreachable — trust the build-time default.
        if (active) setCaps({ demo: COMPILE_IS_DEMO, ready: true });
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  return (
    <CapabilitiesContext.Provider value={caps}>{children}</CapabilitiesContext.Provider>
  );
}

export function useCapabilities(): Capabilities {
  return useContext(CapabilitiesContext);
}

/** Runtime replacement for the old `IS_DEMO` constant. */
export function useIsDemo(): boolean {
  return useContext(CapabilitiesContext).demo;
}
