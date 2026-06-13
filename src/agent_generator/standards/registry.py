"""Standards registry — resolve and cache the active pack and its profiles."""

from __future__ import annotations

from pathlib import Path

from agent_generator.contracts.common import JsonDict, QualityLevel
from agent_generator.standards.compatibility import check_compatibility
from agent_generator.standards.loader import load_pack, load_profile
from agent_generator.standards.models import CompatibilityResult, Profile, StandardsPack


class StandardsRegistry:
    """Resolves the current standards pack and exposes it to the engine.

    Caches the loaded pack and profiles so repeated generations in one process do not
    re-read and re-verify the pack each time.
    """

    def __init__(
        self,
        root: str | Path | None = None,
        *,
        verify: bool = True,
        signature_mode: str = "warn",
    ) -> None:
        self.root = root
        self.verify = verify
        self.signature_mode = signature_mode
        self._pack: StandardsPack | None = None
        self._profiles: dict[str, Profile] = {}

    def current(self) -> StandardsPack:
        if self._pack is None:
            self._pack = load_pack(
                self.root, verify=self.verify, signature_mode=self.signature_mode
            )
        return self._pack

    def profile(self, name: QualityLevel | str) -> Profile:
        key = name.value if isinstance(name, QualityLevel) else str(name)
        if key not in self._profiles:
            self._profiles[key] = load_profile(self.root, key)
        return self._profiles[key]

    def compatibility(self) -> CompatibilityResult:
        return check_compatibility(self.current().manifest)

    def metadata(self) -> JsonDict:
        """Shape for an ``/api/v1/standards/current`` style response."""
        pack = self.current()
        compat = self.compatibility()
        sig = pack.signature
        return {
            "pack_id": pack.pack_id,
            "version": pack.version,
            "status": pack.manifest.status,
            "owner": pack.manifest.owner,
            "brand": pack.manifest.brand,
            "website": pack.manifest.website,
            "combined_digest": f"sha256:{pack.combined_digest}",
            "rule_count": len(pack.rules),
            "checksums_ok": bool(pack.checksums and pack.checksums.ok),
            "signature_mode": sig.mode if sig else "unknown",
            "signature_verified": bool(sig and sig.verified),
            "compatibility": {
                "ok": compat.ok,
                "requirement": compat.requirement,
                "actual": compat.actual,
            },
            "warnings": list(pack.warnings),
        }


__all__ = ["StandardsRegistry"]
