// Placeholder pages — stubs for routes that get built out in later batches.

import { tokens } from '@/styles/tokens';
import { StagePillBadge, type StagePill } from '@/components/primitives/Pill';
import { DemoBanner } from '@/components/demo/DemoBanner';

interface PlaceholderProps {
  title: string;
  blurb: string;
  stage: StagePill;
  batch: string;
}

export function Placeholder({ title, blurb, stage, batch }: PlaceholderProps) {
  return (
    <div style={{ padding: '60px 80px', maxWidth: 720 }}>
      <DemoBanner>
        This page surfaces persistent state that the Hugging Face Space
        demo intentionally does not store. Try the wizard and the
        marketplace — both are fully functional in demo mode.
      </DemoBanner>
      <div className="ag-eyebrow" style={{ marginBottom: 12 }}>{batch}</div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
        <h1 className="ag-h2">{title}</h1>
        <StagePillBadge stage={stage} />
      </div>
      <p className="ag-body" style={{ color: tokens.ink3 }}>{blurb}</p>
    </div>
  );
}
