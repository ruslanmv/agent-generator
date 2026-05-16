// Hyperscaler catalogue — Azure / AWS / GCP / IBM / on-prem.
// Drives the Framework & Model facet rail, the Marketplace facet group,
// and the per-row hyperscaler badges across the wizard, Marketplace, and
// Compatibility card.
//
// Pure data — no React, no DOM. Imported by both the frontend wizard and
// the mirror Pydantic module on the backend (Batch 17).

export type HyperscalerId = 'azure' | 'aws' | 'gcp' | 'ibm' | 'on_prem';

export type VendorId =
  | 'microsoft'
  | 'amazon'
  | 'google'
  | 'ibm'
  | 'langchain'
  | 'crewai'
  | 'community';

export interface Hyperscaler {
  id: HyperscalerId;
  label: string;
  /** Short uppercase code for the mono badge (e.g. "AZ", "AWS"). */
  short: string;
  /** Brand hex used for the chip border + dot. */
  brand: string;
  vendor: VendorId;
}

export const HYPERSCALERS: Hyperscaler[] = [
  { id: 'azure',   label: 'Azure',     short: 'AZ',  brand: '#0078d4', vendor: 'microsoft' },
  { id: 'aws',     label: 'AWS',       short: 'AWS', brand: '#ff9900', vendor: 'amazon'    },
  { id: 'gcp',     label: 'GCP',       short: 'GCP', brand: '#34a853', vendor: 'google'    },
  { id: 'ibm',     label: 'IBM',       short: 'IBM', brand: '#054ada', vendor: 'ibm'       },
  { id: 'on_prem', label: 'On‑prem',   short: 'OP',  brand: '#161616', vendor: 'community' },
];

export const VENDOR_LABEL: Record<VendorId, string> = {
  microsoft: 'Microsoft',
  amazon:    'AWS',
  google:    'Google',
  ibm:       'IBM',
  langchain: 'LangChain',
  crewai:    'CrewAI',
  community: 'community',
};

/** Lookup by id with a stable default (Azure) so callers never have to
 * narrow `Hyperscaler | undefined`. */
export function hyperscaler(id: HyperscalerId): Hyperscaler {
  return HYPERSCALERS.find((h) => h.id === id) ?? HYPERSCALERS[0];
}
