// Tauri adapter — dynamic-imports `@tauri-apps/api/*` modules so the web
// build doesn't pull them in. Wiring lands in Batch 26 (native plugins);
// this file ships the shape today so the rest of the app can be written
// platform-blind.

import { webPlatform } from './web';
import type { Platform, PlatformInfo } from './types';

const VERSION = import.meta.env.APP_VERSION ?? '0.0.0-dev';

const lazy = <T>(loader: () => Promise<T>) => {
  let promise: Promise<T> | null = null;
  return () => (promise ??= loader());
};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const dialog       = lazy(() => import(/* @vite-ignore */ '@tauri-apps/plugin-dialog').catch(() => ({} as any)));
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const tauriFs      = lazy(() => import(/* @vite-ignore */ '@tauri-apps/plugin-fs').catch(() => ({} as any)));
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const store        = lazy(() => import(/* @vite-ignore */ '@tauri-apps/plugin-store').catch(() => ({} as any)));
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const stronghold   = lazy(() => import(/* @vite-ignore */ '@tauri-apps/plugin-stronghold').catch(() => ({} as any)));
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const updater      = lazy(() => import(/* @vite-ignore */ '@tauri-apps/plugin-updater').catch(() => ({} as any)));
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const notification = lazy(() => import(/* @vite-ignore */ '@tauri-apps/plugin-notification').catch(() => ({} as any)));
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const opener       = lazy(() => import(/* @vite-ignore */ '@tauri-apps/plugin-opener').catch(() => ({} as any)));
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const deepLinkApi  = lazy(() => import(/* @vite-ignore */ '@tauri-apps/plugin-deep-link').catch(() => ({} as any)));
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const os           = lazy(() => import(/* @vite-ignore */ '@tauri-apps/plugin-os').catch(() => ({} as any)));

let cachedOs = 'unknown';
async function detectOs(): Promise<string> {
  if (cachedOs !== 'unknown') return cachedOs;
  try {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const m = (await os()) as any;
    cachedOs = (await m.platform?.()) ?? 'unknown';
  } catch {
    /* plugin not installed yet — keep 'unknown'. */
  }
  return cachedOs;
}

const info: PlatformInfo = { id: 'tauri', os: 'unknown', appVersion: VERSION };
detectOs().then((o) => (info.os = o)).catch(() => undefined);

export const tauriPlatform: Platform = {
  info,
  fs: {
    async saveFile(name, bytes) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const d = (await dialog()) as any;
      const path: string | null = await d.save?.({ defaultPath: name }) ?? null;
      if (!path) return null;
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const f = (await tauriFs()) as any;
      await f.writeFile?.(path, bytes);
      return path;
    },
    async openFile(opts) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const d = (await dialog()) as any;
      const path: string | null = await d.open?.({
        multiple: false,
        filters: opts?.accept?.length
          ? [{ name: 'Files', extensions: opts.accept.map((a) => a.replace(/^\./, '')) }]
          : undefined,
      }) ?? null;
      if (!path) return null;
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const f = (await tauriFs()) as any;
      const bytes = (await f.readFile?.(path)) as Uint8Array;
      const name = path.split(/[\\/]/).pop() ?? 'unnamed';
      return { name, bytes };
    },
  },
  kv: {
    async get(k) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const s = (await store()) as any;
      const file = await s.load?.('settings.json');
      return (await file?.get?.(k)) ?? null;
    },
    async set(k, v) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const s = (await store()) as any;
      const file = await s.load?.('settings.json');
      await file?.set?.(k, v);
      await file?.save?.();
    },
    async delete(k) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const s = (await store()) as any;
      const file = await s.load?.('settings.json');
      await file?.delete?.(k);
      await file?.save?.();
    },
  },
  secureStore: {
    async get(k) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const sh = (await stronghold()) as any;
      const vault = await sh.load?.('vault.hold');
      return (await vault?.get?.(k)) ?? null;
    },
    async set(k, v) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const sh = (await stronghold()) as any;
      const vault = await sh.load?.('vault.hold');
      await vault?.set?.(k, v);
      await vault?.save?.();
    },
    async delete(k) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const sh = (await stronghold()) as any;
      const vault = await sh.load?.('vault.hold');
      await vault?.delete?.(k);
      await vault?.save?.();
    },
  },
  deepLink: {
    onUrl(handler) {
      let unlisten: (() => void) | null = null;
      (async () => {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const d = (await deepLinkApi()) as any;
        const off: (() => void) = await d.onOpenUrl?.((urls: string[]) => {
          urls.forEach((u) => {
            try { handler(new URL(u)); } catch { /* malformed — ignore */ }
          });
        }) ?? (() => undefined);
        unlisten = off;
      })().catch(() => undefined);
      return () => { unlisten?.(); };
    },
  },
  updater: {
    async check() {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const u = (await updater()) as any;
      const update = await u.check?.();
      if (!update?.available) return null;
      return { version: update.version, notes: update.body ?? '' };
    },
    async install() {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const u = (await updater()) as any;
      const update = await u.check?.();
      if (update?.available) await update.downloadAndInstall?.();
    },
  },
  notify: {
    async send(title, body) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const n = (await notification()) as any;
      const permission = await n.isPermissionGranted?.();
      if (!permission) await n.requestPermission?.();
      await n.sendNotification?.({ title, body });
    },
  },
  shell: {
    async open(url) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const o = (await opener()) as any;
      if (o.openUrl) {
        await o.openUrl(url);
      } else {
        webPlatform.shell.open(url);
      }
    },
  },
};
