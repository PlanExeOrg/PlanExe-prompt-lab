#!/usr/bin/env python3
"""
Run Claude Code and Codex in parallel to produce insight files for an analysis step.

Usage:
    python analysis/run_insight.py analysis/0_identify_potential_levers
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

DEFAULT_TIMEOUT = 600  # 10 minutes

PROMPT_TEMPLATE = """\
You are an analysis agent ("{agent_name}").

## Instructions

1. Read `analysis/AGENTS.md` for the full conventions you must follow.
2. The meta.json for this analysis step is shown below — it tells you which
   prompt and history runs to examine.
3. Produce a single insight file at `{output_file}`.

## Repository layout

The repo root is: {repo_root}

Key paths relative to the repo root:
- Baseline training data: `baseline/train/`
- Runner history outputs: `history/`
- Registered prompts: `prompts/`
- Analysis directory: `{analysis_dir}/`

## meta.json contents

```json
{meta_json}
```
{pr_impact_section}
## Requirements

- Follow the section structure from AGENTS.md (Negative Things, Positive Things,
  Comparison, Quantitative Metrics, Evidence Notes, Questions For Later Synthesis,
  Reflect, Potential Code Changes, Summary, etc.).
- Compute quantitative metrics: uniqueness counts, average field lengths,
  constraint violations, template leakage. Present them in tables.
- Label prompt hypotheses H1, H2, … and code hypotheses C1, C2, …
- Cite evidence from specific files (history run outputs, baseline data, prompt
  files). Do not rely on memory alone.
- Compare the history runs against the baseline training data.
- Keep claims auditable — quote or reference the exact artifact paths.
- Check events.jsonl for LLMChatError entries — these may indicate Pydantic
  schema validation failures (e.g., max_length exceeded) that discard entire
  LLM responses. Schema-level hard constraints that clash with model output
  tendencies waste tokens on retries and hurt success rates.
- **Content quality vs baseline**: Compare average field lengths (consequences,
  options, review) against the baseline training data. Report the ratio. A ratio
  above 2× is a warning sign — longer is not better if the extra length is
  fabricated numbers, marketing copy, or verbose restatements. Count fabricated
  percentage claims (e.g. "reduces costs by 30%") that have no basis in the
  project context. Flag marketing-copy language in strategic analysis fields.
- **OPTIMIZE_INSTRUCTIONS alignment**: Read the `OPTIMIZE_INSTRUCTIONS` constant
  near the top of `identify_potential_levers.py` (in the PlanExe repo). Check
  whether the current outputs align with its goals — realistic, feasible,
  actionable plans. Flag any violations of its known-problems list (optimism
  bias, fabricated numbers, marketing language, vague aspirations, fragile
  English-only validation). If you discover a recurring problem not yet listed
  in OPTIMIZE_INSTRUCTIONS, propose adding it.
{pr_impact_requirement}
## Output

Write your analysis to: `{output_file}`
Do not write any other files. Do not modify meta.json or events.jsonl.
"""


def find_before_dir(analysis_dir: str) -> str | None:
    """Find the analysis directory immediately before the given one."""
    after_path = REPO_ROOT / analysis_dir
    parts = after_path.name.split("_", 1)
    if len(parts) < 2:
        return None
    step_name = parts[1]
    after_index = int(parts[0])
    if after_index == 0:
        return None
    candidate = after_path.parent / f"{after_index - 1}_{step_name}"
    if candidate.is_dir() and (candidate / "meta.json").is_file():
        return str(candidate.relative_to(REPO_ROOT))
    return None


def build_pr_impact_sections(meta_obj: dict, analysis_dir: str) -> tuple[str, str]:
    """Build the PR impact prompt sections.

    Returns (pr_impact_section, pr_impact_requirement) — both empty strings
    if there is no PR info or no previous analysis to compare against.
    """
    if "pr_url" not in meta_obj:
        return ("", "")

    before_dir = find_before_dir(analysis_dir)
    if not before_dir:
        return ("", "")

    before_meta_path = REPO_ROOT / before_dir / "meta.json"
    before_meta = json.loads(before_meta_path.read_text())
    before_runs = before_meta.get("history", [])

    if not before_runs:
        return ("", "")

    pr_title = meta_obj.get("pr_title", "unknown")
    pr_desc = meta_obj.get("pr_description", "")
    before_run_list = ", ".join(f"`history/{r}/`" for r in before_runs)

    section = f"""
## PR Under Evaluation

This analysis evaluates the impact of a PR:
- **PR**: {meta_obj["pr_url"]}
- **Title**: {pr_title}
- **Description**: {pr_desc}

### Previous Analysis Runs (before the PR)

The previous analysis (`{before_dir}/`) examined these history runs:
{before_run_list}

Read the actual output files from both the previous runs (listed above) and the
current runs (listed in meta.json `history`) to compare before vs after.

"""

    requirement = """- **PR Impact (REQUIRED)**: Include a `## PR Impact` section as described in
  AGENTS.md. Compare the current runs against the previous-analysis runs listed
  above. Determine if the PR produced a significant improvement, was neutral,
  or made things worse. End with a verdict: KEEP, REVERT, or CONDITIONAL.
"""

    return (section, requirement)


def build_prompt(agent_name: str, analysis_dir: str, meta_json: str,
                 pr_impact_section: str, pr_impact_requirement: str) -> str:
    output_file = f"{analysis_dir}/insight_{agent_name}.md"
    return PROMPT_TEMPLATE.format(
        agent_name=agent_name,
        output_file=output_file,
        repo_root=REPO_ROOT,
        analysis_dir=analysis_dir,
        meta_json=meta_json,
        pr_impact_section=pr_impact_section,
        pr_impact_requirement=pr_impact_requirement,
    )



def main():
    parser = argparse.ArgumentParser(
        description="Run analysis agents (Claude Code + Codex) in parallel.",
    )
    parser.add_argument(
        "analysis_dir",
        help="Relative path to the analysis step directory (e.g. analysis/0_identify_potential_levers)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Per-agent timeout in seconds (default: {DEFAULT_TIMEOUT})",
    )
    args = parser.parse_args()

    analysis_dir: str = args.analysis_dir
    meta_path = REPO_ROOT / analysis_dir / "meta.json"
    if not meta_path.is_file():
        sys.exit(f"ERROR: No meta.json found at {meta_path}")

    meta_json = meta_path.read_text()
    meta_obj = json.loads(meta_json)

    pr_impact_section, pr_impact_requirement = build_pr_impact_sections(meta_obj, analysis_dir)

    claude_prompt = build_prompt("claude", analysis_dir, meta_json, pr_impact_section, pr_impact_requirement)
    codex_prompt = build_prompt("codex", analysis_dir, meta_json, pr_impact_section, pr_impact_requirement)

    print(f"Starting analysis for: {analysis_dir}")
    if "pr_url" in meta_obj:
        print(f"  PR: {meta_obj.get('pr_title', 'unknown')}")
        before_dir = find_before_dir(analysis_dir)
        if before_dir:
            print(f"  Comparing against: {before_dir}")
        else:
            print(f"  No previous analysis found — PR impact section will be skipped")
    print(f"  Claude insight → {analysis_dir}/insight_claude.md")
    print(f"  Codex  insight → {analysis_dir}/insight_codex.md")
    print()

    # Check which output files already exist (resume support).
    analysis_path = REPO_ROOT / analysis_dir
    events_path = analysis_path / "events.jsonl"
    claude_output = analysis_path / "insight_claude.md"
    codex_output = analysis_path / "insight_codex.md"

    run_claude = not claude_output.is_file()
    run_codex = not codex_output.is_file()

    if not run_claude and not run_codex:
        print("Both insight files already exist — nothing to do.")
        emit_event(events_path, "insight_claude_complete",
                   status="ok", skipped="already_exists")
        emit_event(events_path, "insight_codex_complete",
                   status="ok", skipped="already_exists")
        return

    if not run_claude:
        print(f"  Skipping Claude — {claude_output.relative_to(REPO_ROOT)} already exists")
        emit_event(events_path, "insight_claude_complete",
                   status="ok", skipped="already_exists")
    if not run_codex:
        print(f"  Skipping Codex — {codex_output.relative_to(REPO_ROOT)} already exists")
        emit_event(events_path, "insight_codex_complete",
                   status="ok", skipped="already_exists")

    # Launch agents that still need to run.
    claude_proc = None
    codex_proc = None

    if run_claude:
        claude_t0 = time.monotonic()
        claude_proc = subprocess.Popen(
            [
                "claude",
                "-p", claude_prompt,
                "--allowedTools", "Read,Glob,Grep,Write",
                "--add-dir", str(REPO_ROOT),
                "--model", "sonnet",
            ],
            cwd=REPO_ROOT,
            start_new_session=True,
        )
        emit_event(events_path, "insight_claude_start", pid=claude_proc.pid)

    if run_codex:
        codex_t0 = time.monotonic()
        codex_proc = subprocess.Popen(
            [
                "codex",
                "exec", codex_prompt,
                "-C", str(REPO_ROOT),
                "--full-auto",
            ],
            cwd=REPO_ROOT,
            start_new_session=True,
        )
        emit_event(events_path, "insight_codex_start", pid=codex_proc.pid)

    timeout = args.timeout
    pids = []
    if claude_proc:
        pids.append(f"claude={claude_proc.pid}")
    if codex_proc:
        pids.append(f"codex={codex_proc.pid}")
    print(f"PIDs: {' '.join(pids)}")
    print(f"Waiting for agents to finish (timeout: {timeout}s)...")
    print()

    claude_ok = not run_claude  # True if skipped (already exists)
    codex_ok = not run_codex
    claude_timed_out = False
    codex_timed_out = False

    if claude_proc:
        remaining = max(0, timeout - (time.monotonic() - claude_t0))
        try:
            claude_exit = claude_proc.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            os.killpg(os.getpgid(claude_proc.pid), signal.SIGKILL)
            claude_proc.wait()
            claude_timed_out = True
            claude_exit = None

        claude_duration = round(time.monotonic() - claude_t0, 2)
        if claude_timed_out:
            emit_event(events_path, "insight_claude_error",
                       error=f"timed out after {timeout}s",
                       duration_seconds=claude_duration)
            claude_output.write_text(
                "# ERROR: claude timed out\n\n"
                f"Claude Code exceeded the {timeout}s time limit.\n"
                "See events.jsonl for details.\n"
            )
        elif claude_exit == 0:
            emit_event(events_path, "insight_claude_complete",
                       status="ok", duration_seconds=claude_duration)
            claude_ok = True
        else:
            emit_event(events_path, "insight_claude_error",
                       error=f"exit code {claude_exit}",
                       duration_seconds=claude_duration)

    if codex_proc:
        remaining = max(0, timeout - (time.monotonic() - codex_t0))
        try:
            codex_exit = codex_proc.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            os.killpg(os.getpgid(codex_proc.pid), signal.SIGKILL)
            codex_proc.wait()
            codex_timed_out = True
            codex_exit = None

        codex_duration = round(time.monotonic() - codex_t0, 2)
        if codex_timed_out:
            emit_event(events_path, "insight_codex_error",
                       error=f"timed out after {timeout}s",
                       duration_seconds=codex_duration)
            codex_output.write_text(
                "# ERROR: codex timed out\n\n"
                f"Codex exceeded the {timeout}s time limit.\n"
                "See events.jsonl for details.\n"
            )
        elif codex_exit == 0:
            emit_event(events_path, "insight_codex_complete",
                       status="ok", duration_seconds=codex_duration)
            codex_ok = True
        else:
            emit_event(events_path, "insight_codex_error",
                       error=f"exit code {codex_exit}",
                       duration_seconds=codex_duration)

    # Report results.
    print()
    print("═" * 50)
    print("Results")
    print("═" * 50)

    if not run_claude:
        print(f"  Claude Code skipped (already exists)")
    elif claude_timed_out:
        print(f"  Claude Code timed out after {timeout}s (killed)")
    elif claude_ok:
        print(f"  Claude Code finished successfully")
    else:
        print(f"  Claude Code exited with code {claude_exit}")

    if not run_codex:
        print(f"  Codex skipped (already exists)")
    elif codex_timed_out:
        print(f"  Codex timed out after {timeout}s (killed)")
    elif codex_ok:
        print(f"  Codex finished successfully")
    else:
        print(f"  Codex exited with code {codex_exit}")

    print()
    print("Insight files:")
    insight_dir = REPO_ROOT / analysis_dir
    insight_files = sorted(insight_dir.glob("insight_*.md"))
    if insight_files:
        for f in insight_files:
            size = f.stat().st_size
            print(f"  {f.relative_to(REPO_ROOT)}  ({size} bytes)")
    else:
        print("  (no insight files found)")

    # If both agents failed (timeout or error), exit non-zero.
    if not claude_ok and not codex_ok:
        sys.exit("ERROR: both agents failed")


if __name__ == "__main__":
    main()
