// Marketplace — orchestrates Browse vs Detail. Selection lives in local
// state so the URL stays at /marketplace; Batch 8 will lift this into the
// router once the catalog API is wired.

import { useState } from 'react';
import { MarketplaceBrowse } from './marketplace/Browse';
import { MarketplaceDetail } from './marketplace/Detail';
import { MH_ITEMS } from '@/lib/marketplace-data';

export function MarketplacePage() {
  const [openId, setOpenId] = useState<string | null>(null);
  const item = openId ? MH_ITEMS.find((i) => i.id === openId) ?? null : null;

  if (item) {
    return <MarketplaceDetail item={item} onBack={() => setOpenId(null)} />;
  }
  return <MarketplaceBrowse onOpen={setOpenId} />;
}
