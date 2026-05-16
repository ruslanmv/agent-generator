import { Navigate, Route, Routes } from 'react-router-dom';
import { DesktopShell } from '@/layouts/DesktopShell';
import { MobileShell } from '@/layouts/MobileShell';
import { GeneratePage } from '@/pages/Generate';
import { RunPage } from '@/pages/Run';
import { PipelinePage } from '@/pages/Pipeline';
import { MarketplacePage } from '@/pages/Marketplace';
import { ExportPage } from '@/pages/Export';
import { DockerPage } from '@/pages/Docker';
import { SettingsPage } from '@/pages/Settings';
import { Placeholder } from '@/pages/Placeholder';
import { MobileGenerate } from '@/pages/mobile/MobileGenerate';
import { MobileMarketplace } from '@/pages/mobile/MobileMarketplace';
import { MobileExport } from '@/pages/mobile/MobileExport';
import { useIsMobile } from '@/lib/use-media';
import { DeepLinkBridge } from '@/lib/deep-link';

export default function App() {
  const mobile = useIsMobile();
  return mobile ? <MobileApp /> : <DesktopApp />;
}

function DesktopApp() {
  return (
    <DesktopShell projectName="arxiv-digest" running={{ elapsed: '13.4s' }}>
      <DeepLinkBridge />
      <Routes>
        <Route path="/" element={<Navigate to="/generate" replace />} />
        <Route path="/generate" element={<GeneratePage />} />
        <Route path="/pipeline" element={<PipelinePage />} />
        <Route path="/run" element={<RunPage />} />
        <Route path="/export" element={<ExportPage />} />
        <Route path="/docker" element={<DockerPage />} />
        <Route path="/projects" element={<Placeholder title="Projects" blurb="Saved generations, runs, and history for the current admin." stage="coming-soon" batch="WORKSPACE  ·  BATCH 8" />} />
        <Route path="/marketplace" element={<MarketplacePage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="*" element={<Navigate to="/generate" replace />} />
      </Routes>
    </DesktopShell>
  );
}

function MobileApp() {
  return (
    <MobileShell>
      <DeepLinkBridge />
      <Routes>
        <Route path="/" element={<Navigate to="/generate" replace />} />
        <Route path="/generate" element={<MobileGenerate />} />
        <Route path="/pipeline" element={<MobileGenerate />} />
        <Route path="/run" element={<MobileGenerate />} />
        <Route path="/marketplace" element={<MobileMarketplace />} />
        <Route path="/export" element={<MobileExport />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="*" element={<Navigate to="/generate" replace />} />
      </Routes>
    </MobileShell>
  );
}
