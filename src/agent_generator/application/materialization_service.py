"""Materialization service — packages and verifies artifacts via MatrixLab."""

from __future__ import annotations

from agent_generator.application.release_service import build_zip_bytes
from agent_generator.domain.artifact_bundle import ArtifactBundle
from agent_generator.domain.materialization_report import MaterializationReport, MaterializationStep
from agent_generator.integrations.matrixlab_client import MatrixLabClient


class MaterializationService:
    """Package an ArtifactBundle and submit to MatrixLab for verification."""

    def __init__(self, client: MatrixLabClient) -> None:
        self.client = client

    def verify(
        self, artifact: ArtifactBundle, project_name: str = "project"
    ) -> MaterializationReport:
        """Package artifact to ZIP and submit for sandbox verification."""
        if not artifact.valid:
            return MaterializationReport(
                status="error",
                summary="Artifact has validation errors — cannot verify.",
                steps=[
                    MaterializationStep(
                        name="precheck", status="error", message="Artifact invalid."
                    )
                ],
            )

        # Package
        zip_bytes = build_zip_bytes(artifact, project_name)

        # Submit to MatrixLab
        try:
            result = self.client.submit_zip(zip_bytes, filename=f"{project_name}.zip")
        except Exception as e:
            return MaterializationReport(
                status="error",
                summary=f"Failed to submit to MatrixLab: {e}",
                steps=[
                    MaterializationStep(name="package", status="success", message="ZIP created."),
                    MaterializationStep(name="submit", status="error", message=str(e)[:200]),
                ],
            )

        # Convert MatrixLab response to MaterializationReport
        steps = [MaterializationStep(name="package", status="success", message="ZIP created.")]
        for step_data in result.get("steps", []):
            steps.append(
                MaterializationStep(
                    name=step_data.get("name", ""),
                    status=step_data.get("status", "error"),
                    message=step_data.get("message", ""),
                    logs=step_data.get("logs", ""),
                )
            )

        return MaterializationReport(
            status=result.get("status", "error"),
            sandbox_backend="matrixlab",
            run_id=result.get("id"),
            steps=steps,
            detected_language=result.get("language", ""),
            detected_framework=result.get("framework", ""),
            files_count=result.get("files_count", 0),
            summary=result.get("summary", ""),
        )
