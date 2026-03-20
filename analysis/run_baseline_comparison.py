#!/usr/bin/env python3
"""
Compare experiment outputs against baseline training data to determine whether
the current prompt/code produces better or worse results.

Unlike run_assessment.py (which compares two analysis directories before/after
a PR), this script compares raw model outputs against the gold-standard baseline.
Useful for first-run scenarios where no prior analysis exists.

Usage:
    python analysis/run_baseline_comparison.py analysis/30_identify_documents
    python analysis/run_baseline_comparison.py analysis/30_identify_documents --timeout 900
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

# Step-specific configuration: which output files to compare.
# Each entry maps step_name -> list of (filename, description) tuples.
STEP_OUTPUT_FILES = {
    "identify_potential_levers": [
        ("002-10-potential_levers.json", "cleaned levers"),
    ],
    "identify_documents": [
        ("017-5-identified_documents_to_find.json", "documents to find"),
        ("017-6-identified_documents_to_create.json", "documents to create"),
    ],
}

OUTPUT_FILENAME = "baseline_comparison.md"


PROMPT_TEMPLATE = """\
You are a baseline comparison agent. Your job is to compare experiment outputs
from multiple models against the gold-standard baseline training data and
determine whether the outputs are better, worse, or comparable.

## Context

Analysis directory: `{analysis_dir}/`
Baseline directory: `baseline/train/`
Step: `{step_name}`

### meta.json

```json
{meta}
```

### Output files to compare

For each plan, compare these files between baseline and experiment outputs:
{output_files_description}

### History runs

{history_description}

## Task

1. Read `{analysis_dir}/meta.json` to identify all history runs.

2. For each history run, read the `meta.json` to identify the model name.

3. Read ALL baseline output files from `baseline/train/<plan>/` for the files
   listed above. These represent the gold standard produced by a strong model
   on the full pipeline.

4. For EVERY model, read the output files from
   `history/<run>/outputs/<plan>/` for ALL plans where the model succeeded.
   Check `history/<run>/outputs.jsonl` for success/failure status.

5. Compute quantitative metrics and produce a structured comparison:

### A. Success Rate

For each model, report:
- Plans succeeded / total (from outputs.jsonl)
- Failure reasons (from outputs.jsonl error field or events.jsonl)
- Present as a table sorted by success rate descending.

### B. Quantitative Comparison

Read the actual JSON output files and compute these metrics per model,
averaged across all successful plans. Compare against the same metrics
computed from baseline files.

For `identify_documents`:
- **Document count**: number of items in each list (to_find, to_create, total)
- **Description length**: average character count of `description` fields
- **Name uniqueness**: count of duplicate `document_name` values
- **Field completeness**: percentage of optional fields that are non-null
  (e.g., `document_template_primary`, `document_template_secondary`,
  `search_keywords`, `document_url`)
- **Steps/keywords count**: average number of items in nested lists
  (`steps_to_find`, `steps_to_create`, `search_keywords`)

For `identify_potential_levers`:
- **Lever count**: total levers per plan
- **Option count**: levers with exactly 3 options vs violations
- **Description length**: average character count of key fields
  (consequences, options, review)
- **Name uniqueness**: unique lever names / total
- **Template leakage**: verbatim copying of prompt example text

Present as a table: Metric | Baseline | Model1 | Model2 | ... | Verdict

### C. Quality Assessment

For each model, assess:
- **Completeness**: Does it cover the same document types/categories as baseline?
- **Specificity**: Are descriptions project-specific or generic boilerplate?
- **Verbosity**: Are descriptions appropriately detailed (not too terse, not bloated)?
  Use baseline as the reference point for appropriate length.

### D. Model Ranking

Rank all models from best to worst based on the combined metrics.
Identify which model(s) most closely match baseline quality.

### E. Overall Verdict

Rate the experiment batch overall: **BETTER**, **COMPARABLE**, **MIXED**, or **WORSE**
than baseline. Justify with specific numbers.

If MIXED, explain which models are comparable/better and which are worse.

### F. Recommendations

Based on the comparison, what changes would bring the outputs closer to
baseline quality? Be specific — cite which metrics need improvement and
for which models.

## Output

Write your comparison to: `{output_file}`

Use this structure:

```
# Baseline Comparison: [step name]

## Success Rate
| Model | Success | Failures |
...

## Quantitative Comparison
| Metric | Baseline | Model1 | Model2 | ... |
...

## Quality Assessment
...

## Model Ranking
1. ...

## Overall Verdict
**[BETTER / COMPARABLE / MIXED / WORSE]**: ...

## Recommendations
...
```

Do not write any other files. Do not modify meta.json or events.jsonl.
"""


def _detect_step_name(analysis_dir: str) -> str:
    """Extract step name from analysis directory name (e.g. '30_identify_documents')."""
    path = REPO_ROOT / analysis_dir
    parts = path.name.split("_", 1)
    if len(parts) != 2:
        sys.exit(f"ERROR: Cannot parse step name from directory: {path.name}")
    return parts[1]


def _build_output_files_description(step_name: str) -> str:
    """Build a human-readable description of which files to compare."""
    files = STEP_OUTPUT_FILES.get(step_name)
    if not files:
        return f"(No output files configured for step '{step_name}' — read all JSON files in the output directories)"
    lines = []
    for filename, desc in files:
        lines.append(f"- `{filename}` ({desc})")
    return "\n".join(lines)


def _build_history_description(meta: dict) -> str:
    """Build a description of history runs from meta.json."""
    history = meta.get("history", [])
    if not history:
        return "(no history runs)"
    lines = []
    for run in history:
        lines.append(f"- `history/{run}/`")
    return "\n".join(lines)


def _stderr_tail(proc: subprocess.Popen, max_chars: int = 500) -> str:
    """Read the tail of a process's stderr (must use stderr=PIPE)."""
    if proc.stderr is None:
        return ""
    raw = proc.stderr.read()
    text = raw.decode("utf-8", errors="replace").strip()
    return text[-max_chars:] if text else ""


def main():
    parser = argparse.ArgumentParser(
        description="Compare experiment outputs against baseline training data.",
    )
    parser.add_argument(
        "analysis_dir",
        help="Relative path to the analysis directory (e.g. analysis/30_identify_documents)",
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

    meta_path = analysis_path / "meta.json"
    if not meta_path.is_file():
        sys.exit(f"ERROR: No meta.json found in {analysis_path}")

    meta = json.loads(meta_path.read_text())
    step_name = _detect_step_name(analysis_dir)

    # Check baseline exists.
    baseline_dir = REPO_ROOT / "baseline" / "train"
    if not baseline_dir.is_dir():
        sys.exit(f"ERROR: Baseline directory not found: {baseline_dir}")

    output_file = f"{analysis_dir}/{OUTPUT_FILENAME}"
    output_path = REPO_ROOT / output_file
    events_path = analysis_path / "events.jsonl"

    if output_path.is_file():
        size = output_path.stat().st_size
        print(f"{OUTPUT_FILENAME} already exists ({size} bytes) — nothing to do.")
        emit_event(events_path, "baseline_comparison_complete",
                   status="ok", skipped="already_exists")
        return

    output_files_desc = _build_output_files_description(step_name)
    history_desc = _build_history_description(meta)

    prompt = PROMPT_TEMPLATE.format(
        analysis_dir=analysis_dir,
        step_name=step_name,
        meta=json.dumps(meta, indent=2),
        output_files_description=output_files_desc,
        history_description=history_desc,
        output_file=output_file,
    )

    pr_title = meta.get("pr_title", "(no PR)")
    print(f"Baseline comparison:")
    print(f"  Analysis: {analysis_dir}")
    print(f"  Step:     {step_name}")
    print(f"  Baseline: baseline/train/")
    if "commit" in meta:
        print(f"  Commit:   {meta['commit']} ({meta.get('branch', '?')})")
    else:
        print(f"  PR:       {pr_title}")
    print(f"  Runs:     {len(meta.get('history', []))} history runs")
    print(f"  Output:   {output_file}")
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
    emit_event(events_path, "baseline_comparison_start", pid=proc.pid)

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
        emit_event(events_path, "baseline_comparison_error",
                   error=f"timed out after {timeout}s",
                   duration_seconds=duration,
                   **({"stderr_tail": stderr_text} if stderr_text else {}))
        output_path.write_text(
            "# ERROR: claude timed out\n\n"
            f"Claude Code exceeded the {timeout}s time limit.\n"
            "See events.jsonl for details.\n"
        )
    elif exit_code == 0:
        emit_event(events_path, "baseline_comparison_complete",
                   status="ok", duration_seconds=duration)
    else:
        emit_event(events_path, "baseline_comparison_error",
                   error=f"exit code {exit_code}", duration_seconds=duration,
                   **({"stderr_tail": stderr_text} if stderr_text else {}))

    print()
    print("=" * 50)
    print("Results")
    print("=" * 50)

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
        print(f"  ({OUTPUT_FILENAME} not found)")

    if timed_out or (exit_code is not None and exit_code != 0):
        sys.exit(1)


if __name__ == "__main__":
    main()
