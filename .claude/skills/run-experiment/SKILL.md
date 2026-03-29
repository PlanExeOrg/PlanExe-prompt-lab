---
name: run-experiment
description: Run self_improve experiments for a pipeline step across all models, using run_optimization_iteration.py
---

# Run Experiment

Run `self_improve/runner.py` experiments for a pipeline step across all configured models.

## Prerequisites

- PlanExe repo at `/Users/neoneye/git/PlanExeGroup/PlanExe` must be on the correct branch/commit.
- Python 3.11 at `/opt/homebrew/bin/python3.11` (has llama_index and dependencies).
- Ollama running locally (for `ollama-llama3.1`).
- API keys configured in `.env` (for cloud models).

## Determine the command

The orchestrator is `run_optimization_iteration.py` in the PlanExe-prompt-lab repo. It handles:
- Commit/branch verification
- Preparing the analysis directory and history output dirs
- Running models (local sequential, then cloud parallel)
- Analysis pipeline

### For a baseline run (no PR, testing current main)

```bash
cd /Users/neoneye/git/PlanExeGroup/PlanExe-prompt-lab
python run_optimization_iteration.py \
    --skip-implement \
    --commit <commit_hash> \
    --step <step_name> \
    --baseline-dir <input_dir>
```

### For a PR run (testing a branch)

```bash
cd /Users/neoneye/git/PlanExeGroup/PlanExe-prompt-lab
python run_optimization_iteration.py \
    --skip-implement \
    --pr <pr_number> \
    --step <step_name> \
    --baseline-dir <input_dir>
```

PlanExe must be checked out to the PR branch before running.

### Common flags

- `--skip-analysis` — skip the analysis pipeline (useful when you only want runner output)
- `--models llama,haiku` — run a subset of models (comma-separated aliases)
- `--baseline-dir <path>` — override the default `baseline/train` input directory

## Input directories

The `--baseline-dir` depends on which step you are running:

| Step | Typical input directory |
|------|----------------------|
| `identify_potential_levers` | `baseline/train` |
| `deduplicate_levers` | `snapshot/0_identify_potential_levers` |
| `enrich_potential_levers` | `snapshot/1_deduplicate_levers` |
| `identify_documents` | `baseline/train` |

Snapshot directories contain baseline plan files up to (but not including) the step being tested. See `snapshot/AGENTS.md` for details.

## What happens when you run it

1. **Verify commit/branch** — confirms PlanExe HEAD matches the specified commit or PR branch.
2. **Prepare iteration** — creates a new analysis directory and pre-creates history output dirs for each model.
3. **Run experiments** — `ollama-llama3.1` runs sequentially (local GPU), then 6 cloud models run in parallel. Each model processes all plans from the input directory.
4. **Analysis** — if this is the first run of a step, runs baseline comparison. If a prior analysis exists, runs assessment (before vs after).

## Models

All 7 models run by default:

| Alias | Full name |
|-------|-----------|
| `llama` | `ollama-llama3.1` (local, sequential) |
| `gpt-oss` | `openrouter-openai-gpt-oss-20b` |
| `gpt5-nano` | `openai-gpt-5-nano` |
| `qwen` | `openrouter-qwen3-30b-a3b` |
| `gpt4o-mini` | `openrouter-openai-gpt-4o-mini` |
| `gemini-flash` | `openrouter-gemini-2.0-flash-001` |
| `haiku` | `anthropic-claude-haiku-4-5-pinned` |

## After the run

- History outputs land in `history/{bucket}/{counter}_{step}/outputs/<plan_name>/`.
- Use `copy_history_to_snapshot.py` to copy outputs into a new snapshot for downstream steps.
- Analysis artifacts land in `analysis/{index}_{step}/`.

## Supported steps

`identify_potential_levers`, `deduplicate_levers`, `enrich_potential_levers`, `identify_documents`
