# matrix-definitions standards loader (Batch 3)

The standards loader connects the engine to the **signed source of truth**,
`matrix-definitions`. It loads a standards pack, verifies it, checks engine compatibility,
and emits a deterministic `MATRIX_STANDARDS.lock`.

## Where the pack comes from

Resolution order for the matrix-definitions root (the directory containing `packs/` and
`profiles/`):

1. an explicit `standards_root` / `root` argument,
2. the `MATRIX_DEFINITIONS_DIR` environment variable,
3. the **version-pinned snapshot bundled with this package**
   (`agent_generator/standards/data/matrix-definitions`, pack `2026.06.0`).

The bundled snapshot makes the engine self-contained: it emits a real, verified lock with no
external checkout. Point `MATRIX_DEFINITIONS_DIR` at a live checkout to use a freshly-signed
pack instead.

## Verification posture

| Check | Posture | Behavior |
|---|---|---|
| **Checksums** (`checksums.txt`) | **Fail-closed** | A digest mismatch or missing file raises `StandardsError` (disable with `verify=False`). |
| **Signature** (cosign bundle) | **Warn mode** | The current pack ships a `status: placeholder` dev bundle. The loader records `signature_mode="placeholder"` and warns; it does not fail. `signature_mode="require"` raises until real signing lands (Batch 10). |
| **Compatibility** | Reported | `manifest.compatibility.agent_generator` (`>=0.2.0`) is checked against the engine version. |

## Usage

```python
from agent_generator import AgentGenerator

engine = AgentGenerator()                       # bundled pack
engine = AgentGenerator(standards_root="/path/to/matrix-definitions")

pack = engine.load_standards_pack()             # StandardsPack (loaded + verified)
meta = engine.standards_metadata()              # /api/v1/standards/current shape
lock = engine.generate_standards_lock("standard")  # -> StandardsLock
```

`generate_standards_lock(level)` builds a deterministic lock for a quality profile
(`starter` / `standard` / `production` / `enterprise`). Given the same pack, level, and
`generated_at`, the rendered YAML is byte-identical.

## What the lock pins

A `MATRIX_STANDARDS.lock` (validated against matrix-definitions
`matrix-standards-lock.schema.json`) records:

- `definitions_pack`: `pack_id`, `version`, and the combined-pack `checksum`.
- `quality_level` and the sorted `rules` applied (from the profile's `required_rules`).
- `control_files`: the Matrix control files the bundle locks.
- `checksums`: a `sha256:` digest for every pack input, so the lock self-documents exactly
  which standards bytes produced it.

A full example lives at `examples/standards/MATRIX_STANDARDS.lock`.

## Export integration

`export_zip` now writes the real lock into the bundle's `MATRIX_STANDARDS.lock` (replacing
the Batch 1 placeholder). If no pack can be resolved, the export degrades to a clearly-marked
placeholder rather than failing.

## Milestone

This batch ships **agent-generator 0.2.0**, which satisfies
`matrix-definitions.compatibility.agent_generator >= 0.2.0`. That is the point at which
Matrix Builder can set `AGENT_GENERATOR_MODE=sdk` and call the real engine: in SDK mode the
adapter now reports the active pack, a passing compatibility check, and the warn-mode
signature state.

## Re-syncing the bundled snapshot

The bundled pack is a pinned copy of matrix-definitions `2026.06.0`. To update it, copy the
new `packs/current/` and the four `profiles/*.yaml` into
`src/agent_generator/standards/data/matrix-definitions/`, then run `pytest tests/standards/`
— the checksum and schema tests fail loudly if the snapshot is inconsistent.
