"""Commit snapshots and diffs (Batch E2).

``tree_hash`` content-addresses a full bundle tree (order-independent sha over the LF-normalized
file map — the same recipe as the immutable contract hash). ``diff_submissions`` produces a
deterministic added/changed/deleted classification plus a byte-stable unified ``diff.patch``.
``build_commit_manifest`` packages a checkpoint. All are pure and newline-normalized, so a CRLF
working copy and its LF original hash and diff identically.
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass

from agent_generator.artifacts.canonical import normalize_newlines
from agent_generator.contracts.commit import CommitManifest
from agent_generator.contracts.common import ValidationStatus
from agent_generator.control.contract import compute_contract_hash
from agent_generator.control.submission import Submission


def _normalized_files(submission: Submission) -> dict[str, str]:
    return {path: normalize_newlines(content) for path, content in submission.files.items()}


def tree_hash(submission: Submission) -> str:
    """Order-independent ``sha256:`` digest over the LF-normalized full file tree."""
    return compute_contract_hash(_normalized_files(submission))


@dataclass(frozen=True)
class DiffResult:
    added: list[str]
    changed: list[str]
    deleted: list[str]
    patch: str

    @property
    def is_empty(self) -> bool:
        return not (self.added or self.changed or self.deleted)

    def changed_paths(self) -> list[str]:
        """All paths touched (added + changed + deleted), sorted."""
        return sorted(set(self.added) | set(self.changed) | set(self.deleted))


def diff_submissions(base: Submission, head: Submission) -> DiffResult:
    """Classify changes from ``base`` to ``head`` and render a deterministic unified patch."""
    b = _normalized_files(base)
    h = _normalized_files(head)
    added = sorted(set(h) - set(b))
    deleted = sorted(set(b) - set(h))
    changed = sorted(p for p in (set(b) & set(h)) if b[p] != h[p])
    return DiffResult(
        added=added,
        changed=changed,
        deleted=deleted,
        patch=_render_patch(b, h, added, changed, deleted),
    )


def _render_patch(
    b: dict[str, str],
    h: dict[str, str],
    added: list[str],
    changed: list[str],
    deleted: list[str],
) -> str:
    chunks: list[str] = []
    for path in sorted(set(added) | set(changed) | set(deleted)):
        base_lines = b.get(path, "").splitlines()
        head_lines = h.get(path, "").splitlines()
        from_file = "/dev/null" if path in added else f"a/{path}"
        to_file = "/dev/null" if path in deleted else f"b/{path}"
        body = "\n".join(
            difflib.unified_diff(
                base_lines, head_lines, fromfile=from_file, tofile=to_file, lineterm=""
            )
        )
        if body:
            chunks.append(f"diff --git a/{path} b/{path}\n{body}")
    return ("\n".join(chunks) + "\n") if chunks else ""


def build_commit_manifest(
    *,
    commit_no: int,
    head: Submission,
    base: Submission | None = None,
    parent_commit_ref: str | None = None,
    batch_ref: str | None = None,
    validation_status: ValidationStatus = ValidationStatus.NOT_RUN,
    summary: str = "",
) -> CommitManifest:
    """Build an immutable commit manifest for ``head`` (optionally diffed against ``base``)."""
    if base is not None:
        delta = diff_submissions(base, head)
        added, changed, deleted = delta.added, delta.changed, delta.deleted
    else:
        added, changed, deleted = sorted(head.files), [], []
    return CommitManifest(
        commit_no=commit_no,
        parent_commit_ref=parent_commit_ref,
        batch_ref=batch_ref,
        tree_hash=tree_hash(head),
        validation_status=validation_status,
        summary=summary,
        added=added,
        changed=changed,
        deleted=deleted,
    )


__all__ = ["tree_hash", "DiffResult", "diff_submissions", "build_commit_manifest"]
