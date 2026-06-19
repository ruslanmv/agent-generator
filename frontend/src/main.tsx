import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import { AuthProvider } from './lib/auth';
import { CapabilitiesProvider } from './lib/capabilities';
import { bootAccent } from './lib/accent';
import './styles/global.css';

// Apply the persisted accent before the first render to avoid a one-frame
// flash of the default cobalt.
bootAccent();

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <CapabilitiesProvider>
        <AuthProvider>
          <App />
        </AuthProvider>
      </CapabilitiesProvider>
    </BrowserRouter>
  </React.StrictMode>,
);
