"""Controlled blueprint compiler (Batch 5, strict export in Batch 6).

Compiles a ``BlueprintResult`` (+ its standards lock + coder prompts) into a deterministic,
byte-stable ``CompiledBundle``: the six MATRIX control files, docs, README, scaffold sources,
prompts, an SBOM, a manifest, and a checksums file — with immutable files hash-locked.

Strict assembly order (each layer covers the previous):
  content + SBOM  →  manifest.json  →  checksums.txt
"""

from __future__ import annotations

from agent_generator.artifacts.canonical import normalize_newlines
from agent_generator.artifacts.checksums import CHECKSUMS_PATH, build_checksums_txt
from agent_generator.artifacts.sbom import SBOM_PATH, build_sbom
from agent_generator.contracts.blueprint import BlueprintResult
from agent_generator.contracts.standards import StandardsLock
from agent_generator.control.contract import IMMUTABLE_FILES, compute_contract_hash
from agent_generator.template_compiler import control_files as cf
from agent_generator.template_compiler.file_plan import CompiledBundle, CompiledFile
from agent_generator.template_compiler.manifest import MANIFEST_PATH, build_manifest_json
from agent_generator.template_compiler.scaffold_writer import build_scaffold


def _f(path: str, content: str, kind: str, *, immutable: bool = False) -> CompiledFile:
    """Build a CompiledFile with LF-normalized content (strict line endings)."""
    return CompiledFile(path, normalize_newlines(content), kind=kind, immutable=immutable)


def compile_blueprint(
    blueprint: BlueprintResult,
    *,
    version: str = "1.0.0",
    standards_lock: StandardsLock | None,
    standards_lock_text: str,
    prompt_files: dict[str, str],
) -> CompiledBundle:
    """Compile a controlled blueprint into a full, deterministic file plan."""
    sbom_timestamp = standards_lock.generated_at if standards_lock else "1980-01-01T00:00:00Z"
    files: list[CompiledFile] = []

    # 1. Control files (MATRIX_BLUEPRINT.yaml and MATRIX_STANDARDS.lock are immutable).
    files.append(
        _f("MATRIX_BLUEPRINT.yaml", cf.render_blueprint_yaml(blueprint), "control", immutable=True)
    )
    files.append(_f("MATRIX_STANDARDS.lock", standards_lock_text, "control", immutable=True))
    files.append(_f("MATRIX_TASKS.md", cf.render_tasks_md(blueprint), "control"))
    files.append(
        _f("MATRIX_ALLOWED_CHANGES.md", cf.render_allowed_changes_md(blueprint), "control")
    )
    files.append(_f("MATRIX_ACCEPTANCE_CRITERIA.md", cf.render_acceptance_md(blueprint), "control"))
    files.append(
        _f("MATRIX_VALIDATION.md", cf.render_validation_md(blueprint, standards_lock), "control")
    )

    # 2. README + docs.
    files.append(_f("README.md", cf.render_readme(blueprint, version), "doc"))
    files.append(_f("docs/architecture.md", cf.render_architecture_doc(blueprint), "doc"))
    files.append(_f("docs/security.md", cf.render_security_doc(blueprint, standards_lock), "doc"))
    files.append(
        _f("docs/standards-report.md", cf.render_standards_report(blueprint, standards_lock), "doc")
    )

    # 3. Scaffold sources.
    for sf in build_scaffold(blueprint):
        files.append(_f(sf.path, sf.content, sf.kind))

    # 4. Coder prompts (rendered by the engine and passed in).
    for path, content in sorted(prompt_files.items()):
        files.append(_f(path, content, "prompt"))

    # 5. SBOM (placeholder) — part of the content layer the manifest indexes.
    files.append(
        _f(SBOM_PATH, build_sbom(blueprint, version=version, timestamp=sbom_timestamp), "sbom")
    )

    # 6. Hash-lock the immutable files.
    immutable_map = {f.path: f.content for f in files if f.immutable}
    contract_hash = compute_contract_hash(immutable_map)

    # 7. Manifest indexes content + SBOM (excludes manifest.json and checksums.txt).
    manifest_text = build_manifest_json(
        blueprint_id=blueprint.blueprint_id,
        slug=blueprint.slug,
        version=version,
        files=files,
        immutable_files=tuple(sorted(immutable_map)),
        contract_hash=contract_hash,
        sbom_ref=SBOM_PATH,
    )
    files.append(_f(MANIFEST_PATH, manifest_text, "manifest"))

    # 8. checksums.txt is the outermost index: covers everything except itself.
    checksums_text = build_checksums_txt({f.path: f.content for f in files})
    files.append(_f(CHECKSUMS_PATH, checksums_text, "checksums"))

    return CompiledBundle(
        blueprint_id=blueprint.blueprint_id,
        slug=blueprint.slug,
        version=version,
        files=tuple(sorted(files, key=lambda f: f.path)),
        contract_hash=contract_hash,
        immutable_files=tuple(sorted(immutable_map)),
    )


__all__ = ["compile_blueprint", "IMMUTABLE_FILES"]
