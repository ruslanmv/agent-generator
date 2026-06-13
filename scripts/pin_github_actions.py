#!/usr/bin/env python3
"""Pin GitHub Actions to full commit SHAs (Ruslan Magana Definition GHA-002).

Third-party actions referenced by mutable tags (``@v4``) can change underneath CI. GHA-002
requires pinning every ``uses:`` to a full 40-character commit SHA, with the human-readable
tag preserved as a trailing comment.

Modes
-----
``--check`` (default)
    List every unpinned ``uses:`` reference and exit non-zero if any are found. Needs no
    network — suitable as a CI gate.

``--apply``
    Resolve each tag to its commit SHA via the GitHub API and rewrite the workflow files
    in place. Set ``GITHUB_TOKEN`` (or ``GH_TOKEN``) to avoid unauthenticated rate limits.

This keeps pinning reproducible and auditable instead of a one-off manual edit that drifts.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

WORKFLOWS_DIR = Path(__file__).resolve().parents[1] / ".github" / "workflows"

# uses: owner/repo@ref   (ignores local ./actions and docker:// references)
_USES = re.compile(r"^(?P<indent>\s*)(?P<key>-?\s*uses:\s*)(?P<ref>[^\s#]+)(?P<rest>.*)$")
_SHA = re.compile(r"^[0-9a-f]{40}$")


def _iter_uses(text: str):
    for lineno, line in enumerate(text.splitlines(), start=1):
        match = _USES.match(line)
        if not match:
            continue
        ref = match.group("ref")
        if ref.startswith((".", "docker://")):
            continue
        if "@" not in ref:
            continue
        action, _, version = ref.partition("@")
        yield lineno, line, match, action, version


def _is_pinned(version: str) -> bool:
    return bool(_SHA.match(version))


def _resolve_sha(action: str, version: str, token: str | None) -> str:
    owner_repo = "/".join(action.split("/")[:2])
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "pin-github-actions"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    for ref_kind in ("tags", "heads"):
        url = f"https://api.github.com/repos/{owner_repo}/git/refs/{ref_kind}/{version}"
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310
                import json

                data = json.load(resp)
        except urllib.error.HTTPError:
            continue
        obj = data.get("object", {})
        sha = obj.get("sha")
        if obj.get("type") == "tag":  # annotated tag -> dereference to commit
            tag_url = f"https://api.github.com/repos/{owner_repo}/git/tags/{sha}"
            with urllib.request.urlopen(  # noqa: S310
                urllib.request.Request(tag_url, headers=headers), timeout=15
            ) as resp:
                import json

                sha = json.load(resp).get("object", {}).get("sha", sha)
        if sha:
            return sha
    raise RuntimeError(f"could not resolve {action}@{version}")


def check() -> int:
    unpinned: list[tuple[Path, int, str, str]] = []
    for path in sorted(WORKFLOWS_DIR.glob("*.yml")):
        for lineno, _line, _m, action, version in _iter_uses(path.read_text()):
            if not _is_pinned(version):
                unpinned.append((path, lineno, action, version))
    if not unpinned:
        print("OK: all GitHub Actions are SHA-pinned (GHA-002)")
        return 0
    print(f"GHA-002: {len(unpinned)} unpinned action reference(s):")
    for path, lineno, action, version in unpinned:
        print(f"  {path.name}:{lineno}  {action}@{version}")
    print("\nRun with --apply (and GITHUB_TOKEN set) to pin them.")
    return 1


def apply() -> int:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    cache: dict[tuple[str, str], str] = {}
    changed = 0
    for path in sorted(WORKFLOWS_DIR.glob("*.yml")):
        lines = path.read_text().splitlines(keepends=True)
        out: list[str] = []
        for raw in lines:
            line = raw.rstrip("\n")
            match = _USES.match(line)
            if not match:
                out.append(raw)
                continue
            ref = match.group("ref")
            action, _, version = ref.partition("@")
            if ref.startswith((".", "docker://")) or "@" not in ref or _is_pinned(version):
                out.append(raw)
                continue
            key = (action, version)
            if key not in cache:
                cache[key] = _resolve_sha(action, version, token)
            sha = cache[key]
            newline = f"{match.group('indent')}{match.group('key')}{action}@{sha}  # {version}\n"
            out.append(newline)
            changed += 1
        path.write_text("".join(out))
    print(f"Pinned {changed} action reference(s).")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="resolve and rewrite (needs network)")
    parser.add_argument("--check", action="store_true", help="list unpinned actions (default)")
    args = parser.parse_args()
    return apply() if args.apply else check()


if __name__ == "__main__":
    sys.exit(main())
