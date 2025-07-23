#!/usr/bin/env python3
"""
Timing measurements for the agent-generator workflow.

Run this script to see how long each major phase takes in both full-run and
dry-run modes, averaged over multiple runs.
"""

import argparse
import time
from pathlib import Path
from statistics import mean

# Third-party imports
from dotenv import load_dotenv

# Local application imports
# These are now all at the top, satisfying the linter.
from agent_generator.config import get_settings
from agent_generator.frameworks import FRAMEWORKS
from agent_generator.providers import PROVIDERS
from agent_generator.utils.parser import parse_natural_language_to_workflow
from agent_generator.utils.prompts import render_prompt


def measure_full_single(
    prompt: str, framework_name: str, provider_name: str
) -> dict[str, float]:
    """Single-run timings for the full LLM workflow."""
    timings: dict[str, float] = {}

    t0 = time.perf_counter()
    settings = get_settings()
    timings["settings_init"] = time.perf_counter() - t0

    t1 = time.perf_counter()
    workflow = parse_natural_language_to_workflow(prompt)
    timings["parse_workflow"] = time.perf_counter() - t1

    t2 = time.perf_counter()
    prompt_str = render_prompt(workflow, settings, framework_name)
    timings["render_prompt"] = time.perf_counter() - t2

    provider_cls = PROVIDERS[provider_name]
    t3 = time.perf_counter()
    provider_inst = provider_cls(settings)
    timings["provider_init"] = time.perf_counter() - t3

    t4 = time.perf_counter()
    if hasattr(provider_inst, "_get_iam_token"):
        try:
            provider_inst._get_iam_token()
        except Exception:
            pass  # Ignore errors for timing purposes
    timings["iam_fetch"] = time.perf_counter() - t4

    t5 = time.perf_counter()
    try:
        # Use minimal tokens for speed, we only care about the call overhead
        provider_inst.generate(prompt_str, max_tokens=1, temperature=0.0)
    except Exception:
        pass  # Ignore errors for timing purposes
    timings["llm_call"] = time.perf_counter() - t5

    t6 = time.perf_counter()
    FRAMEWORKS[framework_name]().generate_code(workflow, settings, mcp=False)
    timings["code_gen"] = time.perf_counter() - t6

    return timings


def measure_dry_single(prompt: str, framework_name: str) -> dict[str, float]:
    """Single-run timings for the dry-run (scaffold-only) workflow."""
    timings: dict[str, float] = {}

    t0 = time.perf_counter()
    settings = get_settings()
    timings["settings_init"] = time.perf_counter() - t0

    t1 = time.perf_counter()
    workflow = parse_natural_language_to_workflow(prompt)
    timings["parse_workflow"] = time.perf_counter() - t1

    t2 = time.perf_counter()
    # Dry-run skips rendering prompt and LLM; directly scaffolds
    FRAMEWORKS[framework_name]().generate_code(
        workflow,
        settings,
        mcp=False,
    )
    timings["code_gen"] = time.perf_counter() - t2

    return timings


def average_timings(single_fn, *args, runs: int) -> dict[str, float]:
    """Averages timings over multiple runs after a warm-up."""
    # Determine phases from the first run
    first_run_timings = single_fn(*args)
    phases = list(first_run_timings.keys())
    accum = {phase: [time] for phase, time in first_run_timings.items()}

    # Perform the rest of the runs
    for _ in range(runs - 1):
        run_timings = single_fn(*args)
        for phase, value in run_timings.items():
            if phase in accum:
                accum[phase].append(value)

    return {phase: mean(values) for phase, values in accum.items()}


def main() -> None:
    """Parse arguments and run the timing measurements."""
    # This is the correct place to load environment variables: inside the main
    # entry point, before any logic that needs them is executed.
    load_dotenv(dotenv_path=Path.cwd() / ".env", override=False)

    parser = argparse.ArgumentParser(
        description="Compare full vs dry-run timings for agent-generator workflows."
    )
    parser.add_argument("--prompt", default="Build an agent", help="Prompt text")
    parser.add_argument(
        "--framework", default="watsonx_orchestrate", help="Framework name"
    )
    parser.add_argument("--provider", default="watsonx", help="Provider name")
    parser.add_argument(
        "-n", "--runs", type=int, default=3, help="Number of runs to average"
    )
    args = parser.parse_args()

    # Add a warm-up run that isn't timed to account for initial caching, etc.
    print("Performing warm-up run...")
    measure_full_single(args.prompt, args.framework, args.provider)
    print("Warm-up complete.\n")

    print("Measuring timings for prompt and framework:")
    print(f"  Prompt:    '{args.prompt}'")
    print(f"  Framework: {args.framework}")
    print(f"  Provider:  {args.provider}")
    print(f"  Runs:      {args.runs}\n")

    full_avg = average_timings(
        measure_full_single, args.prompt, args.framework, args.provider, runs=args.runs
    )
    dry_avg = average_timings(
        measure_dry_single, args.prompt, args.framework, runs=args.runs
    )

    print("Average FULL-run timings (ms):")
    total_full = sum(full_avg.values())
    for phase, secs in full_avg.items():
        print(f"  {phase:15s}: {secs * 1000:7.1f} ms")
    print(f"  {'TOTAL':15s}: {total_full * 1000:7.1f} ms\n")

    print("Average DRY-run timings (ms):")
    total_dry = sum(dry_avg.values())
    for phase, secs in dry_avg.items():
        print(f"  {phase:15s}: {secs * 1000:7.1f} ms")
    print(f"  {'TOTAL':15s}: {total_dry * 1000:7.1f} ms")

    if total_full > 0:
        savings = (total_full - total_dry) / total_full * 100
        print(f"\n✅ Dry-run is {savings:.1f}% faster.")


if __name__ == "__main__":
    main()
