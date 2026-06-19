// Batch 0 — typed contracts mirroring the backend (backend/app/api/*.py).
// One place for every request/response shape the typed endpoints use.

export type Visibility = 'private' | 'unlisted' | 'public';
export type DiagnosticSeverity = 'ok' | 'warn' | 'err';
export type PatternSupport = 'native' | 'adapter' | 'unsupported';

// ── auth ────────────────────────────────────────────────────────────────────
export interface UserOut {
  id: string;
  provider: string;
  username: string;
  email: string | null;
  avatar_url: string | null;
  role: string;
}
export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// ── health ──────────────────────────────────────────────────────────────────
export interface HealthResponse {
  status: string;
  [k: string]: unknown;
}

// ── projects ────────────────────────────────────────────────────────────────
export interface FileIn {
  path: string;
  content: string;
}
export interface FileOut extends FileIn {
  id: string;
}
export interface ProjectIn {
  name: string;
  description?: string | null;
  framework: string;
  hyperscaler?: string | null;
  pattern?: string | null;
  model?: string | null;
  state?: Record<string, unknown> | null;
  visibility?: Visibility;
  files?: FileIn[];
}
export type ProjectPatch = Partial<ProjectIn>;
export interface ProjectOut {
  id: string;
  owner_id: string;
  name: string;
  description: string | null;
  framework: string;
  hyperscaler: string | null;
  pattern: string | null;
  model: string | null;
  state: Record<string, unknown> | null;
  visibility: Visibility;
  files: FileOut[];
  created_at: string;
  updated_at: string;
}

// ── runs ────────────────────────────────────────────────────────────────────
export interface RunStartIn {
  prompt?: string | null;
}
export interface RunOut {
  id: string;
  project_id: string;
  owner_id: string;
  status: string;
  prompt: string | null;
  error: string | null;
  created_at: string;
  updated_at: string;
}
/** A single run event as replayed over REST (`GET /api/runs/{id}/events`) or streamed
 *  over the WebSocket (`/ws/runs/{id}`). */
export interface RunEventOut {
  seq: number;
  kind: string;
  payload: Record<string, unknown>;
  created_at: string;
}

// ── compatibility (wizard / marketplace facets) ───────────────────────────────
/** Facet items (frameworks / hyperscalers / models / patterns) are refined by the
 *  wizard in Batch 2; typed loosely here so the catalogue is usable everywhere. */
export interface CatalogueFacetItem {
  id: string;
  label?: string;
  [k: string]: unknown;
}
export interface Catalogue {
  hyperscalers: CatalogueFacetItem[];
  frameworks: CatalogueFacetItem[];
  orchestration_patterns: CatalogueFacetItem[];
  models: CatalogueFacetItem[];
  export_by_framework: Record<string, string[] | '*'>;
  pattern_by_framework: Record<string, Record<string, PatternSupport>>;
}
export interface DiagnoseIn {
  framework?: string | null;
  hyperscaler?: string | null;
  pattern?: string | null;
  model?: string | null;
  [k: string]: unknown;
}
export interface Diagnostic {
  category: string;
  value: string;
  sub: string;
  severity: DiagnosticSeverity;
  step: number;
}

// ── marketplace ───────────────────────────────────────────────────────────────
export interface MarketplaceAgent {
  id: string;
  name: string;
  description: string;
  framework: string;
  hyperscalers: string[];
  author: string;
  downloads: number;
  tags: string[];
}
export interface PublishIn {
  project_id: string;
  name?: string | null;
  description?: string | null;
  tags?: string[];
}
export interface PublishOut {
  id: string;
  url: string | null;
  status: string;
}

// ── OllaBridge ────────────────────────────────────────────────────────────────
export interface PairIn {
  project_id: string;
  server_url?: string | null;
  [k: string]: unknown;
}
export interface PairOut {
  project_id: string;
  server_url: string;
  paired: boolean;
}
export interface OllaBridgeStatus {
  project_id: string;
  paired: boolean;
  server_url: string | null;
}

// ── secrets (project-scoped) ──────────────────────────────────────────────────
export interface SecretIn {
  value: string;
}
export interface SecretOut {
  key: string;
  version: number;
}
export interface SecretValueOut {
  key: string;
  value: string;
}

// ── docker builds ─────────────────────────────────────────────────────────────
export interface DockerBuildIn {
  project_id: string;
  image: string;
  push?: boolean;
  platforms?: string[];
}
export interface DockerBuildOut {
  build_id: string;
  mode: string;
  image: string;
  status: string;
  stream_url: string;
}
