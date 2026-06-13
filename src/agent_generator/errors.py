"""Engine-level error types.

A small, stable hierarchy so callers (Matrix Builder, the CLI, the HTTP facade) can catch
engine failures without depending on internal exception types from the planning, building,
or validation layers.
"""

from __future__ import annotations


class AgentGeneratorError(Exception):
    """Base class for all engine errors."""


class EngineUnavailableError(AgentGeneratorError):
    """The requested engine capability could not be initialized."""


class IdeaParseError(AgentGeneratorError):
    """An idea could not be parsed into a usable intent."""


class CandidateNotFoundError(AgentGeneratorError):
    """A requested blueprint candidate id was not found."""


class BlueprintError(AgentGeneratorError):
    """A controlled blueprint could not be produced."""


class StandardsError(AgentGeneratorError):
    """A standards pack could not be loaded or verified."""


class ValidationError(AgentGeneratorError):
    """Validation could not be performed (distinct from a failing validation result)."""


class ExportError(AgentGeneratorError):
    """A Matrix Bundle could not be exported."""


__all__ = [
    "AgentGeneratorError",
    "EngineUnavailableError",
    "IdeaParseError",
    "CandidateNotFoundError",
    "BlueprintError",
    "StandardsError",
    "ValidationError",
    "ExportError",
]
