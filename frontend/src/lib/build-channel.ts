// Build-channel helpers. The SPA is shipped through four channels —
// web, tauri, capacitor, and hf (Hugging Face Space demo) — all from
// the same source tree. Components that need to behave differently
// in the demo should branch off `IS_DEMO`; do not fork files.
//
// `AG_BUILD_CHANNEL` is injected by `vite.config.ts` at build time,
// so the constants below are tree-shaken into a single boolean per
// build and add zero bytes to production bundles.

export type BuildChannel = 'web' | 'tauri' | 'capacitor' | 'hf';

export const BUILD_CHANNEL: BuildChannel = import.meta.env.AG_BUILD_CHANNEL;

/**
 * `true` only when the SPA is running inside the Hugging Face Space
 * demo. Use it to disable irreversible / persistent operations
 * (GitHub OAuth, project save/restore, run history, etc.) and to
 * surface a "demo mode" affordance in the UI.
 */
export const IS_DEMO = BUILD_CHANNEL === 'hf';

/**
 * `true` for builds embedded inside a native shell (Tauri desktop or
 * Capacitor mobile). Useful for hiding browser-only chrome (e.g. the
 * web update banner) or enabling shell-only features.
 */
export const IS_NATIVE_SHELL =
  BUILD_CHANNEL === 'tauri' || BUILD_CHANNEL === 'capacitor';

/**
 * Single, human-readable label for the current build channel. Surface
 * via tooltips, the About modal footer, telemetry tags, etc.
 */
export const BUILD_CHANNEL_LABEL: Record<BuildChannel, string> = {
  web: 'Web',
  tauri: 'Desktop',
  capacitor: 'Mobile',
  hf: 'Demo',
};
