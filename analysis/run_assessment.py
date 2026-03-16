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
import sys
from pathlib import Path
import subprocess


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

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

Do not write any other files.
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


def main():
    parser = argparse.ArgumentParser(
        description="Assess whether a PR improved output quality by comparing before/after analyses.",
    )
    parser.add_argument(
        "after_dir",
        help="Relative path to the post-change analysis directory (e.g. analysis/1_identify_potential_levers)",
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
        print("  Run: python analysis/update_meta_pr.py " + after_dir + " <PR_NUMBER>")
        print()

    output_file = f"{after_dir}/assessment.md"

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

    result = subprocess.run(
        [
            "claude",
            "-p", prompt,
            "--allowedTools", "Read,Glob,Grep,Write",
            "--add-dir", str(REPO_ROOT),
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
    output_path = REPO_ROOT / output_file
    if output_path.is_file():
        size = output_path.stat().st_size
        print(f"  {output_file}  ({size} bytes)")
    else:
        print("  (assessment.md not found)")


if __name__ == "__main__":
    main()
