// Files — full-bleed code preview. Reuses the existing FilePreviewPane
// component but no longer competes with the agent table, config, and
// safety review for horizontal space.

import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { Button } from '@/components/primitives/Button';
import { FilePreviewPane } from '../components/FilePreviewPane';
import { ReviewShell } from './ReviewShell';
import { useReviewSub } from './state';

export function ReviewFiles() {
  const { go } = useReviewSub();
  return (
    <ReviewShell
      title="Generated files"
      subtitle="19 files · regenerate, lock, or diff per file. Toggle to the HomePilot adapter view to see runtime-specific additions."
      footer={
        <>
          <Button variant="ghost" onClick={() => go('config')}>
            <Icon name="arrow-l" size={13} /> Configuration
          </Button>
          <span
            className="ag-mono ag-small"
            style={{ color: tokens.muted, marginLeft: 14 }}
          >
            regenerate · lock · diff
          </span>
          <span style={{ flex: 1 }} />
          <Button variant="ghost">
            <Icon name="download" size={13} /> Download .zip
          </Button>
          <Button variant="primary" onClick={() => go('safety')}>
            Safety <Icon name="arrow" size={13} stroke="#fff" />
          </Button>
        </>
      }
    >
      <FilePreviewPane height={460} />
    </ReviewShell>
  );
}
