import { defineConfig, devices } from '@playwright/test';

// Smoke flows for the production Vite bundle. CI launches `vite
// preview` from the frontend/ directory and points us at it.
//
// We deliberately don't spin up the backend here — the smoke flows
// exercise the SPA's static surface (wizard navigation, marketplace,
// step transitions, deep-link form). End-to-end backend integration
// tests live in tests/integration on the backend side (Batch 30
// follow-up).

const PORT = Number(process.env.E2E_WEB_PORT ?? 4173);
const BASE_URL = process.env.E2E_BASE_URL ?? `http://localhost:${PORT}`;

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 2 : undefined,
  reporter: process.env.CI
    ? [['github'], ['html', { open: 'never' }]]
    : 'list',
  timeout: 30_000,
  use: {
    baseURL: BASE_URL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 900 } },
    },
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] },
    },
  ],
  webServer: process.env.E2E_NO_SERVER
    ? undefined
    : {
        command: `npm --prefix ../../frontend run preview -- --host 127.0.0.1 --port ${PORT} --strictPort`,
        url: BASE_URL,
        reuseExistingServer: !process.env.CI,
        stdout: 'pipe',
        stderr: 'pipe',
        timeout: 120_000,
      },
});
