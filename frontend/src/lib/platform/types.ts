// Platform-abstraction contract — what every shell (web · Tauri ·
// Capacitor) must provide. Keep small: only OS-specific operations
// belong here. Everything else (HTTP, WebSocket, routing) is identical
// across shells.

export type PlatformId = 'web' | 'tauri' | 'capacitor';

export interface PlatformInfo {
  id: PlatformId;
  /** "linux" | "macos" | "windows" | "android" | "ios" | "browser". */
  os: string;
  /** App version pulled from package.json at build time. */
  appVersion: string;
}

/** File-system operations — desktop and mobile use native pickers;
 * web falls back to a download attribute. */
export interface FsAdapter {
  /** Prompt the user to save `bytes` as `name`. Returns the chosen path
   * (Tauri / Capacitor) or `null` on web (where the browser downloads
   * to its default folder). */
  saveFile(name: string, bytes: Uint8Array, mime?: string): Promise<string | null>;
  /** Read a user-picked file. Returns `null` if the user cancels. */
  openFile(opts?: { accept?: string[] }): Promise<{ name: string; bytes: Uint8Array } | null>;
}

/** Persistent key/value store. Web → localStorage; Tauri → Stronghold
 * or tauri-plugin-store; Capacitor → Preferences plugin (Android
 * SharedPreferences). */
export interface KvAdapter {
  get(key: string): Promise<string | null>;
  set(key: string, value: string): Promise<void>;
  delete(key: string): Promise<void>;
}

/** Secure key/value store — distinct from `kv` because secrets MUST
 * land in the OS keychain on desktop and Android KeyStore on mobile.
 * On web they fall through to `kv` with a warning logged in dev. */
export interface SecureStoreAdapter {
  get(key: string): Promise<string | null>;
  set(key: string, value: string): Promise<void>;
  delete(key: string): Promise<void>;
}

/** Deep-link router. Tauri registers `agent-generator://` at install
 * time; Capacitor uses Android intent filters; web parses the
 * `?deeplink=` query param so QR codes still work. */
export interface DeepLinkAdapter {
  /** Subscribe to URL events. Returns an unsubscribe function. */
  onUrl(handler: (url: URL) => void): () => void;
}

/** Auto-update — desktop only. Mobile uses the Play Store/App Store
 * channel and the adapter no-ops. Web no-ops too (the SPA picks up
 * new builds on next reload). */
export interface UpdaterAdapter {
  /** Returns the latest version manifest or `null` if no update. */
  check(): Promise<{ version: string; notes: string } | null>;
  /** Download + install + relaunch. */
  install(): Promise<void>;
}

/** OS-native notifications. Web → Notification API; Tauri →
 * tauri-plugin-notification; Capacitor → @capacitor/local-notifications. */
export interface NotifyAdapter {
  send(title: string, body: string): Promise<void>;
}

/** Open external URLs in the host browser (Tauri/Capacitor) or a new
 * tab (web). Avoid opening untrusted URLs without confirming with the
 * user first — desktop browsers will, but Tauri's webview won't. */
export interface ShellAdapter {
  open(url: string): Promise<void>;
}

export interface Platform {
  info: PlatformInfo;
  fs: FsAdapter;
  kv: KvAdapter;
  secureStore: SecureStoreAdapter;
  deepLink: DeepLinkAdapter;
  updater: UpdaterAdapter;
  notify: NotifyAdapter;
  shell: ShellAdapter;
}
