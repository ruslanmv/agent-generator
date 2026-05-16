/// <reference types="vite/client" />

// Augment Vite's `import.meta.env` with the values our `vite.config.ts`
// injects at build time. The defaults make the types non-optional so
// callers don't have to narrow.

interface ImportMetaEnv {
  readonly APP_VERSION: string;
  /** "web" | "tauri" | "capacitor" — set per shell in CI; defaults to
   * "web" when `vite build` is invoked directly. */
  readonly AG_BUILD_CHANNEL: 'web' | 'tauri' | 'capacitor';
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
