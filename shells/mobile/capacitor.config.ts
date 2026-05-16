import type { CapacitorConfig } from '@capacitor/cli';

// Capacitor 6 configuration. Points `webDir` at the canonical
// `frontend/dist` so we never rebuild assets twice. Native plugin
// settings mirror the choices in `frontend/src/lib/platform/capacitor.ts`
// — keep them in sync when adding a plugin.

const config: CapacitorConfig = {
  appId: 'io.agent_generator.app',
  appName: 'Agent Generator',
  webDir: '../../frontend/dist',

  // Force the in-app webview to load a known URL on startup. In dev,
  // `CAP_SERVER_URL` can override this so `npm run dev` on the Vite
  // side hot-reloads to the phone over LAN.
  server: {
    androidScheme: 'https',
    cleartext: false,
    // Set CAP_SERVER_URL=http://192.168.1.42:5173 in your shell to
    // point at a Vite dev server during development. Unset for builds.
    url: process.env.CAP_SERVER_URL,
  },

  android: {
    // Make Android Studio prefer the bundled webview over Chrome Custom
    // Tabs for in-app content. External URLs (Settings → Privacy
    // Policy, etc.) still open in the system browser via
    // `@capacitor/browser`.
    allowMixedContent: false,
    captureInput: true,
    // 28 = Android 9. Below that, the WebView is too old for our ES2022
    // build target and the SPA renders incorrectly.
    minWebViewVersion: 80,
  },

  plugins: {
    SplashScreen: {
      launchShowDuration: 800,
      launchAutoHide: true,
      backgroundColor: '#161616', // tokens.ink — matches the desktop rail
      androidSplashResourceName: 'splash',
      showSpinner: false,
    },
    StatusBar: {
      // The web app uses a light surface (#f0eee9). Status-bar foreground
      // should be dark on Android so icons remain visible.
      style: 'LIGHT',
      backgroundColor: '#f0eee9',
      overlaysWebView: false,
    },
    Keyboard: {
      resize: 'body',
      style: 'LIGHT',
      resizeOnFullScreen: true,
    },
    LocalNotifications: {
      smallIcon: 'ic_stat_icon',
      iconColor: '#0a3df0', // tokens.accent
    },
  },
};

export default config;
