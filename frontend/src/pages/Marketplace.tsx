// Marketplace — orchestrates Browse vs Detail. Selection lives in local
// state so the URL stays at /marketplace.
//
// Batch 5: the catalogue is loaded live from `/api/marketplace/agents`
// (`useMarketplaceItems`) and falls back to the bundled fixture when the
// hub is unreachable, so Browse + Detail render real entries end-to-end.

import { useState } from 'react';
import { MarketplaceBrowse } from './marketplace/Browse';
import { MarketplaceDetail } from './marketplace/Detail';
import { useMarketplaceItems } from '@/lib/marketplace-api';

export function MarketplacePage() {
  const { items, source } = useMarketplaceItems();
  const [openId, setOpenId] = useState<string | null>(null);
  const item = openId ? items.find((i) => i.id === openId) ?? null : null;

  if (item) {
    return <MarketplaceDetail item={item} onBack={() => setOpenId(null)} />;
  }
  return <MarketplaceBrowse items={items} live={source === 'backend'} onOpen={setOpenId} />;
}
