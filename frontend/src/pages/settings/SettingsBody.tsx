// Shared settings tab body — rendered by both the modal (opened from the
// AdminAccountMenu) and the full /settings route, so the tab content stays
// in one place. All seven tabs in `SETTINGS_TABS` are wired here.

import { AccountSettings } from './Account';
import { DataControlsSettings } from './DataControls';
import { DefaultsSettings } from './Defaults';
import { GeneralSettings } from './General';
import { ProvidersSettings } from './Providers';
import { ShortcutsSettings } from './Shortcuts';
import { TemplatesSettings } from './Templates';

interface Props {
  tabId: string;
}

export function SettingsBody({ tabId }: Props) {
  switch (tabId) {
    case 'general':
      return <GeneralSettings />;
    case 'account':
      return <AccountSettings />;
    case 'providers':
      return <ProvidersSettings />;
    case 'templates':
      return <TemplatesSettings />;
    case 'defaults':
      return <DefaultsSettings />;
    case 'shortcuts':
      return <ShortcutsSettings />;
    case 'data':
      return <DataControlsSettings />;
    default:
      return <GeneralSettings />;
  }
}
