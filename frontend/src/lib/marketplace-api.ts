// Batch 5 — Marketplace (Matrix Hub) real reads.
//
// The backend (`/api/marketplace/agents`, `/agents/{id}`, `/publish`) brokers the
// Matrix Hub catalogue. Its `MarketplaceAgent` shape is leaner than the rich
// `MarketplaceItem` the Browse/Detail UI renders, so we adapt one to the other and
// fail open to the bundled `MH_ITEMS` fixture whenever the catalogue is unreachable.

import { endpoints } from './endpoints';
import { useAsync } from './useAsync';
import type { MarketplaceAgent, PublishIn, PublishOut } from './api-types';
import { MH_ITEMS, type MarketplaceItem } from './marketplace-data';

/** Compact a download count the way the cards expect (1284 → "1.3k"). */
function formatInstalls(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}m`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return String(n);
}

/** Map a backend catalogue agent onto the UI's richer item shape. The synthetic
 *  `type:id@version` id keeps `packageName()`/`snakeName()` (which split on `:` and
 *  `@`) working unchanged in Detail. */
export function agentToItem(a: MarketplaceAgent): MarketplaceItem {
  return {
    id: `agent:${a.id}@1.0.0`,
    type: 'agent',
    name: a.name,
    org: a.author,
    version: '1.0.0',
    stars: a.downloads,
    installs: formatInstalls(a.downloads),
    summary: a.description,
    capabilities: a.tags,
    frameworks: [a.framework],
    // The catalogue tracks hyperscalers rather than model providers; surface them
    // so the Detail compatibility rail stays informative.
    providers: a.hyperscalers,
    score: Number((0.7 + Math.min(a.downloads, 2000) / 10_000).toFixed(2)),
    verified: a.author === 'agent-generator',
    kind: 'pip',
  };
}

export interface MarketplaceState {
  items: MarketplaceItem[];
  loading: boolean;
  /** 'backend' once the live catalogue answered; 'fixture' while loading or offline. */
  source: 'backend' | 'fixture';
}

/** Load the live catalogue, mapped to UI items. Fail-open to the static fixture so
 *  the page always renders. */
export function useMarketplaceItems(): MarketplaceState {
  const { data, loading } = useAsync<MarketplaceAgent[]>(
    () => endpoints.marketplace.agents(),
    [],
  );
  if (data && data.length) {
    return { items: data.map(agentToItem), loading, source: 'backend' };
  }
  return { items: MH_ITEMS, loading, source: 'fixture' };
}

/** Publish a project to the hub. Returns null on the demo (no `/publish` route) or
 *  any failure so callers can degrade gracefully. */
export async function publishProject(body: PublishIn): Promise<PublishOut | null> {
  try {
    return await endpoints.marketplace.publish(body);
  } catch {
    return null;
  }
}
