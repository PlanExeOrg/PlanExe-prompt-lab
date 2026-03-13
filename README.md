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

runs/                               # optimization run outputs
  <date>_<step_name>/
    meta.json                       # step, base prompt, model list
    candidates/                     # candidate prompt texts
    outputs/                        # LLM outputs per candidate per plan
    evaluations/                    # reasoning model comparisons
    summary.json                    # ranked candidates
    failed_attempts.log

scores/                             # longitudinal tracking
  scoreboard.csv                    # step, date, baseline_score, best_score, delta

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
