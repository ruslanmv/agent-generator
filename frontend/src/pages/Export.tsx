// Export & Publish — replaces the HomePilot-centric "GenerateDone" with a
// neutral export grid. HomePilot is one card among many; clicking it (or
// any runtime adapter) opens a generic Runtime Adapter Preview modal.
//
// Publishing flips the page into a 3-step MatrixHub flow: Validation →
// Visibility → Published. State is local so the URL stays at /export;
// router-level deep links land in Batch 8.

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { Button } from '@/components/primitives/Button';
import { ExportGrid } from './export/ExportGrid';
import { PublishCard } from './export/PublishCard';
import { Published } from './export/Published';
import { PublishValidation } from './export/PublishValidation';
import { PublishVisibility } from './export/PublishVisibility';
import { RuntimeAdapterModal } from './export/RuntimeAdapterModal';
import { ADAPTER_PRESETS, type ExportAdapter } from '@/lib/export-data';

type Phase = 'done' | 'validation' | 'visibility' | 'published';

export function ExportPage() {
  const navigate = useNavigate();
  const [phase, setPhase] = useState<Phase>('done');
  const [adapterId, setAdapterId] = useState<string | null>(null);

  const handlePickAdapter = (adapter: ExportAdapter) => {
    // HomePilot has a tailored preset; everything else also opens the
    // adapter preview but via the generic template.
    if (ADAPTER_PRESETS[adapter.id]) {
      setAdapterId(adapter.id);
    } else if (adapter.homepilot) {
      setAdapterId('homepilot');
    } else {
      setAdapterId(adapter.id);
    }
  };

  if (phase === 'validation') {
    return (
      <PublishValidation
        onCancel={() => setPhase('done')}
        onContinue={() => setPhase('visibility')}
      />
    );
  }
  if (phase === 'visibility') {
    return (
      <PublishVisibility
        onBack={() => setPhase('validation')}
        onPublish={() => setPhase('published')}
      />
    );
  }
  if (phase === 'published') {
    return (
      <Published
        onBackToProject={() => setPhase('done')}
        onOpenMarketplace={() => navigate('/marketplace')}
      />
    );
  }

  return (
    <>
      <GenerateDone
        onSelectAdapter={handlePickAdapter}
        onPublish={() => setPhase('validation')}
      />
      {adapterId && (
        <RuntimeAdapterModal
          adapterId={adapterId}
          onClose={() => setAdapterId(null)}
          onInstall={() => setAdapterId(null)}
        />
      )}
    </>
  );
}

interface DoneProps {
  onSelectAdapter: (adapter: ExportAdapter) => void;
  onPublish: () => void;
}

function GenerateDone({ onSelectAdapter, onPublish }: DoneProps) {
  return (
    <div style={{ padding: '40px 80px', maxWidth: 1280, margin: '0 auto', position: 'relative' }}>
      <div className="ag-eyebrow" style={{ marginBottom: 12 }}>GENERATE · COMPLETE</div>
      <div style={{ display: 'flex', alignItems: 'flex-end', gap: 16, marginBottom: 8 }}>
        <h2 className="ag-h2" style={{ margin: 0 }}>arxiv-digest is ready.</h2>
        <span className="ag-mono ag-small" style={{ color: tokens.muted, paddingBottom: 6 }}>
          22 files · 1.4 MB · 18.4s · 7,210 tokens
        </span>
      </div>
      <p className="ag-body" style={{ marginBottom: 18, color: tokens.ink3 }}>
        Export it to a runtime, push it to a repository, or publish to MatrixHub for others to
        discover.
      </p>

      <div style={{ display: 'flex', gap: 8, marginBottom: 28, alignItems: 'center' }}>
        <Button variant="ghost" size="sm">
          <Icon name="doc" size={13} /> Preview files
        </Button>
        <Button variant="ghost" size="sm">
          <Icon name="play" size={13} /> Run dry-run
        </Button>
        <Button variant="ghost" size="sm">
          <Icon name="cog" size={13} /> Review permissions
        </Button>
        <span style={{ flex: 1 }} />
        <span className="ag-mono ag-small" style={{ color: tokens.muted }}>
          package · agent-generator.package.v1
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.55fr 1fr', gap: 28 }}>
        <ExportGrid onSelectAdapter={onSelectAdapter} />
        <PublishCard onPublish={onPublish} />
      </div>
    </div>
  );
}
