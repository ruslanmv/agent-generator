"""MatrixLab Sandbox client — submits artifacts for verification."""

from __future__ import annotations

from typing import Any

import requests


class MatrixLabClient:
    """HTTP client for the MatrixLab Sandbox verification service."""

    def __init__(
        self,
        base_url: str = "https://agent-matrix-matrixlab-sandbox.hf.space",
        api_key: str | None = None,
        timeout: int = 120,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        h: dict[str, str] = {}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    @property
    def available(self) -> bool:
        try:
            r = requests.get(f"{self.base_url}/health", headers=self._headers(), timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    def submit_zip(self, zip_bytes: bytes, filename: str = "project.zip") -> dict[str, Any]:
        """Submit a ZIP for verification. Returns the full run result."""
        r = requests.post(
            f"{self.base_url}/runs",
            headers=self._headers(),
            files={"file": (filename, zip_bytes, "application/zip")},
            timeout=self.timeout,
        )
        r.raise_for_status()
        return r.json()

    def get_run(self, run_id: str) -> dict[str, Any]:
        r = requests.get(
            f"{self.base_url}/runs/{run_id}",
            headers=self._headers(),
            timeout=self.timeout,
        )
        r.raise_for_status()
        return r.json()

    def list_runs(self) -> list[dict[str, Any]]:
        r = requests.get(
            f"{self.base_url}/runs",
            headers=self._headers(),
            timeout=self.timeout,
        )
        r.raise_for_status()
        return r.json().get("runs", [])
