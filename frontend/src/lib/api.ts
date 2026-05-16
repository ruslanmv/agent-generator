// Minimal API client.
//
// One source of truth for the backend base URL + auth header. The web
// shell uses the same-origin convention (the nginx Dockerfile reverse-
// proxies /api/* to the backend); the desktop/mobile shells set
// `VITE_API_URL` at build time to point at the production backend.

const API_BASE = (import.meta.env.VITE_API_URL ?? '').replace(/\/$/, '');

export function apiUrl(path: string): string {
  return `${API_BASE}${path.startsWith('/') ? path : `/${path}`}`;
}

export function wsUrl(path: string): string {
  const base = API_BASE;
  if (!base) {
    // Same-origin fallback.
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${proto}//${location.host}${path}`;
  }
  return base.replace(/^http/, 'ws') + path;
}

const TOKEN_KEY = 'ag.access_token';

export function setAccessToken(token: string | null): void {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

export function getAccessToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

function authHeaders(): HeadersInit {
  const token = getAccessToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export interface ApiError extends Error {
  status: number;
  body: unknown;
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
): Promise<T> {
  const res = await fetch(apiUrl(path), {
    method,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  let payload: unknown;
  try {
    payload = await res.json();
  } catch {
    payload = null;
  }
  if (!res.ok) {
    const err: ApiError = Object.assign(
      new Error(`API ${method} ${path} failed: ${res.status}`),
      { status: res.status, body: payload },
    );
    throw err;
  }
  return payload as T;
}

export const api = {
  get: <T>(path: string) => request<T>('GET', path),
  post: <T>(path: string, body?: unknown) => request<T>('POST', path, body),
  patch: <T>(path: string, body?: unknown) => request<T>('PATCH', path, body),
  del: <T>(path: string) => request<T>('DELETE', path),
};
