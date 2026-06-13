"""Publication contracts — MatrixHub publish request and response.

The engine prepares and dry-runs publication payloads (Batch 10). Live publishing is
gated on a parallel matrix-hub track, so ``dry_run`` defaults to ``True``.
"""

from __future__ import annotations

from agent_generator.contracts.common import JsonDict, StrictModel


class PublicationRequest(StrictModel):
    schema_version: str = "matrix.builder.publication/v1"
    bundle_id: str | None = None
    target: str = "matrixhub"
    dry_run: bool = True
    visibility: str = "public"
    slug: str | None = None
    metadata: JsonDict = {}


class PublicationResponse(StrictModel):
    publication_id: str = "pub_not_connected"
    bundle_id: str = "bundle_demo"
    target: str = "matrixhub"
    dry_run: bool = True
    accepted: bool = False
    status: str
    matrixhub_slug: str | None = None
    required_artifacts: list[str] = []
    missing_artifacts: list[str] = []
    validation_status: str | None = None
    validation_report_id: str | None = None
    trust_status: str = "dry-run"
    message: str


__all__ = ["PublicationRequest", "PublicationResponse"]
