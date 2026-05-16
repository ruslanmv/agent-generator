// Step 5 — Published.
// Success state with the canonical pull command and a link back to
// the Marketplace.

import { useNavigate } from 'react-router-dom';
import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { Button } from '@/components/primitives/Button';
import { useDocker } from './state';
import { Heading } from './Configure';

export function Published() {
  const navigate = useNavigate();
  const { config } = useDocker();
  const pull = `docker pull ${config.image}`;

  return (
    <>
      <Heading
        eyebrow="STEP 5 / 5 · PUBLISHED"
        title={`${config.image} is live.`}
        blurb="Pull and run anywhere. The image carries a cosign signature and SBOM if you toggled those on in Configure."
      />
      <div
        style={{
          background: '#0b0b0b',
          color: '#dcdcdc',
          padding: 14,
          fontFamily: tokens.mono,
          fontSize: 13,
          border: `1px solid ${tokens.border}`,
          marginBottom: 14,
          userSelect: 'all',
        }}
      >
        <span style={{ color: '#888' }}>$ </span>
        {pull}
      </div>
      <div style={{ display: 'flex', gap: 10 }}>
        <Button
          variant="ghost"
          onClick={() => void navigator.clipboard?.writeText(pull)}
        >
          <Icon name="doc" size={12} /> Copy pull command
        </Button>
        <Button variant="ghost" onClick={() => navigate('/marketplace')}>
          <Icon name="cube" size={12} /> Open Marketplace
        </Button>
        <span style={{ flex: 1 }} />
        <Button variant="primary" onClick={() => navigate('/projects')}>
          Done <Icon name="check" size={12} stroke="#fff" />
        </Button>
      </div>
    </>
  );
}
