// Batch 8 — load a project and derive its pipeline graph.
//
// Fetches `GET /api/projects/{id}` and runs `derivePipeline`. Fails open to the bundled
// seed when there is no project id or the fetch fails, so the editor always renders.

import { api } from '@/lib/api';
import { useAsync } from '@/lib/useAsync';
import {
  derivePipeline,
  type DerivedPipeline,
  type RawProject,
} from '@/lib/pipeline-derive';

export function usePipeline(projectId: string | null): DerivedPipeline & { loading: boolean } {
  const { data, loading } = useAsync<RawProject | null>(async () => {
    if (!projectId) return null;
    try {
      return await api.get<RawProject>(`/api/projects/${encodeURIComponent(projectId)}`);
    } catch {
      return null;
    }
  }, [projectId]);

  return { ...derivePipeline(data), loading };
}
