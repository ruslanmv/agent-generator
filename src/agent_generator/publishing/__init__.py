"""Publishing (Batch 10) — MatrixHub publication gate (dry-run).

Live publishing is out of the MVP (private-first). The engine prepares and dry-runs a
publication, enforcing the trust gate: a bundle is publishable only when it is
blueprint-locked, standards-locked, has release evidence, and has passed validation.
"""

from __future__ import annotations

from agent_generator.publishing.matrixhub import (
    REQUIRED_ARTIFACTS,
    build_publication,
)

__all__ = ["REQUIRED_ARTIFACTS", "build_publication"]
