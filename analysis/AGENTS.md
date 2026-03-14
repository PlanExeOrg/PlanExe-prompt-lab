# Analysis Folder Guide

Scope: everything under `analysis/`.

This folder stores per-step analysis artifacts for prompt-lab experiments.
Each step gets its own directory:

- `analysis/<index>_<step_name>/meta.json`
- `analysis/<index>_<step_name>/insight_<agent>.md`

Example:

- `analysis/0_identify_potential_levers/meta.json`
- `analysis/0_identify_potential_levers/insight_codex.md`
- `analysis/0_identify_potential_levers/insight_claude.md`

## Optimization Pipeline Context

This analysis folder is part of the system prompt optimizer described in
[proposal 117](https://github.com/PlanExeOrg/PlanExe/blob/main/docs/proposals/117-system-prompt-optimizer.md).

The full workflow:

1. **Runner** (`prompt_optimizer/runner.py` in PlanExe) re-executes a single
   pipeline step with a candidate system prompt against baseline training data.
   Outputs land in `history/`.
2. **Analysis** (this folder) — agents independently examine the runner outputs
   against `baseline/train/` and write insight files.
3. **Synthesis** — a later agent reads all insight files for a step, resolves
   disagreements, and decides which prompt changes or code changes to pursue.
4. **Candidate generation** — produce prompt variants informed by synthesis
   conclusions, failed-attempt logs, and identified failure modes.
5. **Verification** — the best candidates are scored against `baseline/verify/`
   (a held-out set) to confirm improvement is not overfit to training data.

Analysis sits between the runner and synthesis. Its job is to produce
grounded, auditable evaluations that a synthesis agent can compare.

## Purpose

Keep `meta.json` factual and non-conclusive.
Keep each `insight_<agent>.md` analytical and attributable to one agent.
Do not put the final cross-agent decision in these files. A later synthesis step
should compare the insight files and decide what is most promising.

## Directory Naming

- Directory pattern: `<index>_<step_name>`
- `<index>` is a zero-based integer that matches the analysis sequence.
- `<step_name>` should match the pipeline step name and prompt folder name when possible.

## `meta.json` Rules

`meta.json` is for provenance and scope, not judgment.

Include factual fields such as:

- `prompt`: relative path to the registered prompt file
- `history`: array of relative run-history paths that were analyzed

Recommended neutral fields:

- `schema_version`
- `step`
- `created_at`
- `prompt_sha256`
- `baseline_split`
- `plans`
- `insight_files`
- `caveats`

Do not include:

- winner/champion decisions
- final verdicts
- recommendations about which model or prompt to adopt
- cross-agent synthesis conclusions

If uncertain whether a field is neutral or conclusive, keep it out of `meta.json`
and put it in an `insight_<agent>.md` file instead.

## `insight_<agent>.md` Rules

Each insight file is one agent's independent analysis.

Naming:

- `insight_codex.md`
- `insight_claude.md`
- `insight_<other_agent>.md`

Use lowercase ASCII filenames.

Each insight file should be self-contained and human-readable.
It should explain what was examined, what worked, what failed, and what to try next.

Recommended sections:

- `# Insight <Agent>`
- `## Negative Things`
- `## Positive Things`
- `## Comparison`
- `## Questions For Later Synthesis`
- `## Reflect`
- `## Potential Code Changes` (if code-level causes are relevant)
- `## Summary`

The exact headings may vary, but the file should cover:

- negative findings
- positive findings
- comparison to baseline or prior reference outputs
- hypotheses for prompt changes
- hypotheses for code changes, if relevant
- open questions that a later synthesis step should resolve
- a concise summary

## Evidence Standard

Ground claims in repository artifacts whenever possible.

Prefer citing:

- `history/.../outputs/<plan>/002-10-potential_levers.json`
- `history/.../outputs.jsonl`
- `history/.../meta.json`
- `baseline/train/...`
- registered prompt files under `prompts/`

Do not rely on memory alone when describing failure modes or strengths.

## Comparison Guidance

When comparing runs, separate:

- structural validity: valid JSON, schema compliance, option counts
- content quality: specificity, diversity, usefulness, non-generic reasoning
- operational reliability: retries, timeouts, model configuration failures

If one run is richer but much longer, say so explicitly.
Do not collapse "more verbose" and "better" into the same judgment without comment.

## Quantitative Metrics

Insight files should compute concrete metrics, not just offer impressions.
The exact metrics depend on the step, but useful patterns include:

- **Uniqueness**: count of unique items vs total items (e.g. unique lever names
  out of 15). Report both exact-match and semantic uniqueness when they diverge.
- **Average field length**: character counts for key text fields (e.g. review,
  consequences). Present as a table across runs.
- **Constraint violations**: count items that break the step's output contract
  (e.g. wrong option count, missing fields, placeholder text).
- **Template leakage**: count items that copy prompt examples, use bracket
  placeholders, or repeat robotic patterns across entries.
- **Cross-call duplication**: when a step makes multiple LLM calls and merges
  results, measure how much content is repeated across calls.

Present metrics in tables so runs can be compared at a glance.
Always explain what the numbers mean — a perfect uniqueness score can still
hide content problems (e.g. unique names but identical consequences).

## Hypothesis Format

Each insight file should propose concrete, testable hypotheses for improvement.
Label them (H1, H2, …) and for each:

- State the change (prompt wording, code fix, or workflow change).
- Cite the evidence that motivates it (specific runs, metrics, examples).
- Predict the expected effect so later experiments can confirm or refute it.

Distinguish prompt-level hypotheses (change the system prompt text) from
code-level hypotheses (change `runner.py`, the pipeline step, or validation
logic). Code changes that affect all models are generally higher-leverage than
prompt tweaks that help one model.

## Neutrality and Synthesis

Individual insight files may contain opinions and hypotheses.
`meta.json` should not.

Assume a later synthesis agent will read:

- `meta.json`
- all `insight_<agent>.md` files for the step

and produce a synthesis artifact that:

- resolves disagreements between insight files
- ranks hypotheses by expected impact and evidence strength
- decides which changes to pursue (prompt edits, code fixes, or both)
- feeds into candidate prompt generation for the next optimization round

Write insight files so that synthesis is easy:

- keep file names predictable
- keep claims auditable
- call out caveats and ambiguity
- distinguish facts from hypotheses
- label hypotheses consistently (H1, H2, …) so synthesis can cross-reference

## Key Paths

- **Baseline training data**: `baseline/train/<plan_name>/`
- **Runner outputs**: `history/{counter // 100}/{counter % 100:02d}_{step}/outputs/<plan_name>/`
- **Runner metadata**: `history/.../<run>/meta.json`, `outputs.jsonl`, `events.jsonl`
- **Registered prompts**: `prompts/<step_name>/prompt_{index}_{sha256}.txt`
- **Analysis**: `analysis/<index>_<step_name>/`

The `meta.json` in each analysis directory links to the registered prompt and
history runs that were examined. Use these paths to trace any claim back to
source artifacts.

## Editing Guidance

- Preserve existing analysis files unless asked to rewrite them.
- When adding a new insight file, also add its filename to `meta.json` if that file already tracks `insight_files`.
- Do not rename `insight_<agent>.md` files casually once multiple agents depend on the naming pattern.
- Prefer appending new neutral provenance fields to `meta.json` over changing the meaning of existing ones.
