"""Pack-integrity validation.

Batch 3 scope: structural checks on a loaded pack and a profile. Full blueprint/policy
validation (evaluating generated repos against active rules) is Batch 8.
"""

from __future__ import annotations

import re

from agent_generator.standards.models import Profile, StandardsPack

_RULE_ID = re.compile(
    r"^(RMD|AGENT|ASVS|OWASP|SSDF|SLSA|SUPPLY|GHA|PY|FASTAPI|NEXT|FE|FRONTEND|DOCKER|OBS|MATRIXHUB|DOC|SEC|API)-[0-9]{3,4}$"
)
_KNOWN_STATUS = {"draft", "experimental", "stable", "deprecated", "placeholder"}


def validate_pack(pack: StandardsPack) -> list[str]:
    """Return a list of structural issues; empty means the pack is well-formed."""
    issues: list[str] = []
    if not pack.manifest.schema_version:
        issues.append("manifest missing schema_version")
    if pack.manifest.status not in _KNOWN_STATUS:
        issues.append(f"unknown pack status: {pack.manifest.status}")
    if not pack.rules:
        issues.append("pack defines no rules")
    for rule in pack.rules:
        if not _RULE_ID.match(rule.id):
            issues.append(f"invalid rule id: {rule.id}")
    if pack.checksums is not None and not pack.checksums.ok:
        issues.append(f"checksums not clean: {pack.checksums.summary}")
    return issues


def validate_profile_against_pack(profile: Profile, pack: StandardsPack) -> list[str]:
    """Return profile rule ids that do not match the rule-id format.

    Profiles may reference rules whose full definition lives outside the combined pack's
    summarized rule list, so unknown-but-well-formed ids are allowed; only malformed ids are
    reported here.
    """
    return [rid for rid in profile.required_rules if not _RULE_ID.match(rid)]


__all__ = ["validate_pack", "validate_profile_against_pack"]
