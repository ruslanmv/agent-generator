// Capacitor adapter — Android (Play Store) and iOS-ready. Same lazy
// dynamic-import pattern as the Tauri adapter so the web build doesn't
// pull in the native plugins.

import { webPlatform } from './web';
import type { Platform, PlatformInfo } from './types';

const VERSION = import.meta.env.APP_VERSION ?? '0.0.0-dev';

const lazy = <T>(loader: () => Promise<T>) => {
  let promise: Promise<T> | null = null;
  return () => (promise ??= loader());
};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const prefs       = lazy(() => import(/* @vite-ignore */ '@capacitor/preferences').catch(() => ({} as any)));
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const secure      = lazy(() => import(/* @vite-ignore */ '@aparajita/capacitor-secure-storage').catch(() => ({} as any)));
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const filesystem  = lazy(() => import(/* @vite-ignore */ '@capacitor/filesystem').catch(() => ({} as any)));
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const appPlugin   = lazy(() => import(/* @vite-ignore */ '@capacitor/app').catch(() => ({} as any)));
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const notifPlugin = lazy(() => import(/* @vite-ignore */ '@capacitor/local-notifications').catch(() => ({} as any)));
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const browserPlugin = lazy(() => import(/* @vite-ignore */ '@capacitor/browser').catch(() => ({} as any)));
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const corePlugin  = lazy(() => import(/* @vite-ignore */ '@capacitor/core').catch(() => ({} as any)));

const info: PlatformInfo = { id: 'capacitor', os: 'unknown', appVersion: VERSION };

(async () => {
  try {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const core = (await corePlugin()) as any;
    info.os = core?.Capacitor?.getPlatform?.() ?? 'unknown';
  } catch { /* plugin not installed in dev — leave 'unknown'. */ }
})();

function bytesToBase64(bytes: Uint8Array): string {
  let bin = '';
  for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
  return btoa(bin);
}

function base64ToBytes(b64: string): Uint8Array {
  const bin = atob(b64);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

export const capacitorPlatform: Platform = {
  info,
  fs: {
    async saveFile(name, bytes) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const f = (await filesystem()) as any;
      await f.Filesystem?.writeFile?.({
        path: name,
        data: bytesToBase64(bytes),
        directory: f.Directory?.Documents,
        recursive: true,
      });
      return `Documents/${name}`;
    },
    async openFile() {
      return null;
    },
  },
  kv: {
    async get(k) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const p = (await prefs()) as any;
      const r = await p.Preferences?.get?.({ key: k });
      return r?.value ?? null;
    },
    async set(k, v) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const p = (await prefs()) as any;
      await p.Preferences?.set?.({ key: k, value: v });
    },
    async delete(k) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const p = (await prefs()) as any;
      await p.Preferences?.remove?.({ key: k });
    },
  },
  secureStore: {
    async get(k) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const s = (await secure()) as any;
      return (await s.SecureStorage?.get?.(k)) ?? null;
    },
    async set(k, v) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const s = (await secure()) as any;
      await s.SecureStorage?.set?.(k, v);
    },
    async delete(k) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const s = (await secure()) as any;
      await s.SecureStorage?.remove?.(k);
    },
  },
  deepLink: {
    onUrl(handler) {
      let off: (() => void) | null = null;
      (async () => {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const a = (await appPlugin()) as any;
        const sub = await a.App?.addListener?.('appUrlOpen', (e: { url: string }) => {
          try { handler(new URL(e.url)); } catch { /* malformed — ignore */ }
        });
        off = () => sub?.remove?.();
      })().catch(() => undefined);
      return () => { off?.(); };
    },
  },
  updater: {
    async check()   { return null; },
    async install() { /* no-op */ },
  },
  notify: {
    async send(title, body) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const n = (await notifPlugin()) as any;
      const perm = await n.LocalNotifications?.checkPermissions?.();
      if (perm?.display !== 'granted') {
        await n.LocalNotifications?.requestPermissions?.();
      }
      await n.LocalNotifications?.schedule?.({
        notifications: [{ id: Date.now() % 2_147_483_647, title, body }],
      });
    },
  },
  shell: {
    async open(url) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const b = (await browserPlugin()) as any;
      if (b.Browser?.open) await b.Browser.open({ url });
      else webPlatform.shell.open(url);
    },
  },
};

export { bytesToBase64, base64ToBytes };
