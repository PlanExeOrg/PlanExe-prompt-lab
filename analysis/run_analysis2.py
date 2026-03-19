#!/usr/bin/env python3
"""
Single-phase analysis pipeline with pre-computed metrics.

Pre-computes all quantitative metrics (field lengths, lever counts, option
compliance, template leakage, success rates, name uniqueness) and embeds them
directly in the Claude prompt.  Claude then focuses on qualitative analysis,
pattern detection, and recommendations — without having to read and measure
every JSON file manually.

Usage:
    python analysis/run_analysis2.py analysis/35_identify_potential_levers
    python analysis/run_analysis2.py analysis/35_identify_potential_levers --timeout 900
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
from precompute_metrics import compute_metrics, format_metrics_text


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

DEFAULT_TIMEOUT = 900  # 15 minutes
DEFAULT_MAX_RETRIES = 3

OUTPUT_FILENAME = "baseline_comparison.md"


# ---------------------------------------------------------------------------
# Step detection
# ---------------------------------------------------------------------------

def _detect_step_name(analysis_dir: str) -> str:
    path = REPO_ROOT / analysis_dir
    parts = path.name.split("_", 1)
    if len(parts) != 2:
        sys.exit(f"ERROR: Cannot parse step name from directory: {path.name}")
    return parts[1]


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

PROMPT_TEMPLATE = """\
You are an analysis agent. Your job is to compare experiment outputs from
multiple models against the gold-standard baseline training data, assess
quality, and produce a comprehensive analysis report.

## Context

Analysis directory: `{analysis_dir}/`
Baseline directory: `baseline/train/`
Step: `{step_name}`

### meta.json

```json
{meta}
```

## Pre-computed Metrics

The following metrics have been pre-computed from all baseline and experiment
output files.  Use these numbers directly — do NOT re-read or re-count the
JSON files to verify these metrics.  They are authoritative.

```json
{metrics}
```

### How to read the metrics

- `baseline`: metrics per plan from `baseline/train/`
- `runs`: keyed by history run path, each containing:
  - `model`: the model name
  - `success`: plans succeeded/failed/partial from `outputs.jsonl`
  - `plans`: per-plan metrics identical in structure to baseline
- Per-plan lever metrics include:
  - `lever_count`, `name_uniqueness`, `unique_names`
  - `option_violations` (levers with != 3 options)
  - `template_leakage` / `template_leakage_pct` (reviews matching "the options [verb]" pattern)
  - `consequences_chars`, `review_chars`, `option_chars` (min/max/avg)
- Per-plan document metrics include:
  - `document_count`, `name_uniqueness`, `description_chars`
  - `steps_per_doc`, `keywords_per_doc`, `field_completeness_pct`

## Task

Using the pre-computed metrics above, produce a structured analysis covering:

### A. Success Rate

For each model, report plans succeeded / total.  Note any partial successes
(where calls_succeeded < 3).  Present as a table.

### B. Quantitative Comparison

Aggregate the per-plan metrics into per-model averages.  Compare against
baseline.  Present as tables.

For `identify_potential_levers`, include these tables:
- **Lever count per plan** (table: Plan | Baseline | Model1 | Model2 | ...)
- **Option count compliance** (total levers, violations, compliance %)
- **Average consequences field length** (chars, per plan averaged across levers)
- **Average review field length** (chars, per plan averaged across levers)
- **Name uniqueness** (unique names / total per plan)
- **Template leakage** ("the options" as grammatical subject in review field)
  Present as: Model | Total Levers | Leaky Reviews | Leakage Rate

For `identify_documents`, include:
- **Document count** (to_find, to_create, total)
- **Description length** (average chars)
- **Field completeness** (% of optional fields filled)
- **Steps/keywords count**

### C. Quality Assessment

For each model, read a SAMPLE of actual output files to assess qualitative
aspects that metrics alone cannot capture:
- **Specificity**: Are descriptions project-specific or generic boilerplate?
- **Verbosity**: Appropriately detailed vs bloated?  Use baseline as reference.
  A ratio above 2x baseline length is a warning sign.
- **Content patterns**: Any recurring structural stereotypes?  (e.g., "Core
  tension:" prefix, formulaic triads, marketing-copy language)
- **Fabricated quantification**: Percentage claims with no basis in context.

Read at most 2-3 output files per model for this — the metrics already cover
the quantitative picture.  Focus your file reading on the qualitative aspects.

### D. Model Ranking

Rank all models from best to worst based on combined metrics and quality.
Identify which model(s) most closely match baseline quality.

### E. Overall Verdict

Rate the experiment batch: **BETTER**, **COMPARABLE**, **MIXED**, or **WORSE**
than baseline.  Justify with specific numbers from the pre-computed metrics.

### F. Recommendations

What changes would bring outputs closer to baseline quality?  Be specific —
cite which metrics need improvement and for which models.

## Output

Write your analysis to: `{output_file}`

Use this structure:

```
# Baseline Comparison: [step name]

**PR**: [pr_url] — [pr_title]
**Analysis dir**: `{analysis_dir}/`
**Baseline**: `baseline/train/` (5 plans, claude-sonnet-3.5, iteration baseline)

## Success Rate
| Run | Model | Plans | Successes | Failures |
...

## Quantitative Comparison
[tables as specified above]

## Quality Assessment
### [model name]
...

## Model Ranking
1. ...

## Overall Verdict
**[BETTER / COMPARABLE / MIXED / WORSE]**: ...

## Recommendations
...
```

Do not write any other files.  Do not modify meta.json or events.jsonl.
"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _stderr_tail(proc: subprocess.Popen, max_chars: int = 500) -> str:
    if proc.stderr is None:
        return ""
    raw = proc.stderr.read()
    text = raw.decode("utf-8", errors="replace").strip()
    return text[-max_chars:] if text else ""


def _is_error_marker(path: Path) -> bool:
    if not path.is_file():
        return False
    try:
        with open(path, "r", encoding="utf-8") as f:
            head = f.read(50)
        return head.startswith("# ERROR:")
    except Exception:
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Single-phase analysis with pre-computed metrics.",
    )
    parser.add_argument(
        "analysis_dir",
        help="Relative path to the analysis directory (e.g. analysis/35_identify_potential_levers)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Timeout in seconds (default: {DEFAULT_TIMEOUT})",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=DEFAULT_MAX_RETRIES,
        help=f"Max attempts before giving up (default: {DEFAULT_MAX_RETRIES})",
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

    output_file = f"{analysis_dir}/{OUTPUT_FILENAME}"
    output_path = REPO_ROOT / output_file
    events_path = analysis_path / "events.jsonl"

    if output_path.is_file() and not _is_error_marker(output_path):
        size = output_path.stat().st_size
        print(f"{OUTPUT_FILENAME} already exists ({size} bytes) — nothing to do.")
        emit_event(events_path, "analysis2_complete",
                   status="ok", skipped="already_exists")
        return

    # ------------------------------------------------------------------
    # Phase 0: Pre-compute metrics (fast, pure Python)
    # ------------------------------------------------------------------
    print("Pre-computing metrics...")
    t0 = time.monotonic()

    history_runs = meta.get("history", [])
    metrics_report = compute_metrics(REPO_ROOT, step_name, history_runs)
    metrics_text = format_metrics_text(metrics_report)

    precompute_duration = round(time.monotonic() - t0, 2)
    metrics_size = len(metrics_text)
    print(f"  Metrics computed in {precompute_duration}s ({metrics_size} chars)")

    # Save metrics alongside the analysis for reference
    metrics_path = analysis_path / "precomputed_metrics.json"
    metrics_path.write_text(json.dumps(metrics_report, indent=2, ensure_ascii=False))
    print(f"  Saved to {metrics_path.name}")
    print()

    # ------------------------------------------------------------------
    # Phase 1: Claude analysis (single call)
    # ------------------------------------------------------------------
    prompt = PROMPT_TEMPLATE.format(
        analysis_dir=analysis_dir,
        step_name=step_name,
        meta=json.dumps(meta, indent=2),
        metrics=metrics_text,
        output_file=output_file,
    )

    pr_title = meta.get("pr_title", "(no PR)")
    print(f"Analysis (single phase):")
    print(f"  Analysis: {analysis_dir}")
    print(f"  Step:     {step_name}")
    print(f"  PR:       {pr_title}")
    print(f"  Runs:     {len(history_runs)} history runs")
    print(f"  Metrics:  {metrics_size} chars pre-computed")
    print(f"  Output:   {output_file}")
    print()

    timeout = args.timeout
    succeeded = False

    for attempt in range(1, args.max_retries + 1):
        # Clean error marker from prior attempt
        if _is_error_marker(output_path):
            output_path.unlink()
            print(f"  Removed error marker from prior attempt")

        if attempt > 1:
            print(f"  Retry {attempt}/{args.max_retries}")

        t1 = time.monotonic()
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
        emit_event(events_path, "analysis2_start", pid=proc.pid, attempt=attempt)

        timed_out = False
        try:
            exit_code = proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            proc.wait()
            timed_out = True
            exit_code = None

        duration = round(time.monotonic() - t1, 2)
        stderr_text = _stderr_tail(proc)

        if timed_out:
            emit_event(events_path, "analysis2_error",
                       error=f"timed out after {timeout}s",
                       duration_seconds=duration,
                       **({"stderr_tail": stderr_text} if stderr_text else {}))
            print(f"  Timed out after {timeout}s")
            if attempt < args.max_retries:
                # Write error marker so next attempt doesn't skip
                output_path.write_text(
                    "# ERROR: claude timed out\n\n"
                    f"Timed out after {timeout}s on attempt {attempt}.\n"
                )
                continue
        elif exit_code == 0:
            emit_event(events_path, "analysis2_complete",
                       status="ok", duration_seconds=duration)
            succeeded = True
            break
        else:
            emit_event(events_path, "analysis2_error",
                       error=f"exit code {exit_code}", duration_seconds=duration,
                       **({"stderr_tail": stderr_text} if stderr_text else {}))
            print(f"  Exited with code {exit_code}")
            if attempt < args.max_retries:
                if _is_error_marker(output_path):
                    output_path.unlink()
                continue

    print()
    print("=" * 50)
    print("Results")
    print("=" * 50)

    if succeeded:
        print("  Analysis completed successfully")
    else:
        print(f"  Analysis FAILED after {args.max_retries} attempts")

    total_duration = round(time.monotonic() - t0, 2)
    print(f"  Total time: {total_duration}s (precompute: {precompute_duration}s)")

    if output_path.is_file() and not _is_error_marker(output_path):
        size = output_path.stat().st_size
        print(f"  {output_file}  ({size} bytes)")
    else:
        print(f"  ({OUTPUT_FILENAME} not found or error)")

    if not succeeded:
        sys.exit(1)


if __name__ == "__main__":
    main()
