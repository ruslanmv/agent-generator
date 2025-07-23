# ────────────────────────────────────────────────────────────────
# src/agent_generator/providers/__init__.py
# ────────────────────────────────────────────────────────────────
"""
LLM provider registry:
- Auto‑imports all in-package *_provider.py modules (so BaseProvider.__init_subclass__ can register them).
- Then pulls in any external plugins via setuptools entry‑points.
"""

import importlib
import importlib.metadata
import pkgutil

from .base import PROVIDERS as _internal_registry
from .base import BaseProvider

# 1) Dynamically import every *_provider.py in this package
#    so that BaseProvider.__init_subclass__ populates _internal_registry
_package_path = __path__[0]
for finder, module_name, is_pkg in pkgutil.iter_modules([_package_path]):
    if module_name.endswith("_provider"):
        importlib.import_module(f"{__name__}.{module_name}")

# 2) Discover any entry‑point–defined providers (for installed extras or plugins)
for ep in importlib.metadata.entry_points(group="agent_generator.providers"):
    _internal_registry[ep.name] = ep.load()

# 3) Expose the final registry
PROVIDERS: dict[str, type[BaseProvider]] = dict(_internal_registry)

__all__ = ["BaseProvider", "PROVIDERS"]
