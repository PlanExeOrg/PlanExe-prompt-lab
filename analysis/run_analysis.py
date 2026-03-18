#!/usr/bin/env python3
"""
Run the full analysis pipeline: insight → code review → synthesis → assessment.

Each phase is resumable — if the output files already exist, the phase is
skipped. Assessment is skipped for index-0 analysis directories (no "before"
to compare against).

Timeout handling:
  - Each phase gets up to ``--max-retries`` attempts (default 3).
  - On timeout or non-zero exit, error marker files (containing "# ERROR:")
    are cleaned up before retrying so the phase doesn't skip itself.
  - If all retries are exhausted, the pipeline stops.

Usage:
    python analysis/run_analysis.py analysis/22_identify_potential_levers
    python analysis/run_analysis.py analysis/22_identify_potential_levers --timeout 1200
    python analysis/run_analysis.py analysis/22_identify_potential_levers --max-retries 5
"""
import argparse
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

DEFAULT_TIMEOUT = 1200  # 20 minutes (up from 15)
DEFAULT_MAX_RETRIES = 3

PHASES = [
    ("run_insight.py", "Insight analysis (phase 1)"),
    ("run_code_review.py", "Code review (phase 2)"),
    ("run_synthesis.py", "Synthesis (phase 3)"),
]

# Output files produced by each phase.  Used to detect and clean up error
# marker files before retrying.
PHASE_OUTPUTS: dict[str, list[str]] = {
    "run_insight.py": ["insight_claude.md", "insight_codex.md"],
    "run_code_review.py": ["code_claude.md", "code_codex.md"],
    "run_synthesis.py": ["synthesis.md"],
    "run_assessment.py": ["assessment.md"],
}

ERROR_MARKER = "# ERROR:"


def _is_error_marker(path: Path) -> bool:
    """Return True if the file is an error placeholder (not a real result)."""
    if not path.is_file():
        return False
    try:
        # Only read the first 50 bytes — error markers start with "# ERROR:"
        with open(path, "r", encoding="utf-8") as f:
            head = f.read(50)
        return head.startswith(ERROR_MARKER)
    except Exception:
        return False


def _clean_error_markers(analysis_path: Path, script_name: str) -> int:
    """Remove error marker files for a phase so it can be retried.

    Returns the number of files removed.
    """
    removed = 0
    for filename in PHASE_OUTPUTS.get(script_name, []):
        p = analysis_path / filename
        if _is_error_marker(p):
            p.unlink()
            print(f"  Removed error marker: {filename}")
            removed += 1
    return removed


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
    parser.add_argument(
        "--max-retries",
        type=int,
        default=DEFAULT_MAX_RETRIES,
        help=f"Max attempts per phase before giving up (default: {DEFAULT_MAX_RETRIES})",
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
    print(f"  Max retries: {args.max_retries}")
    print()

    for script_name, label in phases:
        print("=" * 60)
        print(f"Analysis: {label}")
        print("=" * 60)

        script_path = SCRIPT_DIR / script_name

        succeeded = False
        for attempt in range(1, args.max_retries + 1):
            # Clean up error markers from previous failed attempts so
            # the phase script's resume logic doesn't skip it.
            _clean_error_markers(analysis_path, script_name)

            if attempt > 1:
                print(f"  Retry {attempt}/{args.max_retries}")

            cmd = [
                sys.executable, str(script_path),
                str(analysis_dir),
                "--timeout", str(args.timeout),
            ]
            result = subprocess.run(cmd, cwd=REPO_ROOT)

            if result.returncode == 0:
                succeeded = True
                break

            print(f"  {script_name} exited with code {result.returncode}")
            if attempt < args.max_retries:
                print(f"  Will retry ({attempt}/{args.max_retries} attempts used)")
            print()

        if not succeeded:
            print(f"ERROR: {script_name} failed after {args.max_retries} attempts")
            print(f"Stopping pipeline — later phases depend on this one.")
            print()
            print("=" * 60)
            print(f"Analysis pipeline STOPPED at: {label}")
            print("=" * 60)
            sys.exit(1)

        print(f"{label} completed successfully")
        print()

    # Summary.
    print("=" * 60)
    print("Analysis pipeline complete")
    print("=" * 60)
    print("  All phases succeeded")


if __name__ == "__main__":
    main()
