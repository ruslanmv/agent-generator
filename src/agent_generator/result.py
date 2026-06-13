"""Engine status/result value objects.

Lightweight dataclasses returned by introspection methods (``AgentGenerator.status`` /
``info``). Generation results themselves are the typed contracts in
``agent_generator.contracts``; this module only covers engine-level metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class EngineInfo:
    """Static description of the engine surface."""

    engine: str
    package_version: str
    api_version: str
    contracts_version: str
    frameworks: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class EngineStatus:
    """Runtime status, shaped to match the Matrix Builder adapter ``status()`` payload."""

    mode: str
    status: str
    engine: str
    boundary: str = "matrix-builder-orchestrates-agent-generator-generates"

    def as_dict(self) -> dict[str, str]:
        return {
            "mode": self.mode,
            "status": self.status,
            "engine": self.engine,
            "boundary": self.boundary,
        }


__all__ = ["EngineInfo", "EngineStatus"]
