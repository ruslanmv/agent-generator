"""MatrixHub publication gate (Batch 10) — dry-run only.

Publishing is a *contract check*, not a file upload. A bundle may be published only when every
required artifact is present and validation has approved it. This module computes that gate and
returns a ``PublicationResponse``; it never performs a live upload (live publishing waits on the
matrix-hub track and is surfaced later as "Submit as public template").
"""

from __future__ import annotations

from agent_generator.artifacts.checksums import CHECKSUMS_PATH
from agent_generator.artifacts.provenance import PROVENANCE_PATH
from agent_generator.artifacts.sbom import SBOM_PATH
from agent_generator.contracts.publication import PublicationResponse
from agent_generator.contracts.validation import ValidationReport
from agent_generator.template_compiler.file_plan import CompiledBundle
from agent_generator.template_compiler.manifest import MANIFEST_PATH

#: A bundle must contain all of these to be publishable.
REQUIRED_ARTIFACTS: tuple[str, ...] = (
    "README.md",
    "MATRIX_BLUEPRINT.yaml",
    "MATRIX_STANDARDS.lock",
    "docs/security.md",
    "docs/standards-report.md",
    SBOM_PATH,
    PROVENANCE_PATH,
    MANIFEST_PATH,
    CHECKSUMS_PATH,
)


def build_publication(
    compiled: CompiledBundle,
    *,
    validation_report: ValidationReport | None = None,
    slug: str | None = None,
    visibility: str = "public",
    dry_run: bool = True,
) -> PublicationResponse:
    """Evaluate the MatrixHub trust gate and return a (dry-run) publication response."""
    present = set(compiled.paths())
    missing = [a for a in REQUIRED_ARTIFACTS if a not in present]

    validation_ok = bool(validation_report and validation_report.approved)
    validation_status = validation_report.status.value if validation_report else "not-run"
    publication_id = f"pub_{compiled.slug}_{compiled.version}".replace(".", "_")
    target_slug = slug or compiled.slug

    if missing:
        return PublicationResponse(
            publication_id=publication_id,
            bundle_id=compiled.blueprint_id,
            dry_run=dry_run,
            accepted=False,
            status="rejected",
            matrixhub_slug=target_slug,
            required_artifacts=list(REQUIRED_ARTIFACTS),
            missing_artifacts=missing,
            validation_status=validation_status,
            validation_report_id=validation_report.report_id if validation_report else None,
            trust_status="rejected",
            message=f"Missing required artifacts: {', '.join(missing)}",
        )

    if not validation_ok:
        return PublicationResponse(
            publication_id=publication_id,
            bundle_id=compiled.blueprint_id,
            dry_run=dry_run,
            accepted=False,
            status="needs-validation",
            matrixhub_slug=target_slug,
            required_artifacts=list(REQUIRED_ARTIFACTS),
            missing_artifacts=[],
            validation_status=validation_status,
            validation_report_id=validation_report.report_id if validation_report else None,
            trust_status="unverified",
            message="Bundle must pass validation (status approved) before publishing.",
        )

    return PublicationResponse(
        publication_id=publication_id,
        bundle_id=compiled.blueprint_id,
        dry_run=dry_run,
        accepted=True,
        status="accepted-dry-run" if dry_run else "accepted",
        matrixhub_slug=target_slug,
        required_artifacts=list(REQUIRED_ARTIFACTS),
        missing_artifacts=[],
        validation_status=validation_status,
        validation_report_id=validation_report.report_id if validation_report else None,
        trust_status="dry-run" if dry_run else "published",
        message=(
            f"Dry-run accepted: '{target_slug}' is blueprint-locked, standards-locked, "
            f"has release evidence, and passed validation ({visibility})."
        ),
    )


__all__ = ["REQUIRED_ARTIFACTS", "build_publication"]
