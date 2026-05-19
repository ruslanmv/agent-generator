// HF publisher API binding. All endpoints live under /api/hf/*.

import { api } from '@/lib/api';

export interface HFStatus {
  connected: boolean;
  username: string | null;
  namespaces: string[];
}

export interface ValidateRequest {
  namespace: string;
  space_name: string;
  sdk: 'gradio' | 'docker' | 'streamlit' | 'static';
  visibility: 'public' | 'private';
  required_tools: string[];
}

export interface ValidateResponse {
  available: boolean;
  warnings: string[];
  required_secrets: string[];
}

export interface PublishRequest {
  project_id: string;
  namespace: string;
  space_name: string;
  sdk: ValidateRequest['sdk'];
  visibility: ValidateRequest['visibility'];
  enable_agents_md: boolean;
  enable_mcp: boolean;
  require_hf_token: boolean;
  secrets: Record<string, string>;
  dry_run: boolean;
}

export interface PublishResponse {
  status: 'published' | 'would-publish';
  space_url: string;
  agents_url: string;
  api_info_url: string;
  files_pushed: number;
  repo_id: string;
  dry_run: boolean;
}

export const hfApi = {
  status: () => api.get<HFStatus>('/api/hf/status'),
  connect: (token: string) =>
    api.post<HFStatus>('/api/hf/connect', { token }),
  disconnect: () => api.post<HFStatus>('/api/hf/disconnect'),
  validate: (body: ValidateRequest) =>
    api.post<ValidateResponse>('/api/hf/validate-space', body),
  publish: (body: PublishRequest) =>
    api.post<PublishResponse>('/api/hf/publish', body),
};
