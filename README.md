# PlanExe Prompt Lab

Data repo for iteratively optimizing [PlanExe](https://github.com/PlanExeOrg/PlanExe) system prompts.

Stores baseline plan outputs, optimization run artifacts, evaluation scores, and full-plan comparison snapshots. The optimization engine itself lives in the PlanExe repo.

## Setup

```bash
git clone git@github.com:PlanExeOrg/PlanExe-prompt-lab.git
cd PlanExe-prompt-lab

# Populate baseline from a local directory of zip files
python populate_baseline.py /path/to/zips

# Or download from a URL
python populate_baseline.py https://github.com/PlanExeOrg/PlanExe-web/raw/refs/heads/main/
```

### populate_baseline.py options

```
--dry-run    Show what would be done without extracting
--force      Overwrite existing baseline directories
```

## Directory structure

```
dataset.json                        # train/verify split definition

baseline/                           # reference plan outputs (extracted from zips)
  train/
    20260310_hong_kong_game/
      001-2-plan.txt
      ...
      030-report.html
    ...
  verify/
    20260303_crate_recovery_campaign/
    ...

history/                            # captured output, global run counter
  # Path: history/{counter // 100}/{counter % 100:02d}_{step_name}/
  # Counter is auto-incremented: scan for highest run number + 1.
  0/                                # runs 0-99
  1/                                # runs 100-199
  2/                                # runs 200-299
    00_identify_purpose/            # run 200
    01_identify_potential_levers/
    02_identify_potential_levers/
      meta.json                     # step, system prompt SHA, model, system info
      events.jsonl                  # timestamped start/complete/error events
      outputs.jsonl                 # one row per completed plan
      outputs/
        <plan_name>/
          002-9-potential_levers_raw.json
          002-10-potential_levers.json
          activity_overview.json
          usage_metrics.jsonl
    ...

prompts/                            # registered system prompts by step
  identify_potential_levers/
    prompt_0_<sha256>.txt           # prompt_{index}_{sha256}.txt
    prompt_1_<sha256>.txt

analysis/                           # evaluation results by step
  0_identify_purpose/
  1_identify_potential_levers/
    summary.json                    # ranked candidates, aggregate scores
    failed_attempts.log

scores/                             # longitudinal tracking
  scoreboard.csv                    # step, date, baseline_score, best_score, delta
  history.json                      # full history for charting

full_plan_comparisons/              # periodic full-plan regenerations
```

## How it works

1. **Baseline** -- `populate_baseline.py` extracts PlanExe plan zips into `baseline/`. These are the reference outputs to beat.
2. **Optimize** -- The optimizer (in the PlanExe repo) generates candidate system prompts, runs them against train plans, and has a reasoning model score the outputs.
3. **Verify** -- Best candidates are scored against the verify set to prevent overfitting.
4. **Track** -- Scores are recorded in `scores/` for longitudinal comparison.

See [proposal 117](https://github.com/PlanExeOrg/PlanExe/blob/main/docs/proposals/117-system-prompt-optimizer.md) for the full design.

## License

[MIT](LICENSE)
