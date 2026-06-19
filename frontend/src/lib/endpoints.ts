// Batch 0 — typed client: one method per backend route, built on the `api` client.
//
// This is the single typed surface the pages should call instead of the static
// `*-data.ts` fixtures. The JWT/session is threaded automatically by `api` (it sends
// `credentials: 'include'` for the session cookie and an `Authorization: Bearer` header
// when a token is stored). Paths mirror backend/app/api/*.py exactly.

import { api, apiUrl, wsUrl } from './api';
import type * as T from './api-types';

export const endpoints = {
  health: {
    livez: () => api.get<T.HealthResponse>('/livez'),
    readyz: () => api.get<T.HealthResponse>('/readyz'),
  },

  auth: {
    me: () => api.get<T.UserOut>('/api/auth/me'),
    refresh: (refresh_token: string) =>
      api.post<T.TokenPair>('/api/auth/refresh', { refresh_token }),
    logout: () => api.post<{ status: string }>('/api/auth/logout'),
    /** Full URL to start the GitHub OAuth bounce; navigate the browser to it. */
    githubLoginUrl: (next = '/') =>
      apiUrl(`/api/auth/github/login?next=${encodeURIComponent(next)}`),
  },

  compatibility: {
    catalogue: () => api.get<T.Catalogue>('/api/compatibility/catalogue'),
    diagnose: (body: T.DiagnoseIn) =>
      api.post<T.Diagnostic[]>('/api/compatibility/diagnose', body),
  },

  projects: {
    list: () => api.get<T.ProjectOut[]>('/api/projects'),
    create: (body: T.ProjectIn) => api.post<T.ProjectOut>('/api/projects', body),
    get: (id: string) => api.get<T.ProjectOut>(`/api/projects/${id}`),
    patch: (id: string, body: T.ProjectPatch) =>
      api.patch<T.ProjectOut>(`/api/projects/${id}`, body),
  },

  runs: {
    get: (id: string) => api.get<T.RunOut>(`/api/runs/${id}`),
    /** Start a run on a project; returns the run header. */
    start: (projectId: string, body: T.RunStartIn) =>
      api.post<T.RunOut>(`/api/projects/${projectId}/runs`, body),
    /** Replay persisted events (seq > after) over REST. */
    events: (id: string, after = -1) =>
      api.get<T.RunEventOut[]>(`/api/runs/${id}/events?after=${after}`),
    /** WebSocket URL for the live run event stream. */
    streamUrl: (id: string, after = -1) => wsUrl(`/ws/runs/${id}?after=${after}`),
  },

  marketplace: {
    agents: () => api.get<T.MarketplaceAgent[]>('/api/marketplace/agents'),
    agent: (id: string) => api.get<T.MarketplaceAgent>(`/api/marketplace/agents/${id}`),
    publish: (body: T.PublishIn) => api.post<T.PublishOut>('/api/marketplace/publish', body),
  },

  ollabridge: {
    /** Pair a project with OllaBridge Cloud or a local OllaBridge node. */
    pair: (body: T.PairIn) => api.post<T.PairOut>('/api/ollabridge/pair', body),
    status: (projectId: string) =>
      api.get<T.OllaBridgeStatus>(`/api/ollabridge/status/${projectId}`),
  },

  secrets: {
    list: (projectId: string) =>
      api.get<T.SecretOut[]>(`/api/projects/${projectId}/secrets`),
    get: (projectId: string, key: string) =>
      api.get<T.SecretValueOut>(`/api/projects/${projectId}/secrets/${key}`),
  },

  builds: {
    docker: (body: T.DockerBuildIn) =>
      api.post<T.DockerBuildOut>('/api/builds/docker', body),
    /** WebSocket URL for the live docker build log stream. */
    streamUrl: (buildId: string) => wsUrl(`/ws/builds/${buildId}`),
  },
};

export type Endpoints = typeof endpoints;
