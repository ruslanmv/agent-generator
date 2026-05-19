// Generator wizard API bindings.
//
// `planPrompt` hits POST /api/plan with `use_llm: true` so Step 1's
// "Generate" button does real LLM-backed planning (defaults to the
// public OllaBridge tier on the demo Space). The returned spec is
// folded back into the wizard state so steps 2-4 land pre-populated.
//
// `generateProject` hits POST /api/generate at the end of Review v2
// — gets the full artifact bundle, persists it server-side, and
// returns the new project's id so the SPA can route to its detail
// page.

import { api, type ApiError } from '@/lib/api';
import type { FrameworkId } from '@/lib/frameworks';
import type { LlmProvider } from '@/lib/wizard-data';

/** Subset of `agent_generator.domain.ProjectSpec` the wizard reads. */
export interface PlannedSpec {
  name?: string;
  framework?: string;
  artifact_mode?: string;
  agents?: { id?: string; role?: string; goal?: string; tools?: string[] }[];
  tools?: { id?: string; template?: string }[];
  llm?: { provider?: string; model?: string };
}

export interface PlanResponse {
  spec: PlannedSpec;
  warnings: string[];
}

export interface GenerateResponse {
  id: string;
  spec: PlannedSpec;
  artifacts: {
    files?: Record<string, string>;
    manifest?: Record<string, unknown>;
    warnings?: string[];
  };
  warnings: string[];
}

interface PlanRequest {
  prompt: string;
  framework?: FrameworkId | null;
  provider?: LlmProvider | null;
  use_llm: boolean;
}

export async function planPrompt(req: PlanRequest): Promise<PlanResponse> {
  return api.post<PlanResponse>('/api/plan', req);
}

interface GenerateRequest {
  prompt: string;
  framework?: FrameworkId | null;
  provider?: LlmProvider | null;
  use_llm: boolean;
}

export async function generateProject(req: GenerateRequest): Promise<GenerateResponse> {
  return api.post<GenerateResponse>('/api/generate', req);
}

/** Pull a friendly message out of an `ApiError` thrown by `api`. */
export function readApiError(err: unknown): string {
  const e = err as Partial<ApiError>;
  const body = e?.body as { detail?: string | unknown[] } | undefined;
  if (typeof body?.detail === 'string') return body.detail;
  if (Array.isArray(body?.detail) && body.detail.length > 0) {
    const first = body.detail[0] as { msg?: string };
    if (first?.msg) return first.msg;
  }
  return e?.message ?? 'Request failed';
}
