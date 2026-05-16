// Shared settings tab body — rendered by both the modal (opened from the
// AdminAccountMenu) and the full /settings route, so the tab content stays
// in one place.

import { tokens } from '@/styles/tokens';
import { GeneralSettings } from './General';
import { ProvidersSettings } from './Providers';

interface Props {
  tabId: string;
}

export function SettingsBody({ tabId }: Props) {
  if (tabId === 'general') return <GeneralSettings />;
  if (tabId === 'providers') return <ProvidersSettings />;
  return <ComingSoon tabId={tabId} />;
}

function ComingSoon({ tabId }: { tabId: string }) {
  return (
    <div className="ag-body" style={{ color: tokens.muted, padding: '8px 0' }}>
      The <span className="ag-mono" style={{ color: tokens.ink }}>{tabId}</span> tab arrives in a
      follow-up batch. General and Providers are wired today.
    </div>
  );
}
