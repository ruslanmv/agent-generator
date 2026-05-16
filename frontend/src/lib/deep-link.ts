// Bridge between the native deep-link router (Rust side, shells/
// desktop/src-tauri/src/deeplink.rs) and the SPA's react-router.
//
// Behaviour:
//   1. Cold launch — the native shell buffers any URL that arrived
//      before the SPA mounted. On startup we drain that queue with the
//      `deeplink_consume_pending` command and replay each path.
//   2. Hot path  — every subsequent deep link fires a `navigate`
//      event with the same `string` payload (an SPA path with optional
//      query / hash). We forward it straight to react-router.
//
// The component is a tiny null renderer so it can sit at the top of
// the React tree and have `useNavigate` in scope.

import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

interface TauriBridge {
  invoke: <T>(cmd: string, args?: Record<string, unknown>) => Promise<T>;
  event: {
    listen: (
      event: string,
      handler: (payload: { payload: string }) => void,
    ) => Promise<() => void>;
  };
}

function tauri(): TauriBridge | null {
  const w = window as unknown as {
    __TAURI__?: TauriBridge;
    __TAURI_INTERNALS__?: unknown;
  };
  return w.__TAURI__ ?? null;
}

export function DeepLinkBridge() {
  const navigate = useNavigate();

  useEffect(() => {
    const t = tauri();
    if (!t) return; // web / mobile shell — no-op

    let unlisten: (() => void) | null = null;

    // 1. Cold-launch drain.
    void t
      .invoke<string[]>('deeplink_consume_pending')
      .then((paths) => paths.forEach((p) => navigate(p)))
      .catch(() => {
        /* command absent in older builds — ignore */
      });

    // 2. Hot path.
    void t.event
      .listen('navigate', (msg) => {
        if (typeof msg.payload === 'string' && msg.payload.startsWith('/')) {
          navigate(msg.payload);
        }
      })
      .then((fn) => {
        unlisten = fn;
      })
      .catch(() => {
        /* ignore */
      });

    return () => {
      if (unlisten) unlisten();
    };
  }, [navigate]);

  return null;
}
