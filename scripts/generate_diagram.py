#!/usr/bin/env python3
# ────────────────────────────────────────────────────────────────
#  scripts/generate_diagram.py
# ────────────────────────────────────────────────────────────────
"""
Convert a saved workflow spec (JSON or YAML) into a Mermaid diagram,
and optionally an SVG via Mermaid CLI (`mmdc`).

Usage:
    python scripts/generate_diagram.py path/to/spec.json
    python scripts/generate_diagram.py spec.yaml -o diagram.mmd
    python scripts/generate_diagram.py spec.yaml -o diagram.svg

Requirements for SVG export:
    npm install -g @mermaid-js/mermaid-cli
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import yaml

# Attempt to import package modules; if running standalone, adjust PYTHONPATH
try:
    from agent_generator.models.workflow import Workflow
    from agent_generator.utils.visualizer import to_mermaid
except ImportError:  # pragma: no cover
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root / "src"))
    from agent_generator.models.workflow import Workflow
    from agent_generator.utils.visualizer import to_mermaid


def _load_spec(fp: Path) -> Workflow:
    """
    Read a JSON or YAML file and return a validated Workflow.
    """
    text = fp.read_text(encoding="utf-8")
    if fp.suffix in {".yaml", ".yml"}:
        data = yaml.safe_load(text)
    elif fp.suffix == ".json":
        data = json.loads(text)
    else:
        raise ValueError("Spec file must end with .json, .yaml, or .yml")
    return Workflow.model_validate(data)


def _export_svg(mermaid_src: str, svg_path: Path) -> None:
    """
    Call Mermaid CLI (`mmdc`) to convert Mermaid source to SVG.
    """
    try:
        subprocess.run(
            ["mmdc", "-i", "-", "-o", str(svg_path)],
            input=mermaid_src.encode("utf-8"),
            check=True,
        )
        print(f"✓ SVG written to {svg_path}")
    except FileNotFoundError:
        print("❌ Mermaid CLI (`mmdc`) not found. Install via npm: npm install -g @mermaid-js/mermaid-cli")
    except subprocess.CalledProcessError as exc:
        print("❌ mmdc error:", exc)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Mermaid or SVG diagrams from a workflow spec.")
    parser.add_argument("spec", type=Path, help="Path to workflow JSON or YAML file.")
    parser.add_argument(
        "-o", "--output", type=Path,
        help="Write Mermaid (.mmd) or SVG (.svg). Defaults to stdout for Mermaid."
    )
    args = parser.parse_args()

    wf = _load_spec(args.spec)
    mermaid_text = to_mermaid(wf)

    if not args.output:
        print(mermaid_text)
        return

    if args.output.suffix == ".mmd":
        args.output.write_text(mermaid_text, encoding="utf-8")
        print(f"✓ Mermaid saved to {args.output}")
    elif args.output.suffix == ".svg":
        _export_svg(mermaid_text, args.output)
    else:
        print("❌ Output extension must be .mmd or .svg")


if __name__ == "__main__":  # pragma: no cover
    main()
