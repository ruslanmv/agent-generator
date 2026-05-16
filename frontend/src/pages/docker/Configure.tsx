// Step 1 — Configure.
// Image tag, base image, multi-arch toggle, supply-chain options.

import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { Button } from '@/components/primitives/Button';
import { Toggle } from '@/components/primitives/Toggle';
import { useDocker } from './state';

export function Configure() {
  const { config, setConfig, setStep } = useDocker();
  return (
    <>
      <Heading
        eyebrow="STEP 1 / 5 · CONFIGURE"
        title="Set image identity and supply-chain options."
        blurb="The CI pipeline (.github/workflows/backend-image.yml) honours these settings — building a release tag here produces an identical artefact."
      />
      <div style={{ display: 'grid', gap: 14 }}>
        <Field label="Image tag">
          <Input
            value={config.image}
            onChange={(v) => setConfig({ ...config, image: v })}
            mono
            placeholder="ghcr.io/owner/agent:tag"
          />
        </Field>
        <Field label="Base image">
          <Input
            value={config.baseImage}
            onChange={(v) => setConfig({ ...config, baseImage: v })}
            mono
            placeholder="python:3.11-slim"
          />
        </Field>
        <Field label="Platforms">
          <div style={{ display: 'flex', gap: 10 }}>
            {(['linux/amd64', 'linux/arm64'] as const).map((p) => {
              const on = config.platforms.includes(p);
              return (
                <button
                  key={p}
                  type="button"
                  onClick={() =>
                    setConfig({
                      ...config,
                      platforms: on
                        ? config.platforms.filter((x) => x !== p)
                        : [...config.platforms, p],
                    })
                  }
                  style={{
                    padding: '6px 10px',
                    border: `1px solid ${on ? tokens.ink : tokens.border}`,
                    background: on ? tokens.surface : '#fff',
                    fontFamily: tokens.mono,
                    fontSize: 12,
                    cursor: 'pointer',
                  }}
                >
                  {on ? '✓ ' : ''}
                  {p}
                </button>
              );
            })}
          </div>
        </Field>
        <Field label="Push on build">
          <Toggle
            checked={config.pushOnBuild}
            onChange={(on) => setConfig({ ...config, pushOnBuild: on })}
          />
        </Field>
        <Field label="Sign with cosign (keyless)">
          <Toggle
            checked={config.signWithCosign}
            onChange={(on) => setConfig({ ...config, signWithCosign: on })}
          />
        </Field>
        <Field label="Emit SPDX SBOM">
          <Toggle
            checked={config.emitSBOM}
            onChange={(on) => setConfig({ ...config, emitSBOM: on })}
          />
        </Field>
      </div>
      <Footer>
        <span style={{ flex: 1 }} />
        <Button
          variant="primary"
          onClick={() => setStep(1)}
          disabled={
            !config.image ||
            !config.baseImage ||
            config.platforms.length === 0
          }
        >
          Continue to env <Icon name="arrow" size={12} stroke="#fff" />
        </Button>
      </Footer>
    </>
  );
}

export function Heading({
  eyebrow,
  title,
  blurb,
}: {
  eyebrow: string;
  title: string;
  blurb: string;
}) {
  return (
    <>
      <div className="ag-eyebrow" style={{ marginBottom: 10 }}>
        {eyebrow}
      </div>
      <h2 className="ag-h2" style={{ marginBottom: 6 }}>
        {title}
      </h2>
      <p
        className="ag-body"
        style={{ marginBottom: 22, color: tokens.ink3 }}
      >
        {blurb}
      </p>
    </>
  );
}

export function Footer({ children }: { children: React.ReactNode }) {
  return (
    <div
      style={{
        marginTop: 28,
        display: 'flex',
        alignItems: 'center',
        gap: 10,
      }}
    >
      {children}
    </div>
  );
}

export function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
      <span
        style={{
          width: 200,
          fontSize: 13,
          color: tokens.ink2,
          flexShrink: 0,
        }}
      >
        {label}
      </span>
      <div style={{ flex: 1 }}>{children}</div>
    </div>
  );
}

export function Input({
  value,
  onChange,
  mono,
  placeholder,
}: {
  value: string;
  onChange: (v: string) => void;
  mono?: boolean;
  placeholder?: string;
}) {
  return (
    <input
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      style={{
        width: '100%',
        height: 30,
        padding: '0 10px',
        border: `1px solid ${tokens.border}`,
        background: '#fff',
        fontFamily: mono ? tokens.mono : tokens.sans,
        fontSize: 13,
        color: tokens.ink,
        outline: 'none',
        borderRadius: 0,
      }}
    />
  );
}
