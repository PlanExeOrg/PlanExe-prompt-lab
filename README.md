# PlanExe Prompt Lab

Data repo for iteratively optimizing [PlanExe](https://github.com/PlanExeOrg/PlanExe) pipeline steps.

Stores baseline plan outputs, experiment run history, analysis artifacts, and registered prompts. The optimization engine (`self_improve/`) lives in the PlanExe repo.

## Supported Steps

| Step | Source file | What it produces |
|------|-----------|-----------------|
| `identify_potential_levers` | `identify_potential_levers.py` | Strategic levers with options, consequences, reviews |
| `identify_documents` | `identify_documents.py` | Documents to find and create for project planning |

## Quick Start

```bash
git clone git@github.com:PlanExeOrg/PlanExe-prompt-lab.git
cd PlanExe-prompt-lab

# Populate baseline from a local directory of zip files
python populate_baseline.py /path/to/zips

# Or download from a URL
python populate_baseline.py https://github.com/PlanExeOrg/PlanExe-web/raw/refs/heads/main/
```

### Running a full optimization iteration

```bash
# From PlanExe-prompt-lab directory:
python run_optimization_iteration.py --skip-implement --pr 342 --step identify_documents

# Or run just the analysis on existing data:
python analysis/run_analysis.py analysis/30_identify_documents
```

### populate_baseline.py options

```
--dry-run    Show what would be done without extracting
--force      Overwrite existing baseline directories
```

## Directory Structure

```
dataset.json                        # train/verify split definition
config.json                         # analysis config (e.g., codex enable/disable)

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

history/                            # experiment outputs, global run counter
  # Path: history/{counter // 100}/{counter % 100:02d}_{step_name}/
  # Counter is auto-incremented across ALL steps.
  0/                                # runs 0-99
  1/                                # runs 100-199
  2/                                # runs 200+
    17_identify_documents/          # run 217
      meta.json                     # step, model, system info
      events.jsonl                  # timestamped start/complete/error events
      outputs.jsonl                 # one row per completed plan
      outputs/
        <plan_name>/
          017-5-identified_documents_to_find.json
          017-6-identified_documents_to_create.json
          activity_overview.json
          usage_metrics.jsonl
    18_identify_documents/          # run 218 (different model)
    ...

prompts/                            # registered system prompts by step
  identify_potential_levers/
    prompt_0_<sha256>.txt           # prompt_{index}_{sha256}.txt
    prompt_1_<sha256>.txt
  identify_documents/
    prompt_0_<sha256>.txt

analysis/                           # per-iteration analysis artifacts
  # Index is globally unique across all steps.
  28_identify_potential_levers/
  29_identify_potential_levers/
    meta.json                       # PR info, history run list
    events.jsonl                    # analysis progress events
    insight_claude.md               # independent quality analysis
    code_claude.md                  # independent code review
    synthesis.md                    # cross-agent synthesis + recommendation
    assessment.md                   # before/after comparison verdict
  30_identify_documents/            # first identify_documents iteration
    meta.json
    insight_claude.md
    code_claude.md
    synthesis.md
    baseline_comparison.md          # vs baseline (no prior analysis to compare)

full_plan_comparisons/              # periodic full-plan regenerations
```

## How It Works

1. **Baseline** -- `populate_baseline.py` extracts PlanExe plan zips into `baseline/`. These are the gold-standard outputs to compare against.

2. **Run experiments** -- The runner (`self_improve/runner.py` in PlanExe) re-executes a pipeline step with the current code against baseline training data, using 7 models (1 local + 6 cloud). Outputs land in `history/`.

3. **Analyze** -- A 4-phase analysis pipeline examines the experiment outputs:
   - **Phase 1: Insight** -- Independent quality analysis of the outputs
   - **Phase 2: Code review** -- Source code review informed by the insight findings
   - **Phase 3: Synthesis** -- Cross-agent reconciliation with ranked recommendations
   - **Phase 4: Assessment or Baseline Comparison**:
     - **Assessment** (when prior analysis exists) -- Before/after comparison with YES/NO/CONDITIONAL verdict
     - **Baseline comparison** (first run of a step) -- Comparison against `baseline/train/` with BETTER/COMPARABLE/MIXED/WORSE verdict

4. **Iterate** -- Read the assessment/synthesis verdict, implement the recommended change, create a PR, and repeat.

See [analysis/AGENTS.md](analysis/AGENTS.md) for detailed analysis pipeline documentation.

## Orchestrator

`run_optimization_iteration.py` orchestrates the full loop:

```bash
# Full auto (Claude Code implements the recommendation, creates PR, runs experiments, analyzes):
python run_optimization_iteration.py

# Manual implementation (you already made the change and created a PR):
python run_optimization_iteration.py --skip-implement --pr 342

# Specify step (default: identify_potential_levers):
python run_optimization_iteration.py --skip-implement --pr 342 --step identify_documents

# Skip phases:
python run_optimization_iteration.py --skip-implement --skip-runner --pr 342  # analysis only
python run_optimization_iteration.py --skip-implement --skip-analysis --pr 342  # runner only

# Subset of models:
python run_optimization_iteration.py --skip-implement --pr 342 --models llama,haiku
```

Model aliases: `llama`, `gpt-oss`, `gpt5-nano`, `qwen`, `gpt4o-mini`, `gemini-flash`, `haiku`

## Key Design Decisions

- **Global counters**: Both history runs and analysis directories use a single global counter across all steps, preventing collisions when steps are interleaved.
- **Resumable phases**: Each analysis phase checks for existing output files and skips if present. Delete a file to re-run that phase.
- **History is append-only**: Never delete from `history/`. Runs are permanent records, even if flawed.
- **PlanExe must be on the PR branch**: The runner imports code from PlanExe, so PlanExe must be checked out to the PR's branch during experiments.

## License

[MIT](LICENSE)
