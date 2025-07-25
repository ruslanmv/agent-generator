# backend/agents/merger_agent.py

import logging
from pathlib import Path
from typing import List

from ..config import settings
from ..utils import relative_tree

logger = logging.getLogger(__name__)


class MergerAgent:
    """
    MergerAgent collects and returns a preview of all artefacts
    produced under build/<framework>. It is idempotent: running
    merge multiple times yields the same tree list.
    """

    def merge(self, framework: str) -> List[str]:
        """
        Walk the bundle directory and return a sorted list of
        its relative file and directory paths.

        Parameters
        ----------
        framework : str
            The framework subdirectory under settings.build_base,
            e.g. "watsonx_orchestrate".

        Returns
        -------
        List[str]
            Each entry ends with "/" if it’s a directory.
        """
        bundle = settings.build_base / framework
        if not bundle.exists():
            logger.warning(
                "Bundle directory %s does not exist; returning empty tree.", bundle
            )
            return []
        tree = relative_tree(bundle, exclude=("*.pyc", "__pycache__"))
        logger.info(
            "Bundle ready at %s (%d artefacts)", bundle, len(tree)
        )
        return tree
