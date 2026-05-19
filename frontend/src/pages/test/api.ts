// Test-surface API bindings.
//
// `listAgents()`  → GET /api/projects             (existing endpoint)
// `chat()`        → POST /api/test/chat           (new — runs LLM inference)
// `listModels()`  → GET /api/ollabridge/models    (new — picks up the
//                                                  pairing-session token)

import { api } from '@/lib/api';
import type { ChatMessage, TestAgent } from './types';

interface ProjectSummary {
  id: string;
  prompt: string;
  framework: string;
  file_count: number;
}

const FRAMEWORK_LABELS: Record<string, string> = {
  crewai: 'crewai',
  crewai_flow: 'crewai-flow',
  langgraph: 'langgraph',
  react: 'react',
  watsonx_orchestrate: 'wxo',
  watsonx: 'wxo',
  autogen: 'autogen',
  llamaindex: 'llamaindex',
};

function projectToAgent(p: ProjectSummary): TestAgent {
  // A short slug becomes the visible name. Fallback to id if the
  // wizard didn't set a prompt (shouldn't happen in practice).
  const slug = p.prompt
    ? p.prompt
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '-')
        .slice(0, 24)
        .replace(/-+$/, '')
    : p.id.slice(0, 8);
  return {
    id: p.id,
    name: slug || p.id.slice(0, 8),
    framework: FRAMEWORK_LABELS[p.framework] ?? p.framework,
    tools: p.file_count,
    status: 'ready',
  };
}

export async function listAgents(): Promise<TestAgent[]> {
  try {
    const rows = await api.get<ProjectSummary[]>('/api/projects');
    return rows.map(projectToAgent);
  } catch {
    return [];
  }
}

export interface ChatRequest {
  agent_id?: string;
  messages: { role: ChatMessage['role']; content: string }[];
  model?: string;
  system_prompt?: string;
  temperature?: number;
  max_tokens?: number;
}

export interface ChatResponse {
  role: 'assistant';
  content: string;
  model: string;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  elapsed_ms: number;
}

export async function chat(req: ChatRequest): Promise<ChatResponse> {
  return api.post<ChatResponse>('/api/test/chat', req);
}

export async function listInferenceModels(): Promise<string[]> {
  try {
    const r = await api.get<{ models: string[] }>('/api/ollabridge/models');
    return r.models;
  } catch {
    return [];
  }
}
