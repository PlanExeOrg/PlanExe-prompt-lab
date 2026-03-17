#!/usr/bin/env python3
"""
Assess whether a PR improved or worsened output quality by comparing two
consecutive analysis directories (before and after the change).

Usage:
    python analysis/run_assessment.py analysis/1_identify_potential_levers
    python analysis/run_assessment.py analysis/1_identify_potential_levers --before analysis/0_identify_potential_levers
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
You are an assessment agent. Your job is to compare two analysis rounds — one
before a code/prompt change and one after — and determine whether the change
helped, hurt, or was neutral.

## Context

The "before" analysis directory is: `{before_dir}/`
The "after" analysis directory is:  `{after_dir}/`

### Before meta.json

```json
{before_meta}
```

### After meta.json

```json
{after_meta}
```

## Task

1. Read ALL files from both analysis directories:
   - `meta.json` — provenance (prompt, history runs, PR info)
   - `insight_*.md` — quality analyses from different agents
   - `code_*.md` — code reviews from different agents
   - `synthesis.md` — cross-agent synthesis with ranked directions

2. Read the baseline training data in `baseline/train/` for reference.

3. For models that appear in BOTH the before and after batches, read a sample
   of their actual output files from `history/` to verify claims made in the
   insight files. At minimum, read the merged lever files (`002-10-*.json`)
   for at least 2 shared models, 1 plan each.

4. Produce a structured assessment covering:

### A. Issue Resolution
- What issue was the PR supposed to fix? (from after meta.json `pr_title`/`pr_description`)
- Is the issue actually resolved in the post-fix outputs? Cite evidence.
- Are there any residual symptoms of the original issue?

### B. Quality Comparison (Before vs After)
For each metric below, compare before and after, citing specific numbers from
the insight files. Flag whether each metric IMPROVED, REGRESSED, or is UNCHANGED.

Metrics to compare:
- **Success rate**: plans succeeded / total per model (a success rate increase
  after removing a Pydantic hard constraint means the constraint was causing
  unnecessary validation failures — check events.jsonl for LLMChatError count)
- **Bracket placeholder leakage**: count of unfilled `[...]` patterns
- **Option count violations**: levers with != 3 options
- **Lever name uniqueness**: unique names / total levers
- **Template leakage**: verbatim copying of prompt examples
- **Review format compliance**: `Controls X vs Y` pattern adherence
- **Consequence chain format**: `Immediate → Systemic → Strategic` markers
- **Content depth**: average option length in characters
- **Cross-call duplication**: lever names repeated across the 3 LLM calls
- **Over-generation count**: how many models produced >7 levers per call now
  that the hard cap is removed? This is informational, not a failure — the
  downstream DeduplicateLeversTask handles the extras
- **Field length vs baseline**: average consequences/options/review length
  compared to baseline training data. Report the ratio. A ratio above 2× is a
  warning; above 3× likely indicates verbosity regression.
- **Fabricated quantification**: count of percentage claims or numeric estimates
  in lever fields that have no basis in the project context (e.g. "reduces
  costs by 30%"). These are almost always LLM-fabricated.
- **Marketing-copy language**: count of hype phrases ("cutting-edge",
  "game-changing", "revolutionary", "breathless") in strategic analysis fields.
  These degrade credibility even if structural compliance is perfect.

**IMPORTANT**: A change that improves success rate (e.g. 88% → 97%) but
degrades content quality across all successful plans is a net negative.
Content quality regressions that affect every plan are higher priority than
structural fixes that recover one failed plan.

**OPTIMIZE_INSTRUCTIONS**: Read the `OPTIMIZE_INSTRUCTIONS` constant near the
top of `identify_potential_levers.py` (in the PlanExe repo). When evaluating
the PR, check whether the change moves closer to or further from its goals
(realistic, feasible, actionable plans). Flag any new violations of its
known-problems list. If the PR or the recommended next change would benefit
from updating OPTIMIZE_INSTRUCTIONS (e.g., adding a newly discovered pitfall),
note that in the Recommended Next Change or Backlog section.

Present this as a comparison table with columns: Metric | Before | After | Verdict.

Only compare models that appear in BOTH batches. If a model only appears in
one batch, note it separately but do not use it for the comparison.

### C. New Issues
- Did the change introduce any NEW problems not present before?
- Did it surface latent issues that were previously hidden?

### D. Verdict
- **Is the PR a keeper?** Answer YES, NO, or CONDITIONAL (with conditions).
- Justify the verdict based on the evidence above.
- If CONDITIONAL, specify what additional changes would be needed.

### E. Recommended Next Change

Read the `synthesis.md` from the "after" analysis directory. It contains a
`## Recommendation` section proposing the next code or prompt change.

Evaluate the recommended solution:
- **What does it propose?** Summarize the recommended change in 1-2 sentences.
- **Is the evidence convincing?** Does the synthesis cite specific runs, metrics,
  and failure modes that the recommendation would fix?
- **What should be verified?** List concrete things to check in the next
  iteration's experiments to confirm the recommendation actually works.
  Be specific — name the models, plans, metrics, or failure classes to watch.
  Example: "Verify haiku no longer hard-fails on gta_game (was 0/1 in run 87
  due to 8 levers exceeding max_length=7)."
- **What could go wrong?** Identify risks or edge cases the recommendation
  might introduce. What regressions should the next iteration watch for?
- **Are there prerequisite issues?** Does the recommendation depend on other
  fixes being in place first?

### F. Backlog
- Any issues from "before" that are now resolved and can be removed from
  the backlog?
- Any new issues that should be added to the backlog?

## Output

Write your assessment to: `{output_file}`

Use this structure:

```
# Assessment: [PR title]

## Issue Resolution
...

## Quality Comparison
| Metric | Before | After | Verdict |
|--------|--------|-------|---------|
...

## New Issues
...

## Verdict
**[YES / NO / CONDITIONAL]**: [one-sentence justification]

## Recommended Next Change
**Proposal**: ...
**Evidence**: ...
**Verify**: ...
**Risks**: ...

## Backlog
...
```

Do not write any other files. Do not modify meta.json or events.jsonl.
"""


def find_before_dir(after_dir: str) -> str | None:
    """Find the analysis directory immediately before the given one."""
    after_path = REPO_ROOT / after_dir
    step_name = after_path.name.split("_", 1)[1]
    after_index = int(after_path.name.split("_", 1)[0])

    if after_index == 0:
        return None

    candidate = after_path.parent / f"{after_index - 1}_{step_name}"
    if candidate.is_dir():
        return str(candidate.relative_to(REPO_ROOT))
    return None


def _stderr_tail(proc: subprocess.Popen, max_chars: int = 500) -> str:
    """Read the tail of a process's stderr (must use stderr=PIPE)."""
    if proc.stderr is None:
        return ""
    raw = proc.stderr.read()
    text = raw.decode("utf-8", errors="replace").strip()
    return text[-max_chars:] if text else ""


def main():
    parser = argparse.ArgumentParser(
        description="Assess whether a PR improved output quality by comparing before/after analyses.",
    )
    parser.add_argument(
        "after_dir",
        help="Relative path to the post-change analysis directory (e.g. analysis/1_identify_potential_levers)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Timeout in seconds (default: {DEFAULT_TIMEOUT})",
    )
    parser.add_argument(
        "--before",
        dest="before_dir",
        default=None,
        help="Relative path to the pre-change analysis directory. Default: auto-detect (index - 1).",
    )
    args = parser.parse_args()

    after_dir: str = args.after_dir
    after_path = REPO_ROOT / after_dir
    if not after_path.is_dir():
        sys.exit(f"ERROR: Directory not found: {after_path}")

    # Determine the before directory.
    before_dir = args.before_dir or find_before_dir(after_dir)
    if not before_dir:
        sys.exit(
            "ERROR: Could not find a before directory. "
            "Use --before to specify it explicitly."
        )
    before_path = REPO_ROOT / before_dir
    if not before_path.is_dir():
        sys.exit(f"ERROR: Before directory not found: {before_path}")

    # Check that both have synthesis.md (all phases must have run).
    for d, label in [(before_path, "before"), (after_path, "after")]:
        if not (d / "synthesis.md").is_file():
            sys.exit(f"ERROR: {label} directory missing synthesis.md: {d}")

    # Read meta.json from both.
    before_meta = (before_path / "meta.json").read_text()
    after_meta = (after_path / "meta.json").read_text()

    # Check that after has PR info.
    after_meta_obj = json.loads(after_meta)
    if "pr_url" not in after_meta_obj:
        print("WARNING: after meta.json has no pr_url — assessment may lack PR context.")
        step_name = after_path.name.split("_", 1)[1] if "_" in after_path.name else "STEP"
        print("  Run: python analysis/prepare_iteration.py " + step_name + " <PR_NUMBER>")
        print()

    output_file = f"{after_dir}/assessment.md"
    output_path = REPO_ROOT / output_file
    events_path = after_path / "events.jsonl"

    if output_path.is_file():
        size = output_path.stat().st_size
        print(f"assessment.md already exists ({size} bytes) — nothing to do.")
        emit_event(events_path, "assessment_claude_complete",
                   status="ok", skipped="already_exists")
        return

    prompt = PROMPT_TEMPLATE.format(
        before_dir=before_dir,
        after_dir=after_dir,
        before_meta=before_meta,
        after_meta=after_meta,
        output_file=output_file,
    )

    print(f"Comparing:")
    print(f"  Before: {before_dir}")
    print(f"  After:  {after_dir}")
    if "pr_title" in after_meta_obj:
        print(f"  PR:     {after_meta_obj['pr_title']}")
    print(f"  Output: {output_file}")
    print()

    timeout = args.timeout
    t0 = time.monotonic()
    proc = subprocess.Popen(
        [
            "claude",
            "-p", prompt,
            "--allowedTools", "Read,Glob,Grep,Write",
            "--add-dir", str(REPO_ROOT),
            "--model", "sonnet",
        ],
        cwd=REPO_ROOT,
        start_new_session=True,
        stderr=subprocess.PIPE,
    )
    emit_event(events_path, "assessment_claude_start", pid=proc.pid)

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
        emit_event(events_path, "assessment_claude_error",
                   error=f"timed out after {timeout}s",
                   duration_seconds=duration,
                   **({"stderr_tail": stderr_text} if stderr_text else {}))
        output_path.write_text(
            "# ERROR: claude timed out\n\n"
            f"Claude Code exceeded the {timeout}s time limit.\n"
            "See events.jsonl for details.\n"
        )
    elif exit_code == 0:
        emit_event(events_path, "assessment_claude_complete",
                   status="ok", duration_seconds=duration)
    else:
        emit_event(events_path, "assessment_claude_error",
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
    if output_path.is_file():
        size = output_path.stat().st_size
        print(f"  {output_file}  ({size} bytes)")
    else:
        print("  (assessment.md not found)")

    if timed_out or (exit_code is not None and exit_code != 0):
        sys.exit(1)


if __name__ == "__main__":
    main()
