# Insight Claude

## Overview

This analysis covers 8 history runs (1/09–1/16) using
`prompt_3_00bdd5a3e5e06aa3bc3638e59f6f1c586b4532152bc73f44862839998e2ae381.txt`
against 5 training plans (silo, gta_game, sovereign_identity, hong_kong_game,
parasomnia_research_unit). No PR is registered in `meta.json`, so no PR Impact section
is produced. Prompt_3 is the successor to prompt_2 (used in analysis/14), which the
analysis/14 assessment recommended upgrading specifically to fix the two-bullet
`review_lever` instruction that was causing llama3.1 call-1 failures.

---

## Run Overview

| Run | Model | Workers | Outcome (2nd attempt) |
|-----|-------|---------|----------------------|
| 1/09 | ollama-llama3.1 | 1 | **Incomplete** — only a `run_single_plan_start` for silo; no completion or error event logged. No output files. |
| 1/10 | ollama-llama3.1 | 1 | 4/5 — parasomnia timed out (ReadTimeout after 120s) |
| 1/11 | openrouter-openai-gpt-oss-20b | 4 | 4/5 — hong_kong_game: `ValueError('Could not extract json string from output: ')` |
| 1/12 | openai-gpt-5-nano | 4 | 4/5 — parasomnia: Pydantic `ValidationError` (review_lever = 'Not applicable here') |
| 1/13 | openrouter-qwen3-30b-a3b | 4 | 5/5 |
| 1/14 | openrouter-openai-gpt-4o-mini | 4 | 5/5 |
| 1/15 | openrouter-gemini-2.0-flash-001 | 4 | 5/5 |
| 1/16 | anthropic-claude-haiku-4-5-pinned | 4 | 5/5 |

**Note on first-attempt failures (runs 1/11–1/16):** All runs except 1/10 and 1/16 fired
at 03:27 UTC with authentication errors (missing API keys). A second batch ran at 09:16 UTC
and succeeded. Run 1/16 had its own first-attempt auth failure at 09:15 UTC (just one minute
before the 09:16 batch). The auth failures are infrastructure issues, not prompt-quality issues.

---

## Negative Things

### N1 — gpt-5-nano parasomnia: `review_lever = 'Not applicable here'`

Run 1/12 parasomnia failed with 6 `ValidationError` entries:

```
levers.0.review_lever
  Value error, review_lever must contain 'Controls [Tension A] vs. [Tension B].'
  input_value='Not applicable here'
```

The model produced 6 levers all with `review_lever = 'Not applicable here'`, causing complete
plan failure after 357 seconds of compute. This is the same all-or-nothing cascade pattern
from earlier iterations: one non-compliant field discards the entire response.

Evidence: `history/1/12_identify_potential_levers/events.jsonl` lines 18–19.

### N2 — gpt-5-nano is extremely slow

Run 1/12 (second attempt): hong_kong_game took 292s, silo 527s, sovereign_identity 792s,
gta_game 1051s. The parasomnia plan consumed 358s before failing. These are outlier latencies
compared to other models (gemini: 32–40s, gpt-4o-mini: 47–54s).

### N3 — llama3.1 ReadTimeout on parasomnia

Run 1/10 parasomnia failed with `ReadTimeout('timed out')` after 120s. This is a timeout
configuration issue, not a format compliance issue, but it remains a reliability gap.

Evidence: `history/1/10_identify_potential_levers/events.jsonl` line 10,
`history/1/10_identify_potential_levers/outputs.jsonl` line 5.

### N4 — gpt-oss-20b JSON extraction failure on hong_kong_game

Run 1/11 hong_kong_game failed with `ValueError('Could not extract json string from output: ')`.
This is the same rotating-plan JSON failure seen in analysis/14 runs. The model produces
non-JSON text for some plans.

Evidence: `history/1/11_identify_potential_levers/events.jsonl` line 18.

### N5 — qwen3-30b option prefix violations

Run 1/13 silo output contains options with prohibited prefix labels. Example from
`history/1/13_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`:

```json
"options": [
  "Imperial Oversight: Absolute rule by a technocratic elite",
  "Decentralized Council: Rotating regional leadership with meritocratic selection",
  "Hybrid AI-Human Governance: Algorithmic policy enforcement with human appeal mechanisms"
]
```

The prompt explicitly prohibits prefixes ("NO prefixes/labels in options"). Three of the first
five levers in the silo output carry colon-prefixed labels. This violates the structural
constraint.

### N6 — qwen3-30b consequences contamination persists

Several levers in run 1/13 outputs have the `review_lever` text duplicated into the
`consequences` field. Example from `history/1/13_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`
lever "Silo Ecosystem Governance":

- `consequences`: "...Long-term stability but stifles innovation. **Controls uniformity vs.
  adaptability. Weakness: The options fail to account for generational cultural drift.**"
- `review`: "Controls uniformity vs. adaptability. Weakness: The options fail to account for
  generational cultural drift."

The same text appears in both fields. The analysis/14 assessment noted this affects ~67% of
qwen3 levers and recommended a post-parse repair validator.

### N7 — Run 1/09 incomplete (ollama-llama3.1)

Run 1/09 has only one event: `run_single_plan_start` for silo. No completion or error event
was recorded. No output files exist beyond `track_activity.jsonl`. The run appears to have
been interrupted before completion. This run cannot be analyzed for quality.

Evidence: `history/1/09_identify_potential_levers/events.jsonl` (1 line only).

### N8 — Lever over-generation persists across all models

The prompt instructs "5 to 7 levers per response." All models that make 3 LLM calls produce
15–22 levers in the merged `002-10-potential_levers.json`. This is by design (multi-call
architecture), but the systemic gap between the stated "5 to 7" constraint and the actual
merged output warrants attention in any future prompt revision.

---

## Positive Things

### P1 — llama3.1 silo and sovereign_identity now succeed

The most important result of this batch: run 1/10 (llama3.1) succeeds for **silo** and
**sovereign_identity**, which were the two plans that failed every single llama3.1 run under
prompt_2 (analysis/14). Under prompt_2, call-1 of llama3.1 for these plans consistently
produced levers with either `"Controls X vs. Y."` or `"Weakness: ..."` in separate levers —
never both in the same `review_lever` field. The new prompt_3 combined example resolved this.

Evidence:
- `history/1/10_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`
  — 22 levers, all `review` fields contain "Controls X vs. Y. Weakness: ..." format
- `history/1/10_identify_potential_levers/events.jsonl` — silo and sovereign_identity both
  show `run_single_plan_complete`
- Contrast with analysis/14 assessment: "Two plans (silo, sovereign_identity) fail every
  llama3.1 run because call-1 hits `check_review_format`"

### P2 — review_lever format compliance is high across all models with output

Every output file I inspected showed `review` fields in the required format
`"Controls [Tension A] vs. [Tension B]. Weakness: The options ..."`. The only violation that
reached the validator was run 1/12 gpt-5-nano parasomnia (N1 above).

### P3 — Three models achieve perfect 5/5 success rate

Runs 1/13 (qwen3), 1/14 (gpt-4o-mini), 1/15 (gemini-2.0-flash), and 1/16 (claude-haiku)
all complete 5/5 plans in the second attempt. This is consistent with the analysis/14 batch.

### P4 — Domain specificity is strong

The gemini-2.0-flash parasomnia output
(`history/1/15_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json`)
contains 17 highly domain-specific levers: "Monitoring Intensity", "Recruitment Breadth",
"Inclusion Stringency", "Environmental Control", "Scoring Automation", "Data Sharing Scope",
etc. These are genuinely project-specific, not generic templates. Consequences include
measurable outcomes (e.g., "50-100% data volume increase", "15-25% reduction in eligible
participants").

### P5 — qwen3-30b gta_game output has high-quality measurable consequences

Run 1/13 gta_game output (`history/1/13_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`)
demonstrates measurable systemic effects in every lever:

- "Immediate: Introduces AI-driven dynamic story generation → Systemic: Increases development
  time by 22% (per 2023 GDC data) → Strategic: Enhances player immersion..."
- "Immediate: Adopt proprietary game engine development → Systemic: Raises R&D costs by $15M..."

This level of quantification exceeds baseline quality for this plan.

### P6 — gemini-2.0-flash is fastest overall

Gemini completed all 5 plans in 32–40 seconds each (second attempt). This is 2–3× faster than
gpt-4o-mini (47–54s) and >5× faster than qwen3 (107–215s).

---

## Comparison

### Prompt_3 vs. Prompt_2 (analysis/14) for llama3.1

This is the central comparison for this analysis batch.

| Metric | prompt_2 (runs 1/02, based on analysis/14) | prompt_3 (run 1/10) |
|--------|---------------------------------------------|---------------------|
| silo success | ✗ (call-1 `check_review_format` failure) | ✓ |
| sovereign_identity success | ✗ (call-1 `check_review_format` failure) | ✓ |
| gta_game success | ✓ | ✓ |
| hong_kong_game success | ✓ | ✓ |
| parasomnia success | ✓ (partial, 1-call recovery via PR #292) | ✗ (ReadTimeout) |
| **llama3.1 total** | **3/5** | **4/5** |

The prompt_3 change fixed the review_lever format failures for silo and sovereign_identity.
The remaining failure (parasomnia ReadTimeout) is a timeout issue, not a format compliance issue.

### Current batch vs. prior batch (analysis/14) overall

| Metric | Analysis/14 (runs 1/02–1/08) | Analysis/15 (runs 1/10–1/16, excluding 1/09) |
|--------|-------------------------------|----------------------------------------------|
| Overall success rate | 32/35 (91.4%) | 32/35 (91.4%) |
| llama3.1 success | 3/5 | 4/5 (improved by +1) |
| gpt-5-nano success | 5/5 | 4/5 (regressed by −1, parasomnia review failure) |
| gpt-oss-20b success | 4/5 | 4/5 (same) |
| qwen3 success | 5/5 | 5/5 (same) |
| gpt-4o-mini success | 5/5 | 5/5 (same) |
| gemini-2.0-flash success | 5/5 | 5/5 (same) |
| claude-haiku success | 5/5 | 5/5 (same) |

The net change is 0: llama3.1 gained 1 success, gpt-5-nano lost 1. Overall rate unchanged.

### History runs vs. baseline training data

Comparing run 1/13 (qwen3, silo) with
`baseline/train/20250321_silo/002-10-potential_levers.json`:

| Dimension | Baseline | Run 1/13 (qwen3) |
|-----------|----------|------------------|
| Lever count | 15 | 15 |
| Domain specificity | High (silo-specific names) | Mixed (some generic names like "Funding and Stakeholder Alignment") |
| Measurable consequences | 8/15 have % or measurable metric | 8/15 have % or measurable metric |
| Option prefixes | 0 violations | 3+ violations |
| Consequences contamination | 0 | ~4/15 |
| review format | All compliant | All compliant |

Baseline is cleaner structurally; qwen3 matches on measurability but has format violations.

Comparing run 1/15 (gemini, parasomnia) with
`baseline/train/20260311_parasomnia_research_unit/002-10-potential_levers.json`:

| Dimension | Baseline | Run 1/15 (gemini) |
|-----------|----------|-------------------|
| Lever count | 15 | 17 |
| Domain specificity | High (study protocol names) | High (study protocol names) |
| Measurable consequences | 12/15 (very high) | 14/17 (high) |
| Option prefixes | 0 | 0 |
| review format | All compliant | All compliant |

Run 1/15 matches baseline quality closely. Both show deep domain expertise.

---

## Quantitative Metrics

### Success Rate by Run

| Run | Model | Plans OK | Plans Failed | Failure Mode |
|-----|-------|----------|--------------|--------------|
| 1/09 | llama3.1 | 0 | N/A | Run incomplete |
| 1/10 | llama3.1 | 4/5 | 1 | ReadTimeout (parasomnia) |
| 1/11 | gpt-oss-20b | 4/5 | 1 | JSON extraction failure (hong_kong_game) |
| 1/12 | gpt-5-nano | 4/5 | 1 | ValidationError: review_lever (parasomnia) |
| 1/13 | qwen3-30b | 5/5 | 0 | — |
| 1/14 | gpt-4o-mini | 5/5 | 0 | — |
| 1/15 | gemini-2.0-flash | 5/5 | 0 | — |
| 1/16 | claude-haiku | 5/5 | 0 | — |

**Combined (runs 1/10–1/16): 32/35 (91.4%)**

### Lever Count per Plan (selected outputs)

| Run | Model | Plan | Lever Count | vs. Prompt Limit (5–7/call) |
|-----|-------|------|-------------|------------------------------|
| 1/10 | llama3.1 | silo | 22 | Over (3 calls × ~7 = 21+) |
| 1/13 | qwen3-30b | silo | 15 | Over (3 calls × 5 = 15) |
| 1/13 | qwen3-30b | gta_game | 15 | Over (3 calls × 5 = 15) |
| 1/14 | gpt-4o-mini | silo | 18 | Over (3 calls × 6 = 18) |
| 1/15 | gemini-2.0-flash | parasomnia | 17 | Over (3 calls × ~6 = 18) |
| 1/16 | claude-haiku | parasomnia | 17 | Over (3 calls × ~6 = 18) |
| Baseline | — | silo | 15 | Over (multi-call) |
| Baseline | — | parasomnia | 15 | Over (multi-call) |

All outputs exceed 7 because the step is a multi-call pipeline (3 LLM calls × 5–7 = 15–22).
The "5 to 7" constraint applies per LLM call, not per merged output.

### review_lever Format Compliance

| Run | Model | Plans with review violations in output | Plans with validation failure |
|-----|-------|----------------------------------------|-------------------------------|
| 1/10 | llama3.1 | 0 | 0 |
| 1/11 | gpt-oss-20b | 0 | 0 |
| 1/12 | gpt-5-nano | — (parasomnia failed) | 1 (parasomnia) |
| 1/13 | qwen3-30b | 0 | 0 |
| 1/14 | gpt-4o-mini | 0 | 0 |
| 1/15 | gemini-2.0-flash | 0 | 0 |
| 1/16 | claude-haiku | 0 | 0 |

**LLMChatError with ValidationError count: 1** (run 1/12, parasomnia, 6 levers × 1 validation error each = 6 errors logged in single event).

### Option Prefix Violations (sampled)

| Run | Model | Plan | Prefix Violations |
|-----|-------|------|-------------------|
| 1/10 | llama3.1 | silo | 0 |
| 1/13 | qwen3-30b | silo | ≥3 levers with colon prefixes |
| 1/13 | qwen3-30b | gta_game | 0 |
| 1/14 | gpt-4o-mini | silo | 0 |
| 1/15 | gemini-2.0-flash | parasomnia | 0 |
| 1/16 | claude-haiku | parasomnia | 0 |

Prefix violations are confined to qwen3-30b on certain plans.

### Execution Speed (second attempt, per-plan)

| Run | Model | Fastest Plan | Slowest Plan | Total |
|-----|-------|-------------|-------------|-------|
| 1/10 | llama3.1 | 81s (gta) | 132s (sovereign) | ~503s |
| 1/12 | gpt-5-nano | 292s (hk) | 1051s (gta) | ~2963s |
| 1/13 | qwen3-30b | 107s (gta) | 215s (parasomnia) | 726s |
| 1/14 | gpt-4o-mini | 48s (silo) | 54s (parasomnia) | 261s |
| 1/15 | gemini-2.0-flash | 33s (silo) | 40s (hk) | 184s |
| 1/16 | claude-haiku | 77s (gta) | 220s (hk) | 575s |

### Template Leakage in review Fields

Across all inspected outputs, "The options fail to consider/account for/address/neglect/do not
consider/ignore..." appear in 100% of review fields. These are all variants of the required
`Weakness:` clause. No evidence of copied `[Tension A]` / `[Tension B]` bracket placeholders
was observed in final output files. This is consistent with analysis/14 finding of 1.1%
bracket leakage; no degradation observed.

### Consequences Contamination (qwen3-30b)

From `history/1/13_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`:
5 of 15 levers (33%) have review text embedded in the `consequences` field. This is lower than
the analysis/14 estimate of ~67% for qwen3, but the sample is limited to one plan and the
pattern persists.

---

## Evidence Notes

**E1** — llama3.1 silo success confirmed:
`history/1/10_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`
contains 22 levers, all with properly formatted `review` fields. The raw file
`002-9-potential_levers_raw.json` shows 3 LLM call responses, each with 7–8 levers,
all `review_lever` fields formatted as "Controls X vs. Y. Weakness: ...".

**E2** — gpt-5-nano parasomnia failure:
`history/1/12_identify_potential_levers/outputs.jsonl` shows parasomnia with
`"status": "error"` and the full validation error message. The model returned
`review_lever = 'Not applicable here'` for all 6 levers in its response — suggesting the
model interpreted the parasomnia plan as a context where "tension controls" didn't apply.

**E3** — qwen3-30b option prefix violation:
`history/1/13_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`,
lever "Governance Architecture", `options[0]`: `"Imperial Oversight: Absolute rule by a
technocratic elite"`. Multiple other levers in the same file follow the same pattern.

**E4** — Review format previously fixed by prompt_3:
The analysis/14 assessment at `analysis/14_identify_potential_levers/assessment.md` (lines
123–135) explicitly recommended fixing the two-bullet `review_lever` instruction. Run 1/10
confirms the fix worked for llama3.1.

**E5** — gpt-oss-20b JSON failure is plan-dependent:
In analysis/14 run 1/03 the failure was hong_kong_game; in run 1/11 the failure is also
hong_kong_game. This is consistent across two runs, suggesting hong_kong_game (not parasomnia
or sovereign_identity) triggers the JSON extraction issue for this model.

---

## Hypotheses

**H1** — `review_lever` prompt fix (prompt_3) successfully resolved llama3.1's silo and
sovereign_identity failures.
- *Evidence*: Run 1/10 shows both plans completing successfully (they failed under prompt_2
  in runs 1/02 and every prior llama3.1 run).
- *Prediction*: Running llama3.1 again with prompt_3 should show ≥4/5 success consistently,
  with silo and sovereign_identity no longer failing due to `check_review_format`.

**H2** — gpt-5-nano produces `review_lever = 'Not applicable here'` when it fails to
  identify a strategic tension in the given domain.
- *Evidence*: The parasomnia plan is a medical research protocol where "strategic tensions"
  are less obvious. All 6 levers in the failed response had the same non-compliant value.
- *Prediction*: This failure mode may recur for technical/scientific plans with any model
  that cannot map the `Controls X vs. Y` template to domain tensions.
- *Fix direction*: Adding a worked example in the prompt using a scientific/research context
  (not just a generic business example) might reduce this failure mode.

**H3** — gpt-oss-20b's hong_kong_game JSON failure is context-length sensitive.
- *Evidence*: The failure consistently occurs for hong_kong_game (long plan description?),
  while other plans succeed. The `ValueError('Could not extract json string from output: ')`
  suggests partial output or truncation.
- *Prediction*: Reducing the hong_kong_game prompt context (pre-summary truncation) would fix
  this. The analysis/14 backlog entry on "gpt-oss-20b rotating JSON failures" remains open.

**H4** — qwen3-30b's option prefix violations are call-specific and plan-specific.
- *Evidence*: The gta_game output for run 1/13 shows no prefix violations, but silo does.
  This suggests context-dependent compliance rather than a general model limitation.
- *Prediction*: Adding a negative example in the prompt showing a prefix-labeled option
  alongside the prohibition text might reduce violations.

---

## Questions For Later Synthesis

1. **PR #294 context**: The git log references `history runs 109-115 for iteration 15
   (review_lever prompt fix, PR #294)`. Runs 1/09–1/16 correspond to iterations 109–116 in
   absolute numbering. What specific change does PR #294 make? Is prompt_3 the prompt from
   PR #294, or is it a previous candidate that PR #294 evaluates?

2. **gpt-5-nano parasomnia review failure**: Is `'Not applicable here'` a known fallback
   pattern for gpt-5-nano, or is it specific to domains where strategic tension framing
   feels artificial?

3. **qwen3 consequences contamination at scale**: With 5/5 plans available in run 1/13,
   what is the actual contamination rate across all plans (not just silo)?

4. **llama3.1 parasomnia timeout**: Is the 120s timeout configured too low for the
   parasomnia plan specifically? The parasomnia description is longer and more complex
   than gta_game or silo. Could a plan-adaptive timeout or a plan-specific shorter prompt
   help?

5. **gpt-4o-mini added to rotation**: The analysis/14 assessment recommended retaining
   gpt-4o-mini in future test matrices. It continues to show 5/5 with good quality.
   Should it be formally added to the standard model set?

---

## Reflect

The single most important signal in this batch is **H1 confirmed**: prompt_3's combined
review_lever example fixed llama3.1's silo and sovereign_identity failures that had persisted
across every prior run. This is a clear, measurable improvement that validates the analysis/14
recommendation.

However, the overall success rate is unchanged (32/35) because gpt-5-nano gained a new
failure mode on parasomnia. The net is neutral, but the improvement for llama3.1 is real and
the gpt-5-nano failure is a different issue (domain-specific non-compliance vs. structural
prompt misinterpretation).

The two persistent structural issues from analysis/14 remain open:
1. qwen3-30b consequences contamination (still ~33% of levers in silo, possibly more elsewhere)
2. gpt-oss-20b JSON extraction failure (consistently hong_kong_game)

Neither was caused by prompt_3; both existed under prompt_2 as well.

---

## Potential Code Changes

**C1** — `break` → `continue` in call-2 failure handler
- File: `identify_potential_levers.py` (around line 278 per analysis/14)
- Change: Replace `break` with `continue` so that when call-2 fails, call-3 still runs.
- Evidence: analysis/14 NI2 — "a `continue` instead of `break` would let call-3 attempt,
  potentially doubling recovered levers." Still open in backlog.
- Risk: Very low. Zero cascading effect.

**C2** — Partial recovery telemetry
- Add a `run_single_plan_partial_recovery` or similar event to `events.jsonl` when the
  `break` exception handler fires.
- Evidence: analysis/14 NI1 — "no partial-recovery event" in logs. Still open in backlog.
- Risk: None.

**C3** — Post-parse `consequences` repair validator for qwen3
- Add a `@field_validator('consequences', mode='after')` that detects and strips trailing
  review text (`"Controls … Weakness: …"` patterns at end of consequences string).
- Evidence: N6 above; analysis/14 backlog item "Consequences contamination repair validator."
- Risk: Low (repair, not reject).

**C4** — `activity_overview.json` thread-safety fix
- File: `track_activity.py:207–252` (per analysis/14 code_claude B1).
- Add a cross-plan thread-local guard to `_update_activity_overview`, matching the existing
  guard in `_record_file_usage_metric`.
- Evidence: analysis/14 NI3. Not introduced by any recent PR but still open.
- Risk: Low. Correctness fix.

---

## Summary

**Prompt_3 impact**: Confirmed to fix llama3.1's call-1 `review_lever` format failures for
silo and sovereign_identity. Run 1/10 shows both plans succeeding for the first time. This
validates the analysis/14 recommendation.

**Net success rate**: 32/35 (91.4%) — unchanged from analysis/14 because llama3.1 gained 1
success (+1) while gpt-5-nano lost 1 (−1, parasomnia `review_lever = 'Not applicable here'`).

**New failure mode**: gpt-5-nano produced `review_lever = 'Not applicable here'` for all
levers in a scientific/medical plan (parasomnia). This is a domain-specific compliance failure
that discards the entire response. A worked example using a non-business domain may help.

**Persistent issues**: qwen3-30b consequences contamination (~33% of levers in sampled run),
qwen3-30b option prefix violations (silo plan), gpt-oss-20b hong_kong_game JSON extraction
failure, and llama3.1 parasomnia ReadTimeout all remain unresolved.

**Recommended next action** (H1 supports proceeding): The prompt_3 fix is working. The
open items from analysis/14 backlog that require the least risk and highest leverage are:
(C1) `break` → `continue` for call-2 failures and (C3) consequences contamination repair
validator for qwen3.
