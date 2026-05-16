import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';
import { readFileSync } from 'node:fs';

// Pull the canonical version string from package.json so the About
// modal, the AdminAccountMenu footer, and `platform.info.appVersion`
// all surface the same value without manual drift.
const pkg = JSON.parse(readFileSync(path.resolve(__dirname, 'package.json'), 'utf8'));

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');

  return {
    plugins: [react()],
    resolve: {
      alias: { '@': path.resolve(__dirname, 'src') },
    },

    // Tauri + Capacitor expect the dev server on a stable host/port.
    // 1420 is the Tauri convention; we keep 5173 to match `npm run dev`
    // and configure the Tauri shell to point at it (Batch 25).
    server: {
      port: Number(env.VITE_DEV_PORT) || 5173,
      host: true,
      strictPort: true,
    },
    preview: {
      port: 4173,
      host: true,
    },

    // Inject the canonical version + an explicit "ag" build channel so
    // every shell can read `import.meta.env.APP_VERSION` and
    // `import.meta.env.AG_BUILD_CHANNEL` (set per shell in CI).
    define: {
      'import.meta.env.APP_VERSION':      JSON.stringify(pkg.version),
      'import.meta.env.AG_BUILD_CHANNEL': JSON.stringify(env.AG_BUILD_CHANNEL ?? 'web'),
    },

    build: {
      // Tauri 2 webviews on macOS / Windows / Linux ship a recent
      // Chromium / WebKit; we can target ES2022 safely.
      target: 'es2022',
      emptyOutDir: true,
      chunkSizeWarningLimit: 600,
    },
  };
});
