// Batch 2 — load the real compatibility catalogue from the backend.
//
// `/api/compatibility/catalogue` is the single source of truth for the wizard facets
// (frameworks, models, hyperscalers, patterns). The wizard renders from it when reachable
// and falls back to the bundled static catalogue otherwise, so the demo never breaks.

import { endpoints } from '@/lib/endpoints';
import { useAsync } from '@/lib/useAsync';
import type { Catalogue } from '@/lib/api-types';

export interface CatalogueState {
  catalogue: Catalogue | null;
  loading: boolean;
  /** true once the backend catalogue has loaded — facets render from it. */
  ready: boolean;
  /** Ids the backend currently offers, for gating the static facet UI. */
  frameworkIds: Set<string> | null;
  modelIds: Set<string> | null;
}

export function useCatalogue(): CatalogueState {
  const { data, loading } = useAsync<Catalogue>(() => endpoints.compatibility.catalogue(), []);
  return {
    catalogue: data,
    loading,
    ready: !!data,
    frameworkIds: data ? new Set(data.frameworks.map((f) => String(f.id))) : null,
    modelIds: data ? new Set(data.models.map((m) => String(m.id))) : null,
  };
}
