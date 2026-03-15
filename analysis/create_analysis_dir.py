#!/usr/bin/env python3
"""
Create a new analysis directory with meta.json that includes all history runs
not yet covered by any previous analysis for the given step.

Scans all existing analysis directories for the step, collects the union of
already-analyzed history runs, then diffs against the full set of history runs
on disk. The new analysis directory gets an auto-incremented index.

Each analysis directory captures a snapshot of runs produced under the same
code/prompt configuration. When a PR changes PlanExe (e.g., removing a Pydantic
max_length constraint), the experiments run after that change land in new history
runs. This script ensures those new runs get their own analysis directory so the
assessment phase can compare "before" vs "after" cleanly.

Usage:
    python analysis/create_analysis_dir.py identify_potential_levers
    python analysis/create_analysis_dir.py identify_potential_levers --dry-run
"""
import argparse
import json
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent


def find_analysis_dirs(step_name: str) -> list[Path]:
    """Find all existing analysis directories for this step, sorted by index."""
    analysis_root = REPO_ROOT / "analysis"
    dirs = sorted(analysis_root.glob(f"*_{step_name}"))
    return [d for d in dirs if d.is_dir()]


def collect_analyzed_runs(analysis_dirs: list[Path]) -> set[str]:
    """Read meta.json from each analysis dir and collect all history run paths."""
    analyzed = set()
    for d in analysis_dirs:
        meta_path = d / "meta.json"
        if not meta_path.is_file():
            continue
        meta = json.loads(meta_path.read_text())
        for run in meta.get("history", []):
            analyzed.add(run)
    return analyzed


def find_all_history_runs(step_name: str) -> list[str]:
    """Scan history/ for all runs matching the step name, sorted by counter."""
    history_root = REPO_ROOT / "history"
    if not history_root.exists():
        return []
    runs = []
    for bucket_dir in sorted(history_root.iterdir()):
        if not bucket_dir.is_dir() or not bucket_dir.name.isdigit():
            continue
        for run_dir in sorted(bucket_dir.iterdir()):
            if not run_dir.is_dir():
                continue
            # Match pattern: {counter}_{step_name}
            parts = run_dir.name.split("_", 1)
            if len(parts) == 2 and parts[0].isdigit() and parts[1] == step_name:
                rel = f"{bucket_dir.name}/{run_dir.name}"
                runs.append(rel)
    return runs


def resolve_prompt_ref(step_name: str, new_runs: list[str]) -> str:
    """Determine the prompt reference from the history runs' meta.json files.

    Reads the system_prompt_sha256 from each run and finds the matching
    prompt file under prompts/{step_name}/. If runs use different prompts,
    uses the one from the most recent run.
    """
    sha256 = None
    for run in reversed(new_runs):
        run_meta = REPO_ROOT / "history" / run / "meta.json"
        if run_meta.is_file():
            meta = json.loads(run_meta.read_text())
            sha256 = meta.get("system_prompt_sha256")
            if sha256:
                break

    if not sha256:
        # Fall back to the latest prompt file on disk.
        prompts_dir = REPO_ROOT / "prompts" / step_name
        prompt_files = sorted(prompts_dir.glob("prompt_*.txt"))
        if not prompt_files:
            sys.exit(f"ERROR: No prompt files found in {prompts_dir}")
        return f"{step_name}/{prompt_files[-1].name}"

    # Find the prompt file with this sha256 in the filename.
    prompts_dir = REPO_ROOT / "prompts" / step_name
    matches = list(prompts_dir.glob(f"prompt_*_{sha256}.txt"))
    if matches:
        return f"{step_name}/{matches[0].name}"

    # sha256 not in any filename — fall back to latest.
    prompt_files = sorted(prompts_dir.glob("prompt_*.txt"))
    if not prompt_files:
        sys.exit(f"ERROR: No prompt files found in {prompts_dir}")
    return f"{step_name}/{prompt_files[-1].name}"


def get_next_index(step_name: str) -> int:
    """Find the next available analysis directory index."""
    analysis_dirs = find_analysis_dirs(step_name)
    if not analysis_dirs:
        return 0
    last_name = analysis_dirs[-1].name
    parts = last_name.split("_", 1)
    return int(parts[0]) + 1


def main():
    parser = argparse.ArgumentParser(
        description="Create a new analysis directory with meta.json for unanalyzed history runs.",
    )
    parser.add_argument(
        "step_name",
        help="Pipeline step name (e.g. identify_potential_levers)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be created without writing anything.",
    )
    args = parser.parse_args()

    step_name: str = args.step_name

    # 1. Find all history runs for this step.
    all_runs = find_all_history_runs(step_name)
    if not all_runs:
        sys.exit(f"ERROR: No history runs found for step '{step_name}'")

    # 2. Find already-analyzed runs across all analysis dirs.
    analysis_dirs = find_analysis_dirs(step_name)
    analyzed = collect_analyzed_runs(analysis_dirs)

    # 3. Compute new runs.
    new_runs = [r for r in all_runs if r not in analyzed]
    if not new_runs:
        print(f"No new history runs to analyze for '{step_name}'.")
        print(f"  Total history runs: {len(all_runs)}")
        print(f"  Already analyzed:   {len(analyzed)}")
        sys.exit(0)

    # 4. Resolve prompt reference.
    prompt_ref = resolve_prompt_ref(step_name, new_runs)

    # 5. Determine the new directory.
    index = get_next_index(step_name)
    new_dir = REPO_ROOT / "analysis" / f"{index}_{step_name}"

    # 6. Build meta.json content.
    meta = {
        "prompt": prompt_ref,
        "history": new_runs,
    }

    print(f"Step: {step_name}")
    print(f"Total history runs:   {len(all_runs)}")
    print(f"Already analyzed:     {len(analyzed)}")
    print(f"New runs to analyze:  {len(new_runs)}")
    for run in new_runs:
        print(f"  history/{run}")
    print(f"Prompt: {prompt_ref}")
    print(f"New analysis dir: {new_dir.relative_to(REPO_ROOT)}")

    if args.dry_run:
        print("\n(dry run — nothing written)")
        print(json.dumps(meta, indent=2))
        return

    # 7. Create directory and write meta.json.
    new_dir.mkdir(parents=True, exist_ok=True)
    meta_path = new_dir / "meta.json"
    meta_path.write_text(json.dumps(meta, indent=2) + "\n")

    print(f"\nCreated: {meta_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
