// Ambient module declarations for native plugins that are pulled in
// only inside the Tauri / Capacitor shells. These packages aren't in
// frontend/package.json (they live in shells/*/package.json) so the
// dynamic imports in src/lib/platform/* would fail type-checking
// without these stubs. The actual API surface is accessed through
// `as any` casts at the call site, so we only need bare module
// declarations here — not full type definitions.

declare module '@capacitor/preferences';
declare module '@capacitor/filesystem';
declare module '@capacitor/app';
declare module '@capacitor/local-notifications';
declare module '@capacitor/browser';
declare module '@capacitor/core';
declare module '@aparajita/capacitor-secure-storage';

declare module '@tauri-apps/plugin-dialog';
declare module '@tauri-apps/plugin-fs';
declare module '@tauri-apps/plugin-store';
declare module '@tauri-apps/plugin-stronghold';
declare module '@tauri-apps/plugin-updater';
declare module '@tauri-apps/plugin-notification';
declare module '@tauri-apps/plugin-opener';
declare module '@tauri-apps/plugin-deep-link';
declare module '@tauri-apps/plugin-os';
