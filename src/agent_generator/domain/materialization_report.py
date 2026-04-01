"""Typed verification result from sandbox execution."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class MaterializationStep(BaseModel):
    name: str
    status: Literal["pending", "running", "success", "warning", "error", "skipped"]
    message: str = ""
    logs: str = ""


class MaterializationReport(BaseModel):
    status: Literal["pending", "running", "success", "warning", "error"]
    sandbox_backend: str = "matrixlab"
    run_id: str | None = None
    steps: list[MaterializationStep] = Field(default_factory=list)
    detected_language: str = ""
    detected_framework: str = ""
    files_count: int = 0
    summary: str = ""
