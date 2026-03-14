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

## Neutrality and Synthesis

Individual insight files may contain opinions and hypotheses.
`meta.json` should not.

Assume a later agent will read:

- `meta.json`
- multiple `insight_<agent>.md` files

and produce a synthesis or decision artifact.
Write the files so that later synthesis is easy:

- keep file names predictable
- keep claims auditable
- call out caveats and ambiguity
- distinguish facts from hypotheses

## Editing Guidance

- Preserve existing analysis files unless asked to rewrite them.
- When adding a new insight file, also add its filename to `meta.json` if that file already tracks `insight_files`.
- Do not rename `insight_<agent>.md` files casually once multiple agents depend on the naming pattern.
- Prefer appending new neutral provenance fields to `meta.json` over changing the meaning of existing ones.
