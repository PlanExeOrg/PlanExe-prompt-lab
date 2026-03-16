# Insight Claude

## Negative Things

### N1 — `check_review_format` causes cascade failures for llama3.1 (systematic)

Run 95 (llama3.1, workers=1): two of five plans failed entirely due to the new `check_review_format`
validator.

- `20250321_silo`: 9 review_format violations — `90.47 s` then `LLMChatError`. Error log shows all 9
  levers failing: alternating between "Controls X vs. Y." (has Controls, missing Weakness) and
  "Weakness: The options fa..." (has Weakness, missing Controls). No lever has both components.
  (`history/0/95_identify_potential_levers/events.jsonl`, error entry at timestamp
  `2026-03-16T00:38:31Z`)
- `20250329_gta_game`: 8 review_format violations — same alternating pattern, `32.69 s` then
  `LLMChatError`. (`history/0/95_identify_potential_levers/events.jsonl`, error entry at timestamp
  `2026-03-16T00:39:04Z`)

This is a **systematic** llama3.1 behavior: the model treats `review_lever` as two separate
fields (Controls phrase OR Weakness phrase) and never combines them. Before the PR, these levers
silently passed; now they correctly fail, but the call-level rejection discards all levers in the
call, leaving 0 output for those plans.

### N2 — `check_option_count` causes cascade failure for haiku

Run 1/01 (haiku): `20250321_silo` failed after 154.98 s.

Error: `levers.7.options Value error, options must have exactly 3 items, got 7
[input_value=['Assign residents to pri...wed. Removing Lever 8.']]`
(`history/1/01_identify_potential_levers/events.jsonl`, `2026-03-16T01:02:52Z`)

The trailing text "Removing Lever 8." in the options list indicates the model was embedding
self-corrective editorial commentary inside the JSON `options` array, producing a 7-element list.
The validator correctly caught this, but the call-level rejection discarded the other 18+ valid
levers from the same DocumentDetails call.

Before this PR, haiku was 5/5 for run 94. Now 4/5.

### N3 — Call-level rejection cascade (B2 bug still in place)

As predicted in `analysis/12_identify_potential_levers/assessment.md` (Risks section): the current
Pydantic structure validates `DocumentDetails` as a unit. A single lever failing either validator
causes the entire `DocumentDetails.levers` list to fail, raising `LLMChatError` and discarding all
levers from that call. Direction 2 (partial result recovery) was not implemented alongside PR #289.

Evidence: Run 95 silo outputs directory contains only `activity_overview.json` and
`usage_metrics.jsonl` — no `002-10-potential_levers.json` file — despite the model generating 9
levers before failing. (`history/0/95_identify_potential_levers/outputs/20250321_silo/`)

### N4 — gpt-oss-20b failure pattern shifted (unrelated to PR)

- Before (run 90): `20260308_sovereign_identity` fails with `Could not extract json string from
  output` at 164 s.
- After (run 96): `20260311_parasomnia_research_unit` fails with
  `Invalid JSON: EOF while parsing a list at line 36 column 5` at 34.85 s.

Different plans, different error classes. The prior failure (sovereign_identity JSON extraction
failure) appears resolved or intermittent, while a new truncation failure appeared on parasomnia.
Neither failure is related to PR #289's validators. (`history/0/96_identify_potential_levers/events.jsonl`)

### N5 — qwen3 consequence contamination persists

Run 98 (qwen3), `20250321_silo`, first lever:
`consequences` field ends with: `"...Controls Order vs. Adaptability. Weakness: The options fail to consider psychological burnout from perpetual surveillance."` —
identical text also appears in `review` for the same lever.
(`history/0/98_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:5,11`)

The `check_review_format` validator does not check `consequences`, so contamination still passes
silently. Orthogonal to PR #289.

---

## Positive Things

### P1 — Both validators are functioning correctly

`check_option_count` caught haiku run 1/01 lever 7 with 7 options instead of 3 — a real violation
that would have propagated to downstream tasks.

`check_review_format` caught llama3.1's systematic failure to include both `Controls` and
`Weakness:` markers — 17 violations across 2 plans (9 in silo + 8 in gta_game) that previously
shipped silently.

Before PR #289, run 89 (llama3.1) wrote 3 levers with 2 options and 4+3 review-format violations
to the final `002-10-potential_levers.json` artifact. No such malformed levers exist in any
successful after-PR run.

### P2 — No silently malformed levers in passing runs

All seven plans that succeed in runs 96–1/01 (excluding the two validator-rejected plans in run 95
and one in 1/01) contain exactly 3 options per lever and properly formatted `review_lever` fields
with both `Controls` and `Weakness:` components. The contract is enforced for every shipped artifact.

### P3 — gemini-2.0-flash added to test matrix, performs well

Runs 99 and 1/00 (gemini-2.0-flash): 5/5 both times. No validation failures. Good-quality
review_lever fields ("Controls X vs. Y. Weakness: ...") and correctly-sized option lists.
(`history/0/99_identify_potential_levers/` and `history/1/00_identify_potential_levers/`)

The second gemini run (1/00) was notably faster: 29–37 s per plan vs. 56–65 s in run 99, possibly
due to API caching or warm infrastructure.

### P4 — Validator failures are faster than model timeouts

Validator-triggered failures complete in 33–90 s vs. prior model timeout failures at 90–184 s.
Pydantic validation at parse time is much cheaper than waiting for full generation timeouts.
Run 95 gta_game failed in 32.69 s; run 95 silo failed in 90.47 s.

### P5 — Overall success rate nominally improved

28/35 (80.0%) before → 31/35 (88.6%) after. However, this reflects a model lineup change
(nemotron 0/5 replaced by gemini-2.0-flash 5/5 twice) and must be interpreted carefully.
See Comparison section.

---

## Comparison

### Per-run summary

| Run | Model | Plans | OK | Errors | Error causes |
|-----|-------|------|----|--------|-------------|
| 88 | nemotron | 5 | 0 | 5 | JSON extraction fail (all) |
| 89 | llama3.1 | 5 | 4 | 1 | ReadTimeout — sovereign_identity |
| 90 | gpt-oss-20b | 5 | 4 | 1 | JSON extraction — sovereign_identity |
| 91 | gpt-5-nano | 5 | 5 | 0 | — |
| 92 | qwen3 | 5 | 5 | 0 | — |
| 93 | gpt-4o-mini | 5 | 5 | 0 | — |
| 94 | haiku | 5 | 5 | 0 | — |
| **Before total** | | **35** | **28** | **7** | |
| 95 | llama3.1 | 5 | 3 | 2 | `check_review_format` — silo (9 violations), gta_game (8 violations) |
| 96 | gpt-oss-20b | 5 | 4 | 1 | JSON truncation — parasomnia |
| 97 | gpt-5-nano | 5 | 5 | 0 | — |
| 98 | qwen3 | 5 | 5 | 0 | — |
| 99 | gemini-2.0-flash | 5 | 5 | 0 | — |
| 1/00 | gemini-2.0-flash | 5 | 5 | 0 | — |
| 1/01 | haiku | 5 | 4 | 1 | `check_option_count` — silo (lever 7: 7 options) |
| **After total** | | **35** | **31** | **4** | |

### Shared-model comparison (models present in both periods)

Models in common: llama3.1, gpt-oss-20b, gpt-5-nano, qwen3, haiku (nemotron and gpt-4o-mini
removed; gemini-2.0-flash added).

| Model | Before (single run) | After (single run) | Change | Cause |
|-------|--------------------|--------------------|--------|-------|
| llama3.1 | 4/5 | 3/5 | −1 | `check_review_format` rejection (new) |
| gpt-oss-20b | 4/5 | 4/5 | 0 | Different plan fails (unrelated to PR) |
| gpt-5-nano | 5/5 | 5/5 | 0 | — |
| qwen3 | 5/5 | 5/5 | 0 | — |
| haiku | 5/5 | 4/5 | −1 | `check_option_count` rejection (new) |
| **Subtotal** | **23/25 = 92%** | **21/25 = 84%** | **−2** | Both regressions are validator working correctly |

The shared-model success rate regressed from 92% to 84%. However, both regressions represent
the validators catching genuine violations that previously shipped silently — they are correctness
improvements in terms of data integrity, expressed as plan-level failures due to the B2 cascade bug.

---

## Quantitative Metrics

### Success rate

| Period | Runs | Plans | OK | Errors | Rate |
|--------|------|------|----|--------|------|
| Before (88–94) | 7 | 35 | 28 | 7 | 80.0% |
| After (95–1/01) | 7 | 35 | 31 | 4 | 88.6% |

*Inflated by nemotron→gemini swap. Shared-model rate: 92% → 84%.*

### Validator rejection counts

| Validator | Before runs | After runs | Change |
|-----------|-------------|------------|--------|
| `check_option_count` rejections in successful artifacts | 3 (run 89, silently shipped) | 0 in artifacts; 1 plan failed | Fixed + new cascade failure |
| `check_review_format` rejections in successful artifacts | 4+3=7 (run 89, silently shipped) | 0 in artifacts; 2 plans failed | Fixed + new cascade failures |
| Plans failing due to validators | 0 | 3 (run 95: silo, gta_game; run 1/01: silo) | +3 (validators working) |
| Plans silently shipping malformed levers | ≥1 (run 89 hong_kong_game) | 0 | Fixed |

### Failure mode breakdown

| Failure mode | Before (88–94) | After (95–1/01) |
|---|---|---|
| Model structurally incapable (nemotron 0/5) | 5 | 0 (removed) |
| Timeout / ReadTimeout | 1 (run 89, sovereign_identity) | 0 |
| JSON extraction fail | 2 (runs 88 all; run 90 sovereign_identity) | 0 |
| JSON truncation (gpt-oss-20b) | 0 | 1 (run 96, parasomnia) |
| `check_review_format` cascade | 0 | 2 (run 95: silo, gta_game) |
| `check_option_count` cascade | 0 | 1 (run 1/01, silo) |

### Average run duration for successful plans (seconds)

| Run | Model | Avg duration (ok plans) |
|-----|-------|------------------------|
| 89 | llama3.1 | 107.8 |
| 94 | haiku | 254.4 |
| 95 | llama3.1 | 131.7 (3 ok plans) |
| 97 | gpt-5-nano | 183.1 |
| 98 | qwen3 | 110.1 |
| 99 | gemini-2.0-flash | 61.2 |
| 1/00 | gemini-2.0-flash | 32.5 |
| 1/01 | haiku | 308.4 (4 ok plans) |

---

## Evidence Notes

1. **Run 95 silo (llama3.1) review_lever errors** — the 9 review_lever fields alternate between
   Controls-only and Weakness-only formats; no lever contains both components simultaneously.
   `history/0/95_identify_potential_levers/events.jsonl`, validator error at `2026-03-16T00:38:31Z`.

2. **Run 95 silo no output files** — `history/0/95_identify_potential_levers/outputs/20250321_silo/`
   contains only `activity_overview.json` and `usage_metrics.jsonl`. The rejection cascade discards
   all generated levers.

3. **Run 1/01 haiku silo error** — `levers.7.options: options must have exactly 3 items, got 7`,
   with options value containing `"Removing Lever 8."` — model embedded editorial commentary in
   options list. `history/1/01_identify_potential_levers/events.jsonl`, `2026-03-16T01:02:52Z`.

4. **Run 1/01 haiku gta_game success** — `002-10-potential_levers.json` shows high-quality levers
   with specific percentages and trade-offs, review_lever fields correctly formatted with both
   Controls and Weakness components.
   `history/1/01_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`

5. **Run 98 qwen3 consequence contamination** — lever 0 (silo): consequences field ends with
   `"Controls Order vs. Adaptability. Weakness: ..."`, identical to the review field.
   `history/0/98_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json:5,11`

6. **Run 97 gpt-5-nano silo output** — 19 levers, all with 3 options and properly formatted
   `review` fields, measurable consequences. Good quality throughout.
   `history/0/97_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`

7. **Run 1/00 gemini-2.0-flash silo output** — review_lever format: "Controls Security vs.
   Adaptability. Weakness: The options fail to consider..."  — both components present, format
   compliant. `history/1/00_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`

8. **Baseline comparison from run 99 (gemini)** — levers follow the expected structure, no
   template placeholders, option spectrum from conservative to radical present throughout.

---

## PR Impact

### What the PR was supposed to fix

PR #289 added two validators to the `Lever` Pydantic model (as recommended by analysis/12
synthesis, Direction 1):

1. `check_option_count`: reject levers where `len(options) != 3`
2. `check_review_format`: reject `review_lever` fields missing `Controls` and/or `Weakness:` markers

These were identified after run 89 produced 3 levers with 2 options and 4+3 review-format
violations that silently shipped to downstream tasks.

### Before vs after comparison

| Metric | Before (runs 88–94) | After (runs 95–1/01) | Change |
|--------|---------------------|----------------------|--------|
| Overall success rate | 28/35 (80.0%) | 31/35 (88.6%) | +8.6% (model swap effect) |
| Shared-model success rate | 23/25 (92.0%) | 21/25 (84.0%) | −8.0% (validators working) |
| Plans silently shipping malformed levers | ≥1 | 0 | **Fixed** |
| `check_option_count` violations in artifacts | 3 (run 89) | 0 | **Fixed** |
| `check_review_format` violations in artifacts | 7 (run 89) | 0 | **Fixed** |
| Plan failures caused by validators | 0 | 3 | +3 (intended effect, B2 cascade) |
| llama3.1 success | 4/5 | 3/5 | −1 (systematic non-compliance caught) |
| haiku success | 5/5 | 4/5 | −1 (option count edge case caught) |
| gpt-oss-20b success | 4/5 | 4/5 | Unchanged (different plan fails, unrelated) |
| gpt-5-nano success | 5/5 | 5/5 | Unchanged |
| qwen3 success | 5/5 | 5/5 | Unchanged |
| qwen3 consequence contamination | ~70% | ~70% | Unchanged (orthogonal to PR) |
| New model: gemini-2.0-flash | not in matrix | 5/5 + 5/5 | New; performing well |
| Validator-caused failures (faster feedback) | 0 | 3 fails at 32–90s vs prior 90–184s timeouts | Faster fail |

### Did the PR fix the targeted issues?

**Yes, completely.**

- No lever with != 3 options appears in any post-PR successful artifact.
- No lever with missing `Controls` or `Weakness:` markers appears in any post-PR successful artifact.
- The validators fire correctly in every case tested:
  - `check_option_count` caught haiku run 1/01 lever 7 (7 options)
  - `check_review_format` caught llama3.1 run 95 silo (9 violations) and gta_game (8 violations)

### Did the PR cause regressions?

**Yes — predicted, but worse than expected for llama3.1.**

The analysis/12 assessment.md explicitly warned of call-level rejection cascade risk and recommended
implementing Direction 2 (partial result recovery) at the same time. This was not done.

The cascade is worse for llama3.1 than expected: the model produces **zero** compliant review_lever
fields per call — every lever has either Controls or Weakness but not both. This means the entire
call fails, not just a fraction. Two previously-passing plans (silo, gta_game) now produce no
output.

For haiku, the cascade effect is less severe — a single lever (lever 7) with 7 options caused a
single plan failure, losing ~18 other valid levers from the call.

### Verdict

**CONDITIONAL**

The validators are correct, necessary, and working exactly as designed. Data integrity is improved:
no malformed levers ship to downstream tasks. However, the call-level rejection cascade — caused
by the pre-existing B2 partial-result-loss bug — is creating more plan failures than acceptable,
particularly for llama3.1 which has systematic `review_lever` format compliance issues.

The PR should be kept (the validators are correct) but Direction 2 (partial result recovery) is
urgently needed to prevent total call failures from propagating as total plan failures.

---

## Questions For Later Synthesis

**Q1**: Is llama3.1's `review_lever` format failure systematic across all plans, or only for
certain plan types? Run 95 shows 0% compliance in silo and gta_game. Is this model simply
incapable of producing the combined "Controls X vs. Y. Weakness: ..." format, or is it a prompt
clarity issue?

**Q2**: Does the haiku lever-7 option-count failure (7 options, including "Removing Lever 8." as
one option) represent a new failure mode where the model embeds editorial corrections inside JSON
arrays? Is this specific to a particular prompt structure or plan type?

**Q3**: Is Direction 2 (partial result recovery) the highest priority fix now that Direction 1 is
deployed? A plan that would have shipped 3 malformed levers now ships 0. Is 0 levers better or
worse than 3 malformed levers (which downstream could filter)?

**Q4**: Should the `check_review_format` validator be model-aware — e.g., reduced to a warning
rather than an error for models with systematically low compliance? Or should the fix be to repair
llama3.1 compliance via prompt changes?

**Q5**: gpt-oss-20b's failure shifted from sovereign_identity (JSON extraction) to parasomnia
(JSON truncation). Is this random variance or is parasomnia now the plan that exceeds this model's
effective structured-output context window?

**Q6**: gemini-2.0-flash appeared twice in the after runs (99 and 1/00) and shows a large
duration variance (32 s vs 62 s per plan). Is the fast run the result of API caching? Should
duplicate model runs be treated as a single data point?

---

## Reflect

The PR validates the synthesis/12 Direction 1 recommendation completely. Both validators fire
on real violations and produce no false positives in the after runs. The data integrity goal
is achieved: no malformed levers reach downstream tasks.

The problem is that "no malformed levers" now sometimes means "no levers at all" for llama3.1.
This reveals something deeper: llama3.1's `review_lever` format compliance is near zero, not
borderline. The model consistently produces either "Controls X vs. Y." or "Weakness: ..." as
separate independent values, suggesting it may be parsing the format as two separate fields rather
than one combined string with two required components. This is a model-specific behavior that the
prompt does not currently address with sufficient clarity for smaller models.

The haiku failure is more nuanced — a 7-option lever is clearly a model artifact (self-correction
embedded in JSON), not a prompt compliance failure. The validator correctly flags it, but the
business trade-off (discard 18+ valid levers to eliminate 1 malformed one) is questionable without
Direction 2 in place.

Overall: the PR moved the system in the right direction but is incomplete without partial result
recovery.

---

## Hypotheses

**H1 — llama3.1 review_lever format confusion**: The model treats "Controls [A] vs. [B]." and
"Weakness: ..." as two separate format options rather than two required clauses in one field.
A prompt change that provides an explicit single-field example with both components (e.g., "Must
be exactly: 'Controls [Tension A] vs. [Tension B]. Weakness: [analysis].'") may improve compliance
for smaller models without affecting larger models. Evidence: run 95 shows 100% alternating pattern
— every lever has one clause, never both.

**H2 — haiku editorial commentary in JSON**: The model occasionally embeds self-corrective
commentary (like "Removing Lever 8.") in structured fields when generating long responses. This
appears to be a haiku-specific tendency under long multi-lever generation. May be reduced by a
stronger prompt instruction prohibiting meta-commentary within JSON fields. Evidence: run 1/01
silo lever 7 options list contains "Removing Lever 8." as one of 7 items.

---

## Potential Code Changes

**C1 — Direction 2: Partial result recovery (HIGH PRIORITY)**

The B2 partial-result-loss bug (`identify_potential_levers.py:231–240`, identified in
analysis/12) discards all previously collected `DocumentDetails` objects when a later LLM call
raises `LLMChatError`. With validators now rejecting calls more frequently (for llama3.1,
systematically), this bug causes total plan failures from single call failures.

Fix: change the exception handler in the 3-call loop to `logger.warning` + `break` when
`len(responses) >= 1`, rather than re-raising the exception. Return the partial result with a
metadata flag indicating partial completion. This is the synthesis/12 Direction 2 recommendation,
which was explicitly noted as a prerequisite companion to Direction 1 in the assessment.

**C2 — Consider lever-level rather than call-level rejection**

Currently Pydantic validates `DocumentDetails.levers` as a list. A single lever failing a validator
fails the entire list. An alternative architecture would validate levers individually (e.g., by
parsing each lever independently and collecting the valid ones) before building the `DocumentDetails`
object. This would allow "accept 6 of 7 levers" rather than "accept 0 of 7 levers" on a single
bad lever.

This is a larger refactor than C1 and should be considered after C1 is implemented and the failure
patterns are re-analyzed.

**C3 — Add overflow telemetry (still missing)**

The synthesis/12 Direction 3 recommendation (log a warning when a raw call returns >7 levers) was
not included in PR #289. After removing `max_length=7`, overflow is still invisible. Very low
effort; recommend adding to the next PR.

---

## Summary

PR #289 adds `check_option_count` and `check_review_format` validators to the `Lever` Pydantic
model. Both validators are functioning correctly:

- `check_review_format` caught llama3.1's systematic failure to combine both `Controls` and
  `Weakness:` markers in a single `review_lever` field (17 violations across 2 plans in run 95).
- `check_option_count` caught a haiku edge case where lever 7 had 7 options including editorial
  commentary (run 1/01 silo).

No malformed levers appear in any post-PR successful artifact. Data integrity is improved.

However, the B2 partial-result-loss bug (call-level rejection cascade) remains unaddressed.
When a validator rejects any lever, the entire DocumentDetails parse fails and all levers from
that LLM call are discarded. For llama3.1, which has near-zero compliance with the combined
review_lever format, this causes complete plan failures: silo and gta_game in run 95 now produce
zero output instead of output with format violations.

Shared-model success rate: 92% before → 84% after (both regressions are validators working
correctly, not unrelated failures).

**Verdict: CONDITIONAL.** Keep the validators; implement Direction 2 (partial result recovery)
urgently. The validators are correct and the contract enforcement is necessary, but deploying
Direction 1 without Direction 2 converts "malformed output" into "no output" — acceptable only
temporarily.
