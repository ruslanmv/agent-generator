"""Batch 5 — blueprint contract hash-locking."""

from __future__ import annotations

from agent_generator.control.contract import build_contract, compute_contract_hash


def test_hash_is_order_independent() -> None:
    a = {"MATRIX_BLUEPRINT.yaml": "x", "MATRIX_STANDARDS.lock": "y"}
    b = {"MATRIX_STANDARDS.lock": "y", "MATRIX_BLUEPRINT.yaml": "x"}
    assert compute_contract_hash(a) == compute_contract_hash(b)


def test_hash_changes_when_content_changes() -> None:
    base = {"MATRIX_BLUEPRINT.yaml": "x", "MATRIX_STANDARDS.lock": "y"}
    tampered = {"MATRIX_BLUEPRINT.yaml": "x!", "MATRIX_STANDARDS.lock": "y"}
    assert compute_contract_hash(base) != compute_contract_hash(tampered)


def test_contract_verify_detects_tampering() -> None:
    files = {"MATRIX_BLUEPRINT.yaml": "blueprint", "MATRIX_STANDARDS.lock": "lock"}
    contract = build_contract("bp-1", "1.0.0", files)

    assert contract.verify(files) is True
    assert contract.verify({**files, "MATRIX_BLUEPRINT.yaml": "edited"}) is False
    # Missing an immutable file also fails.
    assert contract.verify({"MATRIX_BLUEPRINT.yaml": "blueprint"}) is False
