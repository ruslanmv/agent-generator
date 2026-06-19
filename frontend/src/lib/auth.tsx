// Batch 1 — real auth & session.
//
// GitHub OAuth is cookie-based: the backend sets an httpOnly session cookie on
// `/api/auth/github/callback` and bounces back to the app. The API client already sends
// `credentials: 'include'`, so `/api/auth/me` resolves the session with no token handling in JS.
//   • signIn()  → navigate the browser to the GitHub login bounce
//   • signOut() → POST /api/auth/logout, clear any stored token, drop the user
//   • on mount  → GET /api/auth/me to hydrate the session

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react';

import { setAccessToken } from './api';
import { endpoints } from './endpoints';
import type { UserOut } from './api-types';

export type AuthStatus = 'loading' | 'authed' | 'anon';

interface AuthContextValue {
  user: UserOut | null;
  status: AuthStatus;
  signIn: (next?: string) => void;
  signOut: () => Promise<void>;
  reload: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserOut | null>(null);
  const [status, setStatus] = useState<AuthStatus>('loading');

  const reload = useCallback(() => {
    setStatus('loading');
    endpoints.auth
      .me()
      .then((u) => {
        setUser(u);
        setStatus('authed');
      })
      .catch(() => {
        setUser(null);
        setStatus('anon');
      });
  }, []);

  useEffect(() => {
    reload();
  }, [reload]);

  const signIn = useCallback((next?: string) => {
    const target = next ?? window.location.pathname + window.location.search;
    window.location.href = endpoints.auth.githubLoginUrl(target);
  }, []);

  const signOut = useCallback(async () => {
    try {
      await endpoints.auth.logout();
    } catch {
      /* logging out is best-effort; clear the client either way */
    }
    setAccessToken(null);
    setUser(null);
    setStatus('anon');
  }, []);

  return (
    <AuthContext.Provider value={{ user, status, signIn, signOut, reload }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within <AuthProvider>');
  return ctx;
}

/** Two-letter initials for the avatar fallback. */
export function userInitials(user: UserOut | null): string {
  if (!user) return '–';
  const name = user.username || user.email || '?';
  const parts = name.replace(/[^a-zA-Z0-9 ]/g, ' ').trim().split(/\s+/);
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
  return name.slice(0, 2).toUpperCase();
}
