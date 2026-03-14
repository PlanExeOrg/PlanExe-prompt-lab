#!/usr/bin/env python3
"""
Run Claude Code to synthesize all insight and code review files for an analysis
step into a ranked list of 5 directions and 1 top recommendation.

Usage:
    python analysis/run_synthesis.py analysis/0_identify_potential_levers
"""
import argparse
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
PLANEXE_ROOT = Path("/Users/neoneye/git/PlanExeGroup/PlanExe")

# PlanExe source files the agent may want to inspect.
SOURCE_FILES = [
    "worker_plan/worker_plan_internal/lever/identify_potential_levers.py",
    "prompt_optimizer/runner.py",
]

PROMPT_TEMPLATE = """\
You are a synthesis agent. Your job is to read all analysis artifacts for a
single pipeline step and produce a clear, prioritized action plan.

## Inputs

The analysis directory is: `{analysis_dir}/`

Read every file in that directory:
- `meta.json` — provenance (which prompt and history runs were analyzed)
- `insight_*.md` — independent quality analyses from different agents
- `code_*.md` — independent code reviews from different agents

Also read the PlanExe source files so you can verify claims and assess
feasibility:
{source_file_list}

The PlanExe repo is at: {planexe_root}
The prompt-lab repo is at: {repo_root}

## Task

1. Read all insight and code review files carefully.
2. Identify every hypothesis (H1, H2, …), bug (B1, B2, …), improvement (I1,
   I2, …), and suspect pattern (S1, S2, …) across all files.
3. Cross-reference: where do agents agree? Where do they disagree? Verify
   disputed claims by reading the actual source code.
4. Rank the top 5 directions by expected impact, considering:
   - How many models/runs are affected
   - Whether it's a code fix (benefits all models) vs prompt tweak (may only
     help some)
   - Evidence strength (confirmed bug vs hypothesis vs suspicion)
   - Implementation difficulty
5. From those 5, pick the single best recommendation to pursue first.

## Output format

Write your synthesis to: `{output_file}`

Use this structure:

```
# Synthesis

## Cross-Agent Agreement
(Where do the insight/code review files agree? Summarize the consensus.)

## Cross-Agent Disagreements
(Where do they disagree? Who is right, based on your own source code reading?)

## Top 5 Directions

### 1. [Title]
- **Type**: code fix / prompt change / workflow change
- **Evidence**: which agents flagged this, which bugs/hypotheses
- **Impact**: which runs/models/metrics improve
- **Effort**: low / medium / high
- **Risk**: what could go wrong

### 2. [Title]
...

### 5. [Title]
...

## Recommendation
(Pick one. Explain why it should be done first. Be specific about what to
change — file, line, the fix. If it's a prompt change, draft the new wording.)

## Deferred Items
(Anything worth doing later but not first.)
```

Do not write any other files.
"""


def load_analysis_files(analysis_path: Path) -> str:
    """Concatenate all .md files from the analysis directory."""
    parts = []
    for f in sorted(analysis_path.glob("*.md")):
        parts.append(f"### {f.name}\n\n{f.read_text()}")
    if not parts:
        sys.exit(f"ERROR: No .md files found in {analysis_path}")
    return "\n\n---\n\n".join(parts)


def build_prompt(analysis_dir: str) -> str:
    output_file = f"{analysis_dir}/synthesis.md"
    source_file_list = "\n".join(
        f"- `{PLANEXE_ROOT / f}`" for f in SOURCE_FILES
    )
    return PROMPT_TEMPLATE.format(
        analysis_dir=analysis_dir,
        output_file=output_file,
        source_file_list=source_file_list,
        planexe_root=PLANEXE_ROOT,
        repo_root=REPO_ROOT,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Run synthesis agent (Claude Code) to produce a ranked action plan.",
    )
    parser.add_argument(
        "analysis_dir",
        help="Relative path to the analysis step directory (e.g. analysis/0_identify_potential_levers)",
    )
    args = parser.parse_args()

    analysis_dir: str = args.analysis_dir
    analysis_path = REPO_ROOT / analysis_dir
    if not analysis_path.is_dir():
        sys.exit(f"ERROR: Directory not found: {analysis_path}")

    # Check that insight files exist (phase 1 must have run).
    insight_files = list(analysis_path.glob("insight_*.md"))
    if not insight_files:
        sys.exit(f"ERROR: No insight_*.md files in {analysis_path}. Run run_insight.py first.")

    # Check PlanExe source files exist.
    for f in SOURCE_FILES:
        path = PLANEXE_ROOT / f
        if not path.is_file():
            sys.exit(f"ERROR: PlanExe source file not found: {path}")

    prompt = build_prompt(analysis_dir)

    print(f"Starting synthesis for: {analysis_dir}")
    print(f"  Output → {analysis_dir}/synthesis.md")
    print()

    result = subprocess.run(
        [
            "claude",
            "-p", prompt,
            "--allowedTools", "Read,Glob,Grep,Write",
            "--add-dir", str(REPO_ROOT),
            "--add-dir", str(PLANEXE_ROOT),
            "--model", "sonnet",
        ],
        cwd=REPO_ROOT,
    )

    print()
    print("═" * 50)
    print("Results")
    print("═" * 50)

    if result.returncode != 0:
        print(f"  Claude Code exited with code {result.returncode}")
    else:
        print("  Claude Code finished successfully")

    print()
    output_file = analysis_path / "synthesis.md"
    if output_file.is_file():
        size = output_file.stat().st_size
        print(f"  {output_file.relative_to(REPO_ROOT)}  ({size} bytes)")
    else:
        print("  (synthesis.md not found)")


if __name__ == "__main__":
    main()
