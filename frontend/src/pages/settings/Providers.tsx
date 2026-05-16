import { tokens } from '@/styles/tokens';
import { Icon } from '@/components/icons/Icon';
import { Button } from '@/components/primitives/Button';
import { Pill } from '@/components/primitives/Pill';
import { OllaBridgeMark } from '@/components/icons/Logo';
import { PROVIDERS, type Provider } from '@/lib/settings-data';

export function ProvidersSettings() {
  return (
    <div>
      <p className="ag-body" style={{ color: tokens.ink3, marginBottom: 24 }}>
        LLM providers available to generated projects. The default ships with every new project.
      </p>

      {PROVIDERS.map((p, i) => (
        <ProviderRow key={p.id} provider={p} last={i === PROVIDERS.length - 1} />
      ))}

      <div
        style={{
          marginTop: 28,
          padding: 20,
          background: tokens.surface,
          border: `1px solid ${tokens.border}`,
        }}
      >
        <div className="ag-cap" style={{ marginBottom: 6 }}>Plug-in templates</div>
        <p className="ag-body" style={{ color: tokens.ink2, marginBottom: 12 }}>
          Add your own framework template. The community registry ships AutoGen, LlamaIndex, and 14 more.
        </p>
        <div style={{ display: 'flex', gap: 8 }}>
          <Button variant="ghost" size="sm">
            <Icon name="folder" size={12} /> Browse registry
          </Button>
          <Button size="sm">
            <Icon name="plus" size={12} stroke="#fff" /> Add from URL
          </Button>
        </div>
      </div>
    </div>
  );
}

function ProviderRow({ provider, last }: { provider: Provider; last: boolean }) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        padding: '16px 0',
        borderBottom: last ? 'none' : `1px solid ${tokens.border}`,
        gap: 16,
      }}
    >
      {provider.ollabridge ? (
        <OllaBridgeMark size={36} />
      ) : (
        <div
          style={{
            width: 36,
            height: 36,
            background: tokens.surface,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontFamily: tokens.mono,
            fontSize: 13,
            fontWeight: 500,
            flexShrink: 0,
          }}
        >
          {provider.name.slice(0, 2).toLowerCase()}
        </div>
      )}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 14, fontWeight: 500 }}>{provider.name}</span>
          {provider.isDefault && <Pill variant="accent">default</Pill>}
          {provider.isNew && <Pill variant="ok">new</Pill>}
        </div>
        <span className="ag-mono ag-small" style={{ color: tokens.muted }}>
          {provider.models}
        </span>
      </div>
      <Pill variant={provider.status === 'connected' ? 'ok' : 'default'}>
        <Icon
          name="dot"
          size={9}
          stroke={provider.status === 'connected' ? tokens.ok : tokens.muted}
        />
        {provider.status}
      </Pill>
      <Button variant="ghost" size="sm">
        {provider.status === 'connected' ? 'Manage' : 'Connect'}
      </Button>
    </div>
  );
}
