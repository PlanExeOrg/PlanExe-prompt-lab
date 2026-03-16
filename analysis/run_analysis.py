#!/usr/bin/env python3
"""
Run the full analysis pipeline: insight → code review → synthesis → assessment.

Each phase is resumable — if the output files already exist, the phase is
skipped. Assessment is skipped for index-0 analysis directories (no "before"
to compare against).

Usage:
    python analysis/run_analysis.py analysis/22_identify_potential_levers
    python analysis/run_analysis.py analysis/22_identify_potential_levers --timeout 900
"""
import argparse
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

DEFAULT_TIMEOUT = 600  # 10 minutes

PHASES = [
    ("run_insight.py", "Insight analysis (phase 1)"),
    ("run_code_review.py", "Code review (phase 2)"),
    ("run_synthesis.py", "Synthesis (phase 3)"),
]


def main():
    parser = argparse.ArgumentParser(
        description="Run the full analysis pipeline: insight → code review → synthesis → assessment.",
    )
    parser.add_argument(
        "analysis_dir",
        help="Relative path to the analysis directory (e.g. analysis/22_identify_potential_levers)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Per-agent timeout in seconds, passed to each phase (default: {DEFAULT_TIMEOUT})",
    )
    args = parser.parse_args()

    analysis_dir: str = args.analysis_dir
    analysis_path = REPO_ROOT / analysis_dir
    if not analysis_path.is_dir():
        sys.exit(f"ERROR: Directory not found: {analysis_path}")

    if not (analysis_path / "meta.json").is_file():
        sys.exit(f"ERROR: No meta.json found in {analysis_path}")

    # Assessment only makes sense from index 1 onward (needs a "before").
    index = int(analysis_path.name.split("_", 1)[0])

    phases = list(PHASES)
    if index > 0:
        phases.append(("run_assessment.py", "Assessment (phase 4)"))

    print(f"Analysis pipeline for: {analysis_dir}")
    print(f"  Phases: {len(phases)}")
    print(f"  Timeout: {args.timeout}s per agent")
    print()

    failed = []

    for script_name, label in phases:
        print("=" * 60)
        print(f"Analysis: {label}")
        print("=" * 60)

        script_path = SCRIPT_DIR / script_name
        cmd = [
            sys.executable, str(script_path),
            str(analysis_dir),
            "--timeout", str(args.timeout),
        ]
        result = subprocess.run(cmd, cwd=REPO_ROOT)

        if result.returncode != 0:
            print(f"WARNING: {script_name} exited with code {result.returncode}")
            failed.append(script_name)
        else:
            print(f"{label} completed successfully")

        print()

    # Summary.
    print("=" * 60)
    print("Analysis pipeline complete")
    print("=" * 60)

    if failed:
        print(f"  Failed phases: {', '.join(failed)}")
        sys.exit(1)
    else:
        print("  All phases succeeded")


if __name__ == "__main__":
    main()
