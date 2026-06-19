// Batch 0 — loading / error convention for typed API reads.
//
// Wraps an async endpoint call so every page renders consistent loading / error /
// empty states instead of bespoke try/catch. Cancels stale results on unmount or when
// `deps` change, and exposes `reload()` for retry.

import { useCallback, useEffect, useRef, useState } from 'react';
import type { ApiError } from './api';

export type AsyncStatus = 'idle' | 'loading' | 'success' | 'error';

export interface AsyncState<T> {
  data: T | null;
  error: (ApiError | Error) | null;
  status: AsyncStatus;
  loading: boolean;
  reload: () => void;
}

export function useAsync<T>(fn: () => Promise<T>, deps: readonly unknown[] = []): AsyncState<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<(ApiError | Error) | null>(null);
  const [status, setStatus] = useState<AsyncStatus>('idle');
  const [tick, setTick] = useState(0);
  const fnRef = useRef(fn);
  fnRef.current = fn;

  const reload = useCallback(() => setTick((t) => t + 1), []);

  useEffect(() => {
    let active = true;
    setStatus('loading');
    setError(null);
    fnRef.current()
      .then((res) => {
        if (!active) return;
        setData(res);
        setStatus('success');
      })
      .catch((err: ApiError | Error) => {
        if (!active) return;
        setError(err);
        setStatus('error');
      });
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tick, ...deps]);

  return { data, error, status, loading: status === 'loading', reload };
}
