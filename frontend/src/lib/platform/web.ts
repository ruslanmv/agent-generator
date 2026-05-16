// Web platform adapter — pure browser APIs. Faithfully reproduces the
// behaviour the app had in Batches 1–8: localStorage for KV (and a
// warning for secureStore), <a download> for save, <input type=file>
// for open, Notification API for notify, window.open for shell.

import type {
  DeepLinkAdapter,
  FsAdapter,
  KvAdapter,
  NotifyAdapter,
  Platform,
  PlatformInfo,
  SecureStoreAdapter,
  ShellAdapter,
  UpdaterAdapter,
} from './types';

const VERSION = import.meta.env.APP_VERSION ?? '0.0.0-dev';

const info: PlatformInfo = {
  id: 'web',
  os: 'browser',
  appVersion: VERSION,
};

const fs: FsAdapter = {
  async saveFile(name, bytes, mime = 'application/octet-stream') {
    const blob = new Blob([bytes as BlobPart], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = name;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 60_000);
    return null;
  },
  openFile(opts) {
    return new Promise((resolve) => {
      const input = document.createElement('input');
      input.type = 'file';
      if (opts?.accept?.length) input.accept = opts.accept.join(',');
      input.onchange = async () => {
        const file = input.files?.[0];
        if (!file) return resolve(null);
        const bytes = new Uint8Array(await file.arrayBuffer());
        resolve({ name: file.name, bytes });
      };
      input.click();
    });
  },
};

const kv: KvAdapter = {
  async get(k)      { return localStorage.getItem(k); },
  async set(k, v)   { localStorage.setItem(k, v); },
  async delete(k)   { localStorage.removeItem(k); },
};

const secureStore: SecureStoreAdapter = {
  async get(k)      {
    if (import.meta.env.DEV && k.startsWith('secret.')) {
      // eslint-disable-next-line no-console
      console.warn('[platform/web] secureStore.get for "%s" — falling back to localStorage. This is NOT secure on web; only paired tokens for the admin should land here.', k);
    }
    return localStorage.getItem(k);
  },
  async set(k, v)   { localStorage.setItem(k, v); },
  async delete(k)   { localStorage.removeItem(k); },
};

const deepLink: DeepLinkAdapter = {
  onUrl(handler) {
    const initial = new URLSearchParams(window.location.search).get('deeplink');
    if (initial) {
      try { handler(new URL(initial)); } catch { /* malformed — ignore */ }
    }
    const listener = (e: MessageEvent) => {
      if (e.data?.type === 'ag.deeplink' && typeof e.data?.url === 'string') {
        try { handler(new URL(e.data.url)); } catch { /* ignore */ }
      }
    };
    window.addEventListener('message', listener);
    return () => window.removeEventListener('message', listener);
  },
};

const updater: UpdaterAdapter = {
  async check()    { return null; },
  async install()  { window.location.reload(); },
};

const notify: NotifyAdapter = {
  async send(title, body) {
    if (typeof Notification === 'undefined') return;
    let permission: NotificationPermission = Notification.permission;
    if (permission === 'default') permission = await Notification.requestPermission();
    if (permission === 'granted') new Notification(title, { body });
  },
};

const shell: ShellAdapter = {
  async open(url) {
    window.open(url, '_blank', 'noopener,noreferrer');
  },
};

export const webPlatform: Platform = { info, fs, kv, secureStore, deepLink, updater, notify, shell };
