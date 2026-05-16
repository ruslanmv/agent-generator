"""Release service — package artifacts for distribution."""

from __future__ import annotations

from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

from agent_generator.domain.artifact_bundle import ArtifactBundle


def build_zip_bytes(artifact: ArtifactBundle, project_name: str = "project") -> bytes:
    """Create a ZIP archive from an ArtifactBundle."""
    buf = BytesIO()
    with ZipFile(buf, "w", ZIP_DEFLATED) as zf:
        for file in artifact.files:
            zf.writestr(f"{project_name}/{file.path}", file.content)
    return buf.getvalue()
