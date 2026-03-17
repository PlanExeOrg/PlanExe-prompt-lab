#!/usr/bin/env python3
"""
Run Claude Code to synthesize all insight and code review files for an analysis
step into a ranked list of 5 directions and 1 top recommendation.

Usage:
    python analysis/run_synthesis.py analysis/0_identify_potential_levers
"""
import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from event_log import emit_event


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

DEFAULT_TIMEOUT = 900  # 15 minutes
PLANEXE_ROOT = Path("/Users/neoneye/git/PlanExeGroup/PlanExe")

# PlanExe source files the agent may want to inspect.
SOURCE_FILES = [
    "worker_plan/worker_plan_internal/lever/identify_potential_levers.py",
    "self_improve/runner.py",
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
{pr_section}
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
   - Token cost: fixes that prevent wasted retries (e.g., removing hard schema
     constraints that reject valid output) have outsized impact on cost and
     success rate
   - **Content quality**: a change that improves the credibility and groundedness
     of ALL successful plans is higher-impact than one that recovers a single
     failed plan. Content quality regressions (verbosity, fabricated numbers,
     marketing-copy tone) that affect 34/35 plans outweigh structural fixes
     that affect 1/35.
   - **OPTIMIZE_INSTRUCTIONS alignment**: Read the `OPTIMIZE_INSTRUCTIONS`
     constant near the top of `identify_potential_levers.py`. Proposed changes
     should move toward its goals (realistic, feasible, actionable plans) and
     avoid its known pitfalls (optimism bias, fabricated numbers, marketing
     language, vague aspirations, fragile English-only validation). If a
     direction would improve OPTIMIZE_INSTRUCTIONS itself (e.g., documenting
     a new recurring problem), note that.
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

Do not write any other files. Do not modify meta.json or events.jsonl.
"""


def build_pr_section(meta_obj: dict) -> str:
    """Build a PR context section for the synthesis prompt."""
    if "pr_url" not in meta_obj:
        return ""

    pr_title = meta_obj.get("pr_title", "unknown")
    pr_desc = meta_obj.get("pr_description", "")

    return f"""
## PR Under Evaluation

This analysis evaluates the impact of a specific PR:
- **PR**: {meta_obj["pr_url"]}
- **Title**: {pr_title}
- **Description**: {pr_desc}

When ranking directions and writing the recommendation, consider whether the
PR's change is effective. If insight or code review files include a PR Impact
verdict (KEEP/REVERT/CONDITIONAL), factor that into your synthesis.
"""


def load_analysis_files(analysis_path: Path) -> str:
    """Concatenate all .md files from the analysis directory."""
    parts = []
    for f in sorted(analysis_path.glob("*.md")):
        parts.append(f"### {f.name}\n\n{f.read_text()}")
    if not parts:
        sys.exit(f"ERROR: No .md files found in {analysis_path}")
    return "\n\n---\n\n".join(parts)


def build_prompt(analysis_dir: str, pr_section: str) -> str:
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
        pr_section=pr_section,
    )


def _stderr_tail(proc: subprocess.Popen, max_chars: int = 500) -> str:
    """Read the tail of a process's stderr (must use stderr=PIPE)."""
    if proc.stderr is None:
        return ""
    raw = proc.stderr.read()
    text = raw.decode("utf-8", errors="replace").strip()
    return text[-max_chars:] if text else ""


def main():
    parser = argparse.ArgumentParser(
        description="Run synthesis agent (Claude Code) to produce a ranked action plan.",
    )
    parser.add_argument(
        "analysis_dir",
        help="Relative path to the analysis step directory (e.g. analysis/0_identify_potential_levers)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Timeout in seconds (default: {DEFAULT_TIMEOUT})",
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

    # Load meta.json for PR info.
    meta_path = analysis_path / "meta.json"
    meta_obj = {}
    if meta_path.is_file():
        meta_obj = json.loads(meta_path.read_text())

    pr_section = build_pr_section(meta_obj)
    prompt = build_prompt(analysis_dir, pr_section)

    events_path = analysis_path / "events.jsonl"
    synthesis_output = analysis_path / "synthesis.md"

    if synthesis_output.is_file():
        size = synthesis_output.stat().st_size
        print(f"synthesis.md already exists ({size} bytes) — nothing to do.")
        emit_event(events_path, "synthesis_claude_complete",
                   status="ok", skipped="already_exists")
        return

    print(f"Starting synthesis for: {analysis_dir}")
    if "pr_url" in meta_obj:
        print(f"  PR: {meta_obj.get('pr_title', 'unknown')}")
    print(f"  Output → {analysis_dir}/synthesis.md")
    print()

    timeout = args.timeout
    t0 = time.monotonic()
    proc = subprocess.Popen(
        [
            "claude",
            "-p", prompt,
            "--allowedTools", "Read,Glob,Grep,Write",
            "--add-dir", str(REPO_ROOT),
            "--add-dir", str(PLANEXE_ROOT),
            "--model", "sonnet",
        ],
        cwd=REPO_ROOT,
        start_new_session=True,
        stderr=subprocess.PIPE,
    )
    emit_event(events_path, "synthesis_claude_start", pid=proc.pid)

    timed_out = False
    try:
        exit_code = proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        proc.wait()
        timed_out = True
        exit_code = None

    duration = round(time.monotonic() - t0, 2)
    stderr_text = _stderr_tail(proc)
    if timed_out:
        emit_event(events_path, "synthesis_claude_error",
                   error=f"timed out after {timeout}s",
                   duration_seconds=duration,
                   **({"stderr_tail": stderr_text} if stderr_text else {}))
        synthesis_output.write_text(
            "# ERROR: claude timed out\n\n"
            f"Claude Code exceeded the {timeout}s time limit.\n"
            "See events.jsonl for details.\n"
        )
    elif exit_code == 0:
        emit_event(events_path, "synthesis_claude_complete",
                   status="ok", duration_seconds=duration)
    else:
        emit_event(events_path, "synthesis_claude_error",
                   error=f"exit code {exit_code}", duration_seconds=duration,
                   **({"stderr_tail": stderr_text} if stderr_text else {}))

    print()
    print("═" * 50)
    print("Results")
    print("═" * 50)

    if timed_out:
        print(f"  Claude Code timed out after {timeout}s (killed)")
    elif exit_code != 0:
        print(f"  Claude Code exited with code {exit_code}")
    else:
        print("  Claude Code finished successfully")

    print()
    if synthesis_output.is_file():
        size = synthesis_output.stat().st_size
        print(f"  {synthesis_output.relative_to(REPO_ROOT)}  ({size} bytes)")
    else:
        print("  (synthesis.md not found)")

    if timed_out or (exit_code is not None and exit_code != 0):
        sys.exit(1)


if __name__ == "__main__":
    main()
