# Analysis Folder Guide

Scope: everything under `analysis/`.

This folder stores per-step analysis artifacts for prompt-lab experiments.
Each step gets its own directory:

- `analysis/<index>_<step_name>/meta.json`
- `analysis/<index>_<step_name>/events.jsonl` (timestamped progress events)
- `analysis/<index>_<step_name>/insight_<agent>.md`
- `analysis/<index>_<step_name>/code_<agent>.md`
- `analysis/<index>_<step_name>/synthesis.md`
- `analysis/<index>_<step_name>/assessment.md` (from index 1 onward)

Example:

- `analysis/0_identify_potential_levers/meta.json`
- `analysis/0_identify_potential_levers/insight_codex.md`
- `analysis/0_identify_potential_levers/insight_claude.md`
- `analysis/0_identify_potential_levers/code_codex.md`
- `analysis/0_identify_potential_levers/code_claude.md`
- `analysis/0_identify_potential_levers/synthesis.md`

## Optimization Pipeline Context

This analysis folder is part of the system prompt optimizer described in
[proposal 117](https://github.com/PlanExeOrg/PlanExe/blob/main/docs/proposals/117-system-prompt-optimizer.md).

The full workflow:

1. **Runner** (`self_improve/runner.py` in PlanExe) re-executes a single
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

## Running the Scripts

Analysis is a four-phase process, preceded by a setup step. Each phase is
resumable — if the output files already exist, the phase is skipped.

### Quick start: run all phases

```bash
python analysis/run_analysis.py analysis/22_identify_potential_levers
python analysis/run_analysis.py analysis/22_identify_potential_levers --timeout 900
```

`run_analysis.py` runs insight → code review → synthesis → assessment in
order, passing `--timeout` (default 600s / 10 min per agent) through to each
phase. Assessment is auto-skipped for index-0 directories (no "before" to
compare against). Exits non-zero if any phase fails.

Each agent has a per-process timeout. If an agent exceeds it, the process is
killed and a placeholder error file is written so downstream phases can
continue. If both agents in a parallel phase (insight, code review) fail,
that phase exits non-zero and the pipeline stops.

### Running phases individually

The phases can also be run one at a time. This is useful when debugging or
re-running a single phase.

### Phase 0: Prepare iteration

```bash
python analysis/prepare_iteration.py identify_potential_levers 316
```

Validates the PR state is OPEN (exits with an error event if not),
pre-creates history directories (one per model), and creates a new
auto-incremented analysis directory with `meta.json` containing PR info
and the history run list.

Creates `events.jsonl` in the analysis directory and emits `prepare_start` /
`prepare_complete` (or `prepare_error`) events. Subsequent steps (runner,
insight, code review, synthesis, assessment) also write to this file, so you
can monitor progress with `tail -f analysis/<index>_<step>/events.jsonl`.

This must run before Phase 1. It ensures all metadata (including PR context)
is available from the start so insight agents can do targeted analysis.

Use `--dry-run` to preview without writing anything.
Use `--models llama,haiku` to create dirs for a subset of models.

### Phase 1: Insight files

```bash
python analysis/run_insight.py analysis/0_identify_potential_levers
```

Reads `meta.json` from the analysis directory, builds a prompt referencing
the history runs and baseline data, and runs both agents. Each agent
independently produces its `insight_<agent>.md` file.

### Phase 2: Code review files

```bash
python analysis/run_code_review.py analysis/0_identify_potential_levers
```

Reads the `insight_*.md` files produced in phase 1, concatenates them as
context, and asks both agents to review PlanExe source code for bugs and
improvement opportunities that explain the problems found in the insight
files. Each agent produces its `code_<agent>.md` file.

Phase 2 depends on phase 1 — the insight files must exist before running
the code review.

### Phase 3: Synthesis

```bash
python analysis/run_synthesis.py analysis/0_identify_potential_levers
```

Reads all `insight_*.md` and `code_*.md` files, cross-references findings
across agents, and produces a single `synthesis.md` with the top 5 ranked
directions and 1 recommendation. Uses only Claude Code (not parallel agents)
since synthesis must reconcile the independent analyses into one view.

Phase 3 depends on phases 1 and 2.

### Phase 4: Assessment

```bash
python analysis/run_assessment.py analysis/1_identify_potential_levers
```

Compares the current analysis against the previous one (auto-detected by
index - 1, or specified with `--before`). Reads all insight, code review, and
synthesis files from both directories, plus samples of actual output files
from `history/`, and produces an `assessment.md` that answers:

- Did the PR fix the issue it was supposed to fix?
- Did output quality improve or worsen? (metric-by-metric comparison table)
- Were any new issues introduced?
- **Is the PR a keeper?** (YES / NO / CONDITIONAL)

Phase 4 depends on phase 3 and requires `pr_url`/`pr_title`/`pr_description`
in the after directory's `meta.json` (see "Registering the PR" below).

### Registering the PR (before analysis)

The PR is registered in `meta.json` **during phase 0** (`prepare_iteration.py`).
The insight, code review, synthesis, and assessment agents all use this PR info
to focus their analysis.

The `run_optimization_iteration.py` orchestrator calls `prepare_iteration`
automatically before running experiments. When running phases manually:

```bash
python analysis/prepare_iteration.py identify_potential_levers 285       # Phase 0 (creates dir + registers PR)
python analysis/run_analysis.py analysis/12_identify_potential_levers    # Phases 1-4 (all at once)
```

Or run individual phases:

```bash
python analysis/prepare_iteration.py identify_potential_levers 285       # Phase 0
python analysis/run_insight.py analysis/12_identify_potential_levers     # Phase 1
python analysis/run_code_review.py analysis/12_identify_potential_levers # Phase 2
python analysis/run_synthesis.py analysis/12_identify_potential_levers   # Phase 3
python analysis/run_assessment.py analysis/12_identify_potential_levers  # Phase 4
```

`prepare_iteration.py` accepts a bare PR number or a full URL. It fetches
the title and summary via `gh` and writes `pr_url`, `pr_title`,
`pr_description` into the analysis `meta.json`.
Use `--repo owner/name` if the PR is not on `PlanExeOrg/PlanExe`.

### Completeness Heuristic

`prepare_iteration.py` (in scan-existing mode, used by `--skip-runner`)
considers a previous analysis directory "complete" if it contains a
`synthesis.md` file. If a directory has no `synthesis.md`, the script treats
it as incomplete and may try to assign the same runs to a new directory,
causing conflicts.

**When skipping the full pipeline** (e.g., writing a manual `assessment.md`
for a failed iteration), always create a `synthesis.md` stub so the next
run recognizes the directory as complete:

```bash
echo "# Synthesis\n\nAnalysis skipped — see assessment.md." > analysis/10_identify_potential_levers/synthesis.md
```

### Manual Iteration Workflow

Sometimes the full analysis pipeline (phases 1–4) is not appropriate:

- **The iteration was a clear disaster** — e.g., a quality gate broke
  non-English plans, or a change caused mass failures. Running 4 phases of
  LLM analysis on obviously-bad data wastes time and money.
- **The PR had zero observable effect** — e.g., a retry config that was never
  triggered. A manual note is more honest than a multi-page analysis saying
  "nothing changed."

In these cases, write files manually:

1. Create the analysis directory and register the PR:
   ```bash
   python analysis/prepare_iteration.py identify_potential_levers <PR#>
   ```

2. Write a manual `assessment.md` explaining what happened and the verdict.

3. Write a `synthesis.md` stub (see Completeness Heuristic above) so the
   directory is recognized as complete.

4. Optionally write a `pr_status.md` with evidence about the PR's impact.

### System Prompt

The runner always uses the `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` constant
from PlanExe's code. There is no external prompt file or CLI override — the
prompt is whatever is committed in the PlanExe repo at run time. To change the
prompt, modify `identify_potential_levers.py` and merge the PR before running
experiments.

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

- `history`: array of relative run-history paths that were analyzed

Recommended neutral fields:

- `schema_version`
- `step`
- `created_at`
- `baseline_split`
- `plans`
- `insight_files`
- `caveats`
- `pr_url`: GitHub PR URL for the change being evaluated
- `pr_title`: PR title
- `pr_description`: short summary of what the PR changes

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
- `## Rankings` (optional, but useful when comparing many runs)
- `## Negative Things`
- `## Positive Things`
- `## Comparison`
- `## Quantitative Metrics`
- `## Evidence Notes`
- `## PR Impact` (when a PR is being evaluated — see below)
- `## Questions For Later Synthesis`
- `## Reflect`
- `## Potential Code Changes` (if code-level causes are relevant)
- `## Summary`

The exact headings may vary, but the file should cover:

- negative findings
- positive findings
- comparison to baseline or prior reference outputs
- PR impact investigation (when a PR is being evaluated)
- rankings or tiering, when helpful
- quantitative metrics in tables
- evidence examples that justify the main claims
- hypotheses for prompt changes
- hypotheses for code changes, if relevant
- open questions that a later synthesis step should resolve
- a concise summary

## PR Impact Investigation

When `meta.json` contains PR information (`pr_url`, `pr_title`, `pr_description`)
and the prompt provides previous-analysis history runs for comparison, each insight
file must include a `## PR Impact` section that investigates whether the PR actually
helped, was neutral, or made things worse.

This section should:

1. **State what the PR was supposed to fix** (from `pr_title` / `pr_description`).
2. **Compare before vs after runs** using the same metrics from the Quantitative
   Metrics section. Read actual output files from both the current and previous
   history runs. Present a comparison table with columns:
   Metric | Before (runs X–Y) | After (runs X–Y) | Change.
3. **Determine if the PR fixed the targeted issue.** Cite specific evidence.
4. **Check for regressions** — did the PR make anything worse?
5. **End with a verdict**: one of:
   - **KEEP** — the PR produces a significant, measurable improvement.
   - **REVERT** — the PR made things worse or produced no benefit.
   - **CONDITIONAL** — the PR helps in some ways but introduces issues that
     need follow-up work.

The verdict should be evidence-based. "No observable change" is a valid reason
to recommend REVERT — changes that add complexity without measurable benefit
should not be kept.

When no previous-analysis runs are available (e.g. the baseline analysis at
index 0), skip this section entirely.

## `code_<agent>.md` Rules

Each code review file is one agent's independent review of PlanExe source code,
informed by the insight files from the same analysis step.

Naming:

- `code_codex.md`
- `code_claude.md`
- `code_<other_agent>.md`

Use lowercase ASCII filenames.

Each code review file should be self-contained and trace its findings back to
the insight files that motivated the review.

Recommended sections:

- `# Code Review (<Agent>)`
- `## Bugs Found` — confirmed bugs with file:line references
- `## Suspect Patterns` — code that looks wrong but needs more context
- `## Improvement Opportunities` — changes that could boost output quality
- `## Trace to Insight Findings` — map each code issue to insight-file
  observations it explains
- `## Summary`

Label bugs `B1`, `B2`, … and improvements `I1`, `I2`, …
Cite exact file paths and line numbers from the PlanExe repo.

Code review files should not modify any source files. They are read-only
analysis artifacts, like insight files.

## `synthesis.md` Rules

Each analysis step produces one `synthesis.md` file. Unlike insight and code
review files, synthesis is not per-agent — it is a single document that
reconciles all independent analyses.

Recommended sections:

- `# Synthesis`
- `## Cross-Agent Agreement` — where the insight/code review files agree
- `## Cross-Agent Disagreements` — where they disagree, with a verdict
- `## Top 5 Directions` — ranked by impact, with type/evidence/effort/risk
- `## Recommendation` — the single best action to take first
- `## Deferred Items` — worth doing later but not first

The synthesis file should:

- Verify disputed claims by reading actual source code, not just trusting
  one agent over another
- Prefer code fixes over prompt tweaks when the fix benefits all models
- Rank by evidence strength: confirmed bug > hypothesis > suspicion
- Be specific about what to change (file, line, the fix or new wording)

## Evidence Standard

Ground claims in repository artifacts whenever possible.

Prefer citing:

- `history/.../outputs/<plan>/002-10-potential_levers.json`
- `history/.../outputs.jsonl`
- `history/.../meta.json`
- `baseline/train/...`

Do not rely on memory alone when describing failure modes or strengths.

## Comparison Guidance

When comparing runs, separate:

- structural validity: valid JSON, schema compliance, option counts
- content quality: specificity, diversity, usefulness, non-generic reasoning
- content credibility: are claims grounded in the project context or fabricated?
- verbosity vs substance: is increased length adding real information?
- operational reliability: retries, timeouts, model configuration failures

If one run is richer but much longer, say so explicitly.
Do not collapse "more verbose" and "better" into the same judgment without comment.

**Critical**: Longer output is NOT inherently better. Compare field lengths against
the baseline training data. If consequences are 3-4× longer than baseline but don't
contain proportionally more decision-relevant information, that is a regression in
quality-per-word, even if structural compliance is perfect.

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
- **Fabricated quantification**: count of percentage claims, cost deltas, or
  numeric estimates that appear in lever fields (e.g. "reduces costs by 30%",
  "15-20% increase"). These are almost always fabricated by the LLM since the
  project context rarely contains supporting evidence for specific numbers.
- **Baseline length comparison**: compare average field lengths against the
  baseline training data (`baseline/train/<plan>/002-10-potential_levers.json`).
  Report the ratio (e.g. "consequences are 3.6× longer than baseline"). A ratio
  above 2× for any field is a warning sign for verbosity without substance.

Present metrics in tables so runs can be compared at a glance.
Always explain what the numbers mean — a perfect uniqueness score can still
hide content problems (e.g. unique names but identical consequences).

Useful minimums for insight files:

- at least one uniqueness table
- at least one length/depth table or equivalent quantitative signal
- at least one constraint-violation or template-leakage count when relevant
- at least one baseline length comparison (current vs baseline avg field lengths)

## OPTIMIZE_INSTRUCTIONS Alignment

The PlanExe source file `identify_potential_levers.py` contains an
`OPTIMIZE_INSTRUCTIONS` constant that defines the project-level goals and known
pitfalls for lever generation. Every analysis agent should read it (it is near
the top of the file, after imports). When proposing improvements, agents should:

- **Check alignment**: Does the current system prompt, Pydantic schema, and
  validator code align with `OPTIMIZE_INSTRUCTIONS`? If not, flag the mismatch.
- **Propose updates to OPTIMIZE_INSTRUCTIONS itself**: If analysis reveals a new
  recurring problem (e.g., a pattern not yet documented), propose adding it to
  the known-problems list. The constant is living documentation, not frozen.
- **Guard plan quality, not just lever quality**: The instructions emphasize that
  levers must lead to *realistic, feasible, actionable* plans. An option that
  sounds strategic but cannot be scheduled, resourced, or executed by a human or
  AI agent is a failure — even if it passes all structural validators.
- **Watch for optimism bias**: The downstream scenario picker tends to select the
  most ambitious option. If levers only offer moonshot options, the final plan
  will be unrealistically optimistic. Each lever should include at least one
  conservative, low-risk path.
- **Internationalization**: PlanExe receives prompts in many non-English
  languages. Validators that hard-code English keywords (e.g., checking for
  `"Controls "` or `"Weakness:"` in the LLM response) will reject valid output
  when the model responds in the prompt's language. Flag any English-only
  validation as a bug or improvement opportunity.

## Hypothesis Format

Each insight file should propose concrete, testable hypotheses for improvement.

Prompt or workflow hypotheses:

- label them `H1`, `H2`, …

Code-level hypotheses:

- label them `C1`, `C2`, …

For each:

- State the change (prompt wording, code fix, or workflow change).
- Cite the evidence that motivates it (specific runs, metrics, examples).
- Predict the expected effect so later experiments can confirm or refute it.

Distinguish prompt-level hypotheses (change the system prompt text) from
code-level hypotheses (change `runner.py`, the pipeline step, or validation
logic). Code changes that affect all models are generally higher-leverage than
prompt tweaks that help one model.

If an insight file revises or disagrees with an earlier analysis, verify the
disputed point directly from repository artifacts before writing the claim.
Do not copy another agent's metric or conclusion without re-checking it.

## Neutrality and Synthesis

Individual insight files may contain opinions and hypotheses.
`meta.json` should not.

Assume a later synthesis agent will read:

- `meta.json`
- all `insight_<agent>.md` files for the step
- all `code_<agent>.md` files for the step

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
- label hypotheses consistently (`H*` and `C*`) so synthesis can cross-reference
- if you rank runs, explain the basis for the ranking

## Key Paths

- **Baseline training data**: `baseline/train/<plan_name>/`
- **Runner outputs**: `history/{counter // 100}/{counter % 100:02d}_{step}/outputs/<plan_name>/`
- **Runner metadata**: `history/.../<run>/meta.json`, `outputs.jsonl`, `events.jsonl`
- **Analysis**: `analysis/<index>_<step_name>/`

The `meta.json` in each analysis directory links to the history runs that
were examined. Use these paths to trace any claim back to source artifacts.

## Experiment Insights

Lessons learned from past optimization iterations that should inform future
analysis. These are patterns the analysis agents should watch for.

### Pydantic hard constraints vs soft prompt guidance

**Context**: The `identify_potential_levers` step had `max_length=7` on the
`DocumentDetails.levers` Pydantic field. When haiku returned 8 levers in run 87
(plan: gta_game), the entire LLM call failed with a `ValidationError` →
`LLMChatError`, discarding all levers — including the valid ones. This wasted
tokens on a full retry and reduced the success rate for that model.

**Principle**: Prefer soft guidance in the system prompt (e.g., "Propose 5 to 7
levers") over hard Pydantic constraints (`max_length=7`) when a downstream step
already handles over-generation. The `DeduplicateLeversTask` trims extras, so
the schema-level cap was redundant and harmful.

**What to watch for in analysis**:
- LLM call failures caused by schema validation (check `events.jsonl` for
  `LLMChatError` entries with `ValidationError` in the message).
- Models that consistently produce slightly more items than the hard cap — this
  signals the cap is too tight, not that the model is broken.
- Success rate drops that correlate with specific models + plans — these often
  indicate a schema constraint issue rather than a prompt quality issue.

**General rule**: `min_length` constraints are useful (catch under-generation).
`max_length` constraints are risky when downstream dedup/trimming exists. Remove
them and let the pipeline handle overflow gracefully.

### Content quality vs structural compliance

**Context**: After 17 iterations of prompt optimization, the success rate improved
from ~60% to 97.1%. However, an external review of full PlanExe reports
(hong_kong_game plan) rated the baseline report **6.5/10** and the report built
on optimized levers **5.8/10**. The verdict: *"Version 2 improved specificity,
but regressed in credibility."*

The optimization loop had been maximizing **structural compliance** (valid JSON,
validators passing, correct field formats) without any signal for **content
quality** (are levers grounded? are numbers defensible? is the tone appropriate
for a strategic document?).

**Measured impact**: Baseline hong_kong_game levers averaged 269 chars for
consequences, 162 chars for options, 153 chars for reviews. Iteration 17 output
averaged 980, 321, and 319 chars respectively — 3.6×, 2.0×, and 2.1× longer.
The additional length consisted largely of fabricated percentage claims,
marketing-copy language, and verbose restatements rather than new information.

**Specific prompt elements that drove the regression**:
- Mandatory quantification (*"Include measurable outcomes: a % change, capacity
  shift, or cost delta"*) forced models to fabricate numbers.
- Verbose consequence chains (*"Immediate → Systemic → Strategic"*) inflated
  length without proportional substance.
- Formulaic option triads (*"conservative → moderate → radical"*) produced
  predictable three-point spreads instead of genuinely distinct approaches.
- Tech-forcing (*"Radical option must include emerging tech/business model"*)
  pushed toward flashy, unsupported claims.

**Principle**: Structural compliance is necessary but not sufficient. Every
analysis iteration must measure content quality alongside success rate. A change
that raises success rate from 90% to 97% but makes the content of every
successful plan less credible is a net negative.

**What to watch for in analysis**:
- Field length ratios vs baseline above 2× (warning) or 3× (likely regression).
- Fabricated percentage claims that have no basis in the project context.
- Marketing-copy tone: phrases like "cutting-edge", "game-changing",
  "breathless", "revolutionary" in strategic analysis fields.
- Formulaic option structures where all three options follow an obvious
  template (conservative/moderate/radical or similar triads).
- Loss of grounding: options that sound impressive but don't connect to
  specific project constraints, stakeholders, or decisions.

**General rule**: Content quality regressions that affect all successful plans
(e.g., 34/35) are higher priority than structural fixes that recover one
failed plan (e.g., 1/35). Both matter, but quality × breadth outweighs
compliance × edge-case.

## Editing Guidance

- Preserve existing analysis files unless asked to rewrite them.
- When adding a new insight file, also add its filename to `meta.json` if that file already tracks `insight_files`.
- Do not rename `insight_<agent>.md` files casually once multiple agents depend on the naming pattern.
- Prefer appending new neutral provenance fields to `meta.json` over changing the meaning of existing ones.
