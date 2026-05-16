// Platform dispatcher — picks the right adapter at module load and
// exposes one ergonomic surface to the rest of the app.
//
// Usage:
//
//   import { platform } from '@/lib/platform';
//   await platform.secureStore.set('ag.token', tok);
//   await platform.notify.send('Build complete', '21.4s · 142 MB');

import type { Platform, PlatformId } from './platform/types';
import { webPlatform } from './platform/web';
import { tauriPlatform } from './platform/tauri';
import { capacitorPlatform } from './platform/capacitor';

function detect(): PlatformId {
  if (typeof window === 'undefined') return 'web';
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  if ((window as any).__TAURI_INTERNALS__) return 'tauri';
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  if ((window as any).Capacitor?.isNativePlatform?.()) return 'capacitor';
  return 'web';
}

const ADAPTERS: Record<PlatformId, Platform> = {
  web:       webPlatform,
  tauri:     tauriPlatform,
  capacitor: capacitorPlatform,
};

export const platform: Platform = ADAPTERS[detect()];

export const { info, fs, kv, secureStore, deepLink, updater, notify, shell } = platform;

export type {
  Platform,
  PlatformId,
  PlatformInfo,
  FsAdapter,
  KvAdapter,
  SecureStoreAdapter,
  DeepLinkAdapter,
  UpdaterAdapter,
  NotifyAdapter,
  ShellAdapter,
} from './platform/types';

export const isWeb       = () => platform.info.id === 'web';
export const isTauri     = () => platform.info.id === 'tauri';
export const isCapacitor = () => platform.info.id === 'capacitor';
export const isDesktop   = () => platform.info.id === 'tauri';
export const isMobile    = () => platform.info.id === 'capacitor';
