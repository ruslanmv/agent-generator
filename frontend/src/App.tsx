import { Navigate, Route, Routes } from 'react-router-dom';
import { DesktopShell } from '@/layouts/DesktopShell';
import { MobileShell } from '@/layouts/MobileShell';
import { GeneratePage } from '@/pages/Generate';
import { HistoryPage } from '@/pages/History';
import { RunPage } from '@/pages/Run';
import { TestPage } from '@/pages/Test';
import { PipelinePage } from '@/pages/Pipeline';
import { ProjectsHub } from '@/pages/projects/ProjectsHub';
import { ProjectDetailPage } from '@/pages/projects/ProjectDetail';
import { PublishHF } from '@/pages/publish-hf/PublishHF';
import { MarketplacePage } from '@/pages/Marketplace';
import { ExportPage } from '@/pages/Export';
import { DockerPage } from '@/pages/Docker';
import { SettingsPage } from '@/pages/Settings';
import { MobileGenerate } from '@/pages/mobile/MobileGenerate';
import { MobileMarketplace } from '@/pages/mobile/MobileMarketplace';
import { MobileExport } from '@/pages/mobile/MobileExport';
import { useIsMobile } from '@/lib/use-media';
import { BUILD_CHANNEL } from '@/lib/build-channel';
import { DeepLinkBridge } from '@/lib/deep-link';

export default function App() {
  // The Capacitor shell is always the mobile experience — even when
  // the WebView reports a CSS viewport >= 768 px (some Android emulator
  // profiles do this), we want MobileApp. Web/Tauri fall back to the
  // viewport-driven check so resizing a desktop window still works.
  const mobile = useIsMobile() || BUILD_CHANNEL === 'capacitor';
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
        <Route path="/test" element={<TestPage />} />
        <Route path="/export" element={<ExportPage />} />
        <Route path="/docker" element={<DockerPage />} />
        <Route path="/projects" element={<ProjectsHub />} />
        <Route path="/projects/:id" element={<ProjectDetailPage />} />
        <Route path="/projects/:id/publish/hf" element={<PublishHF />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/marketplace" element={<MarketplacePage />} />
        {/* The desktop shell exposes Settings as a modal opened from the
            avatar/account menu — no longer a routed full page. The
            catch-all redirect below handles stale /settings bookmarks. */}
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
