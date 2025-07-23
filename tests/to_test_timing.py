#!/usr/bin/env python3
"""
Timing measurements for the agent-generator workflow.

Run this script to see how long each major phase takes, averaged over multiple runs.
"""

import argparse
import time
from statistics import mean

from agent_generator.config import get_settings
from agent_generator.frameworks import FRAMEWORKS
from agent_generator.providers import PROVIDERS
from agent_generator.utils.parser import parse_natural_language_to_workflow
from agent_generator.utils.prompts import render_prompt


def measure_timing_single(
    prompt: str, framework_name: str, provider_name: str
) -> dict[str, float]:
    """
    Measure and return timings (in seconds) for each phase of the workflow (single run).
    """
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
    # Only WatsonX needs IAM fetching; others will do nothing or internal cache
    if hasattr(provider_inst, "_get_iam_token"):
        try:
            provider_inst._get_iam_token()
        except Exception:
            pass
    timings["iam_fetch"] = time.perf_counter() - t4

    t5 = time.perf_counter()
    # perform minimal LLM call to measure overhead (use dry or low-cost settings if needed)
    try:
        provider_inst.generate(prompt_str, max_tokens=1, temperature=0.0)
    except Exception:
        # ignore errors from actual API call; we only care about timing
        pass
    timings["llm_call"] = time.perf_counter() - t5

    t6 = time.perf_counter()
    FRAMEWORKS[framework_name]().generate_code(workflow, settings, mcp=False)
    timings["code_gen"] = time.perf_counter() - t6

    return timings


def measure_timing(
    prompt: str, framework_name: str, provider_name: str, runs: int
) -> dict[str, float]:
    """
    Run multiple measurements and return average timings.
    """
    phases = [
        "settings_init",
        "parse_workflow",
        "render_prompt",
        "provider_init",
        "iam_fetch",
        "llm_call",
        "code_gen",
    ]
    all_timings = {phase: [] for phase in phases}

    # Warm‑up run to load modules, caches, etc.
    measure_timing_single(prompt, framework_name, provider_name)

    for _ in range(runs):
        run_timing = measure_timing_single(prompt, framework_name, provider_name)
        for phase in phases:
            all_timings[phase].append(run_timing[phase])

    return {phase: mean(all_timings[phase]) for phase in phases}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Measure timings for agent-generator workflow."
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

    print("Measuring workflow timings for:")
    print(f"  Prompt:    '{args.prompt}'")
    print(f"  Framework: {args.framework}")
    print(f"  Provider:  {args.provider}")
    print(f"  Runs:      {args.runs}\n")

    avg = measure_timing(args.prompt, args.framework, args.provider, args.runs)
    total = sum(avg.values())

    print("Average timings (ms):")
    for phase, secs in avg.items():
        print(f"  {phase:15s}: {secs * 1000:7.1f} ms")
    print(f"\nTotal time: {total * 1000:.1f} ms")


if __name__ == "__main__":
    main()
