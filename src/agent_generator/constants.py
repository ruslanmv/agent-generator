# src/agent_generator/constants.py
# ---------------------------------------------------------------------------#
#  Central, single‑source list of the target frameworks agent‑generator       #
#  can emit. This file must be imported—*never duplicated*—by the CLI,        #
#  wizard, backend proxy, validators, and unit tests.                         #
# ---------------------------------------------------------------------------#

from __future__ import annotations

from enum import Enum, unique
from typing import Tuple, Final

__all__ = ["Framework", "SUPPORTED_FRAMEWORKS"]


@unique
class Framework(str, Enum):
    """Enumerates every supported build/runtime framework."""

    WATSONX_ORCHESTRATE: str = "watsonx_orchestrate"
    CREWAI: str = "crewai"
    LANGRAPH: str = "langraph"
    BEEAI: str = "beeai"
    REACT: str = "react"  # react‑py or any “React agents” flavour

    # --------------------------------------------------------------------- #
    # Helper utilities                                                      #
    # --------------------------------------------------------------------- #
    @classmethod
    def default(cls) -> "Framework":
        """Return the default framework used when the user provides none."""
        return cls.WATSONX_ORCHESTRATE

    @classmethod
    def choices(cls) -> Tuple[str, ...]:
        """
        Return the allowed values as a tuple of lowercase strings.

        Useful for Typer / Click `show_choices=True` or argcomplete.
        """
        return tuple(fr.value for fr in cls)


# Immutable tuple for ultra‑fast membership tests and CLI choices
SUPPORTED_FRAMEWORKS: Final[Tuple[str, ...]] = Framework.choices()
