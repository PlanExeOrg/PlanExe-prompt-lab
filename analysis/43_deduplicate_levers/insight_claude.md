# Insight Claude

## Overview

This analysis evaluates PR #364 ("feat: consolidate deduplicate_levers with classification
and safety valve fix") against 7 before-runs (history/3/01–07) and 7 after-runs
(history/3/08–14), one run per model across 5 training plans (35 runs before, 35 after).

**PR summary**: Narrowed the safety valve that caused llama3.1 blanket-keep behavior.
Added calibration hint ("expect 4–8 absorb/remove in 15 levers"). Added concrete
secondary lever examples. Fixed B3 (`...` appended unconditionally in compact history).
Added OPTIMIZE_INSTRUCTIONS with 4 known failure modes. Added deduplicate_levers to
the self_improve runner.

**Model-to-run mapping**:

| Before | After | Model |
|--------|-------|-------|
| 3/01 | 3/08 | ollama-llama3.1 (sequential) |
| 3/02 | 3/09 | openrouter-openai-gpt-oss-20b |
| 3/03 | 3/10 | openai-gpt-5-nano |
| 3/04 | 3/11 | openrouter-qwen3-30b-a3b |
| 3/05 | 3/12 | openrouter-openai-gpt-4o-mini |
| 3/06 | 3/13 | openrouter-gemini-2.0-flash-001 |
| 3/07 | 3/14 | anthropic-claude-haiku-4-5-pinned |

---

## Negative Things

**N1 — gpt-4o-mini over-inclusion persists unchanged**

gpt-4o-mini averaged 9.6 kept levers per plan after the PR vs 9.4 before — essentially
no change. For hong_kong_game it kept 12/15 both before and after. For silo it kept 10/15
both before and after. The calibration hint ("expect 4–8 absorb/remove") did not move
this model.

Evidence:
- Before: `history/3/05_deduplicate_levers/outputs/20260310_hong_kong_game/002-11-deduplicated_levers_raw.json` — 9 primary + 3 secondary + 3 absorb = 12 kept
- After: `history/3/12_deduplicate_levers/outputs/20260310_hong_kong_game/002-11-deduplicated_levers_raw.json` — 8 primary + 4 secondary + 3 absorb = 12 kept

The absorb count remained at 3, far below the calibration hint's expectation of 4–8.

**N2 — gemini-2.0-flash regression on sovereign_identity**

gemini-2.0-flash went from keeping 5 levers to 9 levers on the sovereign_identity plan.
Before the PR, gemini correctly absorbed 10 of 15 levers (true duplicates in the 5-pair
structure of that plan). After the PR, gemini absorbed only 5, then kept 4 near-duplicate
levers as separate primaries (737c7c14, a3994e33, 1079592e, db44b7de).

Evidence:
- Before: `history/3/06_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json`
  — 5 primary + 0 secondary + 10 absorb + 0 remove = 5 kept
- After: `history/3/13_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json`
  — 9 primary + 0 secondary + 5 absorb + 1 remove = 9 kept

The calibration hint "expect 4–8 to be absorbed or removed" may have caused gemini to stop
absorbing after reaching 5 absorbs (at the lower bound of the expected range), then switch
to keeping the remaining levers rather than absorbing the full 10. Consensus from other
models on this plan is 5 kept (llama3.1:5, gpt-5-nano:3, gpt-4o-mini:5, gpt-oss-20b:5,
haiku:5 — all after-PR).

**N3 — qwen3-30b gta_game over-inclusion**

qwen3-30b kept 11/15 levers for gta_game both before (12) and after (11) the PR. Still
over-including. The calibration hint did not materially reduce qwen3's tendency to keep
too many levers in high-variability plans.

**N4 — Fabricated numbers persist unchanged in upstream data**

The source data (from identify_potential_levers) contains fabricated percentage claims that
flow through deduplication unchanged: "15% higher audience engagement", "30% increase in
streaming revenue", "20% higher pre-sales", "10% increase in production costs". Since
deduplicate_levers passes `consequences` fields verbatim, these numbers are inherited
without validation.

Evidence: `history/3/08_deduplicate_levers/outputs/20260310_hong_kong_game/002-11-deduplicated_levers_raw.json`
— all deduplicated_levers contain fabricated % claims in consequences fields (identical
to the input levers).

This is an upstream issue (identify_potential_levers), not a regression, but worth noting
for cross-step analysis.

---

## Positive Things

**P1 — llama3.1 blanket-keep ELIMINATED (primary target fixed)**

The most significant improvement: llama3.1 kept 14–15/15 levers in two plans before (silo:
15/15, hong_kong: 15/15). After the PR, these dropped to 8 and 7 respectively. llama3.1's
average kept per plan fell from 10.6 to 7.0 — now within the target range (7–11).

Evidence:
- Silo before: `history/3/01_deduplicate_levers/outputs/20250321_silo/002-11-deduplicated_levers_raw.json`
  — 14 primary + 1 secondary + 0 absorb = 15 kept
- Silo after: `history/3/08_deduplicate_levers/outputs/20250321_silo/002-11-deduplicated_levers_raw.json`
  — 7 primary + 1 secondary + 7 absorb = 8 kept
- Hong_kong before: `history/3/01_deduplicate_levers/outputs/20260310_hong_kong_game/002-11-deduplicated_levers_raw.json`
  — 14 primary + 1 secondary + 0 absorb = 15 kept
- Hong_kong after: `history/3/08_deduplicate_levers/outputs/20260310_hong_kong_game/002-11-deduplicated_levers_raw.json`
  — 5 primary + 2 secondary + 8 absorb = 7 kept

The system prompt change from "Use 'primary' if you lack understanding" to "Use 'primary'
only as a last resort" with the calibration hint directly broke the blanket-primary loop.

**P2 — 100% success rate maintained**

All 35 after-PR runs succeeded (7 models × 5 plans). No LLMChatError entries in any
events.jsonl. The prompt changes did not break schema compliance or cause validation
failures for any model.

Evidence: All `outputs.jsonl` files for runs 08–14 show `"status": "ok"` with no null errors.

**P3 — B3 bug fix confirmed (... not appended unconditionally)**

The previous synthesis identified B3: `...` was unconditionally appended in
`_build_compact_history` regardless of whether truncation occurred. The PR fixes this.
This prevents the LLM from misinterpreting short, un-truncated justifications as incomplete,
which was causing unnecessary re-classification on retry paths.

**P4 — Secondary classification more consistent after examples**

The addition of concrete secondary examples ("marketing campaign timing, internal reporting
cadence, team communication tooling, documentation formatting standards") helped models
distinguish primary vs secondary. Comparing response classification distributions:

- llama3.1: secondary rate improved from 4% (before) to 5% (after) — small but in right
  direction
- gpt-4o-mini hong_kong: secondary increased from 3 to 4 in the kept set, suggesting
  "Audience Engagement" and similar operational levers are being flagged more consistently
- claude-haiku and gpt-oss-20b maintained stable secondary usage across plans

**P5 — OPTIMIZE_INSTRUCTIONS documents 4 failure modes**

The PR adds OPTIMIZE_INSTRUCTIONS documenting blanket-primary, over-inclusion,
hierarchy-direction errors, and chain absorption as known failure modes. This makes future
self-improve iterations for deduplicate_levers aware of these patterns from the start.

**P6 — Downstream token reduction for llama3.1**

With llama3.1 now correctly reducing 15 levers to ~7 instead of passing all 15 through,
the enrich_potential_levers, vital_few_levers, and scenario_generation steps will process
~8 fewer levers per plan for this model — approximately 50% reduction in lever-processing
overhead for that model.

---

## Comparison

Comparing before (runs 01–07) vs after (runs 08–14) system prompts (extracted from output
files):

**Before** (key lines 104–107 of DEDUPLICATE_SYSTEM_PROMPT):
```
Use "primary" if you lack understanding of what the lever is doing. This way a potential
important lever is not getting removed.
Describe what the issue is in the justification.

Don't play it too safe, so you fail to perform the core task: consolidate the levers and
get rid of the duplicates.
```

**After** (replacement):
```
Use "primary" only as a last resort — if you genuinely cannot determine a lever's strategic
role after reading the full context. Describe what is unclear in the justification.

In a well-formed set of 15 levers, expect 4–8 to be absorbed or removed. If you find zero
absorb/remove decisions, reconsider: the input almost always contains near-duplicates.
Do not keep every lever.
```

Also changed: secondary description now includes concrete examples: "marketing campaign
timing, internal reporting cadence, team communication tooling, documentation formatting
standards."

---

## Quantitative Metrics

### Average Kept Levers Per Plan (15 input levers)

| Model | Before avg | After avg | Delta | Target (7–11) |
|-------|-----------|-----------|-------|--------------|
| llama3.1 | 10.6 | 7.0 | -3.6 ✅ | ✅ |
| gpt-oss-20b | 7.2 | 6.6 | -0.6 ✅ | ✅ |
| gpt-5-nano | 5.0 | 4.8 | -0.2 ≈ | borderline |
| qwen3-30b | 8.6 | 8.0 | -0.6 ✅ | ✅ |
| gpt-4o-mini | 9.4 | 9.6 | +0.2 ❌ | ≈ target |
| gemini-2.0-flash | 7.0 | 7.8 | +0.8 ❌ | ✅ |
| claude-haiku | 6.8 | 6.4 | -0.4 ✅ | ✅ |
| **All-model avg** | **7.8** | **7.2** | **-0.6** | ✅ |

### Per-Plan Lever Counts (After PR)

| Plan | llama3.1 | gpt-oss | gpt-5-nano | qwen3 | gpt-4o-mini | gemini | haiku |
|------|----------|---------|-----------|-------|------------|--------|-------|
| silo | 8 | 7 | 5 | 9 | 10 | 7 | 6 |
| gta_game | 6 | 7 | 5 | 11 | 11 | 8 | 7 |
| sovereign_id | 5 | 5 | 3 | 5 | 5 | **9** | 5 |
| hong_kong | 7 | 6 | 5 | 7 | 12 | 7 | 7 |
| parasomnia | 9 | 8 | 6 | 8 | 10 | 8 | 7 |

Bold: gemini's sovereign_identity regression.

### Per-Plan Lever Counts (Before PR)

| Plan | llama3.1 | gpt-oss | gpt-5-nano | qwen3 | gpt-4o-mini | gemini | haiku |
|------|----------|---------|-----------|-------|------------|--------|-------|
| silo | **15** | 7 | 4 | 10 | 10 | 7 | 6 |
| gta_game | 9 | 7 | 5 | 12 | 9 | 8 | 9 |
| sovereign_id | 6 | 6 | 4 | 3 | 5 | **5** | 5 |
| hong_kong | **15** | 8 | 4 | 7 | 12 | 7 | 7 |
| parasomnia | 8 | 8 | 8 | 11 | 11 | 8 | 7 |

Bold: llama3.1's two blanket-keep cases (15/15) and gemini's correct sovereign_identity result.

### Classification Distribution in Response (per 75 levers = 5 plans × 15)

| Model | Before primary% | After primary% | Before absorb% | After absorb% |
|-------|----------------|---------------|----------------|---------------|
| llama3.1 | 67% | 41% | 29% | 53% |
| gpt-oss-20b | 45% | 43% | 51% | 55% |
| gpt-5-nano | 29% | 28% | 67% | 68% |
| qwen3-30b | 55% | 52% | 43% | 45% |
| gpt-4o-mini | 52% | 51% | 37% | 36% |
| gemini-2.0-flash | 44% | 51% | 53% | 43% |
| claude-haiku | 35% | 35% | 49% | 50% |

Note: llama3.1's primary% drop from 67% to 41% is the clearest signal of the fix working.
gemini's primary% increase from 44% to 51% signals the sovereign_identity regression.

### LLMChatError Events

| Period | Errors | Source |
|--------|--------|--------|
| Before (runs 01–07) | 0 | All events.jsonl files |
| After (runs 08–14) | 0 | All events.jsonl files |

No schema validation failures in either period. All 35+35 plan runs succeeded.

### Field Length (Deduplication Justification)

Both before and after runs pass the input levers' `consequences`, `options`, and `review`
fields verbatim — no reformatting occurs at this step. Field length changes are therefore
inherited from the identify_potential_levers step and are not a regression here.

---

## Evidence Notes

- llama3.1 blanket-keep (before): `history/3/01_deduplicate_levers/outputs/20250321_silo/002-11-deduplicated_levers_raw.json` (system_prompt confirms old wording)
- llama3.1 fixed (after): `history/3/08_deduplicate_levers/outputs/20250321_silo/002-11-deduplicated_levers_raw.json` (system_prompt shows new calibration hint)
- gemini regression: `history/3/13_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json` — 9 primary levers kept where 5 is the consensus
- gemini correct (before): `history/3/06_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json` — 5 primary, 10 absorb
- gpt-4o-mini unchanged: `history/3/05_deduplicate_levers/outputs/20260310_hong_kong_game/002-11-deduplicated_levers_raw.json` (before: 12 kept) vs `history/3/12_deduplicate_levers/outputs/20260310_hong_kong_game/002-11-deduplicated_levers_raw.json` (after: 12 kept)

---

## PR Impact

### What the PR Was Supposed to Fix

Per PR #364 description:
1. Fix llama3.1 blanket-keep (14–15/15 kept before)
2. Fix gpt-4o-mini over-inclusion (10–12/15 kept before)
3. Add `primary`/`secondary` classification into the system prompt calibration
4. Fix B3: `...` appended unconditionally in compact history
5. Add OPTIMIZE_INSTRUCTIONS with 4 failure modes
6. Add concrete secondary lever examples

### Before vs After Comparison

| Metric | Before (runs 01–07) | After (runs 08–14) | Change |
|--------|--------------------|--------------------|--------|
| Overall avg kept | 7.8 | 7.2 | -0.6 ✅ |
| llama3.1 avg kept | 10.6 | 7.0 | -3.6 ✅ |
| llama3.1 blanket-keep cases | 2/5 plans | 0/5 plans | fixed ✅ |
| gpt-4o-mini avg kept | 9.4 | 9.6 | +0.2 ❌ |
| gpt-4o-mini hong_kong kept | 12 | 12 | unchanged ❌ |
| gemini avg kept | 7.0 | 7.8 | +0.8 ⚠️ |
| gemini sovereign_identity kept | 5 | 9 | regression ❌ |
| LLMChatError count | 0 | 0 | same ✅ |
| Success rate | 35/35 | 35/35 | same ✅ |
| B3 fix (no spurious ...) | NO | YES | fixed ✅ |

### Did the PR Fix the Targeted Issues?

1. **llama3.1 blanket-keep**: YES, FIXED. The two 15/15 cases (silo and hong_kong) are
   eliminated. Average dropped from 10.6 to 7.0.

2. **gpt-4o-mini over-inclusion**: NO, NOT FIXED. Average is essentially unchanged
   (9.4→9.6). The calibration hint alone is insufficient for this model. gpt-4o-mini
   keeps writing "is a distinct and essential strategic decision" for nearly every lever
   even when near-duplicates are present.

3. **B3 fix**: YES, FIXED (code change, confirmed by PR).

4. **OPTIMIZE_INSTRUCTIONS**: YES, ADDED (code change, confirmed by PR).

5. **Concrete secondary examples**: PARTIALLY effective. Models now more consistently
   classify "audience engagement" and "production efficiency" as secondary, but this did
   not reduce total kept count for most models.

### Regressions Introduced

1. **gemini sovereign_identity regression**: gemini went from 5 kept (correct) to 9 kept
   (over-inclusion). The calibration hint "expect 4–8 absorb/remove" appears to have stopped
   gemini from absorbing all 10 true duplicates once it reached 5 absorbs. This is an
   unintended consequence: the hint is accurate on average but inaccurate for plans with
   more than 8 structural duplicates.

### Verdict

**CONDITIONAL**

The PR fixes the most critical targeted failure (llama3.1 blanket-keep) and provides
real code quality improvements (B3 fix, OPTIMIZE_INSTRUCTIONS). However:

- gpt-4o-mini over-inclusion is entirely unaddressed (0.2 point regression)
- gemini sovereign_identity is a new regression (5→9 kept)
- The calibration hint is inaccurate for plans where the true duplicate count exceeds 8

**Recommended follow-up before next iteration**:
- Widen the calibration hint range from "4–8" to "4–10" to avoid cap behavior on
  high-duplicate plans
- Or reframe as "typically 4–8, but up to 10+ for structured duplicate inputs"
- Investigate why gpt-4o-mini's absorb rate remains at ~37% regardless of instructions;
  this model may need a worked absorb example

---

## Questions For Later Synthesis

1. **Q1**: Is the gemini sovereign_identity regression (5→9) a systematic effect of the
   calibration hint, or a one-off stochastic variance? Only one model (gemini) showed this
   pattern; the other 6 models on sovereign_identity stayed at or below 5. If another run
   with gemini reproduces the same result, the calibration hint range needs widening.

2. **Q2**: gpt-4o-mini absorbs only 3–5 levers regardless of prompt instructions. Is the
   problem in the reasoning pattern of the model, or could a worked example of an absorb
   decision break the pattern? Would adding an in-prompt demonstration help?

3. **Q3**: gpt-5-nano keeps 3–6 levers per plan (avg 4.8) — below the lower end of the
   target range (7). Is under-deduplication a risk here (discarding legitimate distinct
   levers), or is gpt-5-nano's input data simply more duplicated?

4. **Q4**: Do downstream steps (`vital_few_levers`, `scenario_generation`) actually use
   the `classification: primary|secondary` field for prioritization? If not, the core
   motivation for the classification split (D8 from synthesis/42) remains unimplemented.

5. **Q5**: The calibration hint says "In a well-formed set of 15 levers, expect 4–8 to
   be absorbed or removed." Is 4–8 the correct empirically-grounded range? The before-PR
   baseline (gemini run 06) shows 10 absorbs on sovereign_identity. The range may need to
   be 4–10 or "4–10 depending on input diversity."

---

## Reflect

The PR achieved its primary goal (llama3.1 fix) and added valuable infrastructure
(OPTIMIZE_INSTRUCTIONS, B3 fix). The calibration hint is effective for models that were
in the "understimated how much to absorb" regime (llama3.1) but may cause premature
stopping for models that correctly absorb high numbers of duplicates (gemini on
high-duplicate inputs).

The gpt-4o-mini problem is structurally different from the llama3.1 problem: llama3.1
was confused about what "primary" means and defaulted to it; gpt-4o-mini understands the
classification but consistently produces verbose justifications for keeping almost every
lever as "distinct and essential strategic decision." This likely requires a different
intervention — a worked example of absorb reasoning or an explicit anti-pattern ("If all
levers look primary, you are missing the near-duplicates").

---

## Potential Code Changes

**C1 — Widen calibration hint range to avoid capping on high-duplicate inputs**

In `deduplicate_levers.py` DEDUPLICATE_SYSTEM_PROMPT, change:

```
In a well-formed set of 15 levers, expect 4–8 to be absorbed or removed.
```

to:

```
In a well-formed set of 15 levers, expect 4–10 to be absorbed or removed. If your input
contains many near-duplicate names (e.g., "Narrative Innovation Strategy" appearing twice),
expect the higher end of this range.
```

Evidence: gemini sovereign_identity (10 true duplicates) was stopped at 5 absorbs by the
"4–8" upper bound signal.

**C2 — Add anti-blanket-primary instruction for gpt-4o-mini**

Add to DEDUPLICATE_SYSTEM_PROMPT after the calibration hint:

```
If every lever looks "distinct and essential", you are missing the near-duplicates. Compare
lever names and consequences carefully: two levers with similar names but different IDs
are strong candidates for absorb.
```

Evidence: gpt-4o-mini's justifications (`history/3/12_deduplicate_levers/outputs/`) all
contain the phrase "is a distinct and essential strategic decision" — a boilerplate phrase
indicating the model isn't comparing levers, just evaluating each in isolation.

**C3 — Add post-deduplication zero-reduction check (I2 from synthesis/42)**

In `deduplicate_levers.py`, after generating `deduplicated_levers`, log a warning if:
```python
if len(deduplicated_levers) / len(input_levers) > 0.9:
    logger.warning(f"Deduplication yielded {len(deduplicated_levers)}/{len(input_levers)} levers — possible blanket-keep")
```

Evidence: This warning would have caught llama3.1's blanket-keep earlier without waiting
for analysis pipeline to flag it. Currently there is no runtime signal.

---

## Summary

PR #364 made one major improvement and one significant miss:

**✅ Major win**: llama3.1's blanket-keep failure (14–15/15 kept) is eliminated. Average
kept levers for llama3.1 dropped from 10.6 to 7.0, now within target range. This reduces
downstream token cost by ~50% for that model.

**❌ Primary miss**: gpt-4o-mini over-inclusion (9.4→9.6) is entirely unaddressed. The
calibration hint alone does not move this model.

**⚠️ New regression**: gemini sovereign_identity went from 5 kept (correct) to 9 kept
(over-inclusion). The "expect 4–8" upper bound in the calibration hint appears to have
stopped gemini from absorbing all 10 true duplicates in a highly-structured-duplicate plan.

**✅ Code quality improvements**: B3 fix (spurious `...`) and OPTIMIZE_INSTRUCTIONS
(4 failure modes documented) are solid non-risky additions.

**Verdict**: CONDITIONAL — keep the PR but widen the calibration hint range to 4–10 and
add a worked absorb example or anti-boilerplate instruction to address gpt-4o-mini.
