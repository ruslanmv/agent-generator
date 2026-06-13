"""Engine and contract versioning.

The PyPI package version (``agent_generator.__version__``) and the Matrix engine API
version are tracked separately:

* ``__version__`` is the released package version.
* ``ENGINE_API_VERSION`` is the major version of the ``AgentGenerator`` SDK surface; it
  changes only when the public method signatures change incompatibly.
* ``CONTRACTS_VERSION`` (in ``agent_generator.contracts``) tracks the shared data shapes.

Compatibility note: matrix-definitions declares ``agent_generator >= 0.2.0``. That package
bump is intentionally deferred to the end of Batch 3 (standards loader), when the engine can
actually load and verify a signed standards pack. Until then the package stays at its current
version and this module advertises the engine surface that already exists.
"""

from __future__ import annotations

from agent_generator import __version__ as PACKAGE_VERSION

#: Major version of the public ``AgentGenerator`` SDK surface.
ENGINE_API_VERSION = "1"

#: Target package version that unlocks matrix-definitions compatibility (end of Batch 3).
DEFINITIONS_COMPATIBLE_VERSION = "0.2.0"


def engine_version() -> str:
    """Return the running package version string."""
    return PACKAGE_VERSION


__all__ = [
    "PACKAGE_VERSION",
    "ENGINE_API_VERSION",
    "DEFINITIONS_COMPATIBLE_VERSION",
    "engine_version",
]
