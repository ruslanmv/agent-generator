// Generator-stage pill — Draft / Configured / Generated / Needs setup /
// Needs review / Exported / Template. No runtime states.

import { tokens } from '@/styles/tokens';
import { STAGE_META, type ProjectStage } from './types';

interface Props {
  stage: ProjectStage;
}

export function StagePill({ stage }: Props) {
  const meta = STAGE_META[stage];
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        padding: '2px 8px',
        fontFamily: tokens.mono,
        fontSize: 10,
        fontWeight: 600,
        letterSpacing: '.04em',
        textTransform: 'uppercase',
        color: meta.fg,
        background: meta.bg,
        border: `1px solid ${meta.border}`,
      }}
    >
      {meta.label}
    </span>
  );
}
