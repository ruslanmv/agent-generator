// Batch 7 — OllaBridge gateway client.
//
// OllaBridge is the preferred OpenAI-compatible gateway: one endpoint that fronts local
// Ollama models, remote nodes, and the public OllaBridge Cloud Space. The Providers
// settings screen pairs a device (or Cloud) here and the wizard/run select it as the
// active model provider.
//
// These hit the Space's process-global routes (`/api/ollabridge/*`); the full backend
// exposes the same verbs project-scoped. All calls fail soft at the call site so the
// settings UI degrades gracefully when the gateway is unreachable.

import { api } from './api';

export interface OllaBridgeStatus {
  paired: boolean;
  server_url: string | null;
}

export interface OllaBridgePairResult {
  paired: boolean;
  server_url: string;
}

export interface OllaBridgeModels {
  models: string[];
}

export const ollabridge = {
  /** Exchange a device pairing code (shown in the OllaBridge app) for a session token. */
  pair: (code: string, serverUrl?: string) =>
    api.post<OllaBridgePairResult>('/api/ollabridge/pair', {
      code,
      server_url: serverUrl ?? null,
    }),
  /** Is the gateway paired, and against which server URL? */
  status: () => api.get<OllaBridgeStatus>('/api/ollabridge/status'),
  /** Forget the stored pairing token. */
  unpair: () => api.post<OllaBridgeStatus>('/api/ollabridge/unpair'),
  /** Models reachable through the paired (or configured) gateway. */
  models: () => api.get<OllaBridgeModels>('/api/ollabridge/models'),
};
