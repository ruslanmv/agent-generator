"""Control layer — the trust mechanics that keep AI coders inside the contract.

* ``contract`` — immutable blueprint hash-locking (Batch 5).
* ``contract_spec`` — the contract a submission is validated against.
* ``submission`` — normalize request / repo / ZIP / diff into one shape.
* ``checks`` / ``secrets`` — the policy checks.
* ``validator`` — the single validation authority.
* ``repair`` — minimal, bounded repair prompts.
"""

from __future__ import annotations

from agent_generator.control.contract import (
    BlueprintContract,
    build_contract,
    compute_contract_hash,
)
from agent_generator.control.contract_spec import ContractSpec, build_contract_spec
from agent_generator.control.repair import build_repair_prompt
from agent_generator.control.snapshot import (
    DiffResult,
    build_commit_manifest,
    diff_submissions,
    tree_hash,
)
from agent_generator.control.submission import (
    Submission,
    from_patch,
    from_request,
    scan_repo,
    scan_zip,
)
from agent_generator.control.validator import validate_submission

__all__ = [
    "BlueprintContract",
    "build_contract",
    "compute_contract_hash",
    "ContractSpec",
    "build_contract_spec",
    "Submission",
    "from_patch",
    "from_request",
    "scan_repo",
    "scan_zip",
    "validate_submission",
    "build_repair_prompt",
    "tree_hash",
    "diff_submissions",
    "DiffResult",
    "build_commit_manifest",
]
