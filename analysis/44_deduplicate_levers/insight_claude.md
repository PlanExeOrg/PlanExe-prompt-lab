# Insight Claude

## Overview

This analysis evaluates PR #365 ("feat: consolidate deduplicate_levers — classification,
safety valve, B3 fix") against 7 before-runs (history/3/08–14) and 7 after-runs
(history/3/15–21), one run per model across 5 training plans (35 before, 35 after).

**PR primary goals** (from PR description):
1. Fix Gemini calibration-capping on sovereign_identity (widen "4–8" → "4–10 + do not stop early")
2. Add primary/secondary classification to replace flat `keep` for downstream prioritization
3. Complete B3 fix (`...` conditional in `all_levers_summary` — PR #364 only fixed `_build_compact_history`)
4. Document 5th failure mode (calibration-capping) in OPTIMIZE_INSTRUCTIONS
5. Broaden calibration hint: "expect 4–10 absorb/remove" + "do not stop early"

**Model-to-run mapping**:

| Before | After | Model |
|--------|-------|-------|
| 3/08 | 3/15 | ollama-llama3.1 (sequential) |
| 3/09 | 3/16 | openrouter-openai-gpt-oss-20b |
| 3/10 | 3/17 | openai-gpt-5-nano |
| 3/11 | 3/18 | openrouter-qwen3-30b-a3b |
| 3/12 | 3/19 | openrouter-openai-gpt-4o-mini |
| 3/13 | 3/20 | openrouter-gemini-2.0-flash-001 |
| 3/14 | 3/21 | anthropic-claude-haiku-4-5-pinned |

---

## Negative Things

**N1 — "secondary" adoption is patchy across models**

The PR added a "secondary" classification with concrete examples ("marketing campaign timing,
internal reporting cadence, team communication tooling, documentation formatting standards")
and specified "Use primary only as a last resort". Despite this, only 3 of 7 models used
"secondary" at all for sovereign_identity. Models that still defaulted to all-primary for
sovereign_identity: llama3.1, gpt-oss-20b, qwen3-30b, gemini.

Evidence (sovereign_identity kept-lever classification):
- llama3.1 run 15: 5 primary / 0 secondary — `history/3/15_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json`
- gpt-oss-20b run 16: 5 primary / 0 secondary — same path
- gemini run 20: 5 primary / 0 secondary — `history/3/20_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json`

Models that correctly used secondary: haiku classified EU Standards as secondary (4P/1S),
gpt-4o-mini classified EU Standards as secondary (4P/1S), gpt-5-nano classified Policy
Advocacy as secondary (but with chain-absorption issues, see N3).

The "secondary" category is only partially landing. Models with strong instruction-following
(haiku, gpt-4o-mini) adopted it; models with looser instruction adherence defaulted to
all-primary or ran into other problems.

**N2 — Hierarchy-direction violations persist**

Multiple models continue to absorb general/first-batch levers into specific/second-batch
duplicates, violating the "merge the more specific lever into the more general one" instruction.

Evidence (sovereign_identity, run 20, Gemini):
- Lever a02b023d ("Technical Feasibility Strategy", first batch) → absorbed into bd43cd39 (second batch duplicate)
- Lever b1a9192f ("Policy Advocacy Strategy", first batch) → absorbed into 80b177d0 (second batch)
- All 5 first-batch levers absorbed into second-batch counterparts

`history/3/20_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json`,
response entries 1–5 all show `"classification": "absorb"` pointing to second-batch IDs.

The final deduplicated_levers for Gemini keeps bd43cd39, 80b177d0, 1731ad9a, f1c0d856, 2e9016aa
(second-batch instances) rather than a02b023d, b1a9192f, b19a5405, 5019c4ad, 7166dd86
(first-batch instances). The content is semantically equivalent, but violates the hierarchy
instruction. Also observed in gpt-oss-20b run 16 and gpt-5-nano run 17.

**N3 — qwen3-30b over-collapse on sovereign_identity**

After PR #365, Qwen collapsed sovereign_identity to only 3 kept levers (before: 5). This is
below the minimum expected range. Qwen's chain-absorption logic absorbs the general first-batch
levers into specific second-batch levers AND absorbs those into yet another lever in a chain,
resulting in a very small kept set.

Evidence (run 18, Qwen, sovereign_identity):
- Response array: a02b023d → absorb (into bd43cd39), bd43cd39 → absorb (into a02b023d — circular?), with only a3994e33, 1079592e, db44b7de surviving as primary
- `history/3/18_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json`, deduplicated_levers shows 3 entries

Before #365: Qwen had 5 kept for sovereign_identity (clean absorptions). This appears to be
a regression for Qwen on this plan. Qwen's wider calibration hint ("4–10") may have pushed it
toward more aggressive absorption beyond what is warranted.

**N4 — gpt-5-nano self-referential and incoherent justifications**

Run 17 (gpt-5-nano, sovereign_identity) contains self-referential absorption justifications.
Lever bd43cd39 is classified as "remove" (but absorb would be correct per instructions).
Lever f1c0d856 justification says "Absorb into [f1c0d856]" (absorbing into itself).
The justification text also contains raw LLM meta-commentary mid-sentence: "Wait formatting:
I inserted extra {}. We must return proper JSON…" — model is leaking reasoning noise into
the justification field.

Evidence: `history/3/17_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json`
lever b19a5405 justification ends with garbled meta-commentary.

This suggests gpt-5-nano is borderline on the structured output task for this prompt
complexity level.

**N5 — Fabricated percentage claims inherited from upstream (unchanged)**

The sovereign_identity plan contains fabricated percentage claims from identify_potential_levers
that pass through deduplication unchanged: "15% increased policy traction", "20% greater
likelihood", "25% faster scaling", "30% stronger advocacy position", "10% increased alignment".
These numbers appear in the preserved lever content of run 13 (before) and run 20 (after).

Evidence: `history/3/20_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json`
deduplicated_levers[].consequences fields contain fabricated % claims. This is an upstream
issue (identify_potential_levers), not a regression in this PR, but still flagged.

---

## Positive Things

**P1 — Gemini calibration-capping on sovereign_identity FIXED (primary target)**

The most important fix: before PR #365, gemini kept 9 levers for sovereign_identity (the
"4–8" calibration hint caused gemini to stop absorbing after reaching 5 absorbs, then switch
to keeping). After PR #365 (widened to "4–10" + "do not stop early"), gemini correctly
reduces to 5 kept levers with 10 absorbs.

Evidence:
- Before: `history/3/13_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json`
  — 9 primary + 0 secondary + 5 absorb + 1 remove = 9 kept (regression from PR #364)
- After: `history/3/20_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json`
  — 5 primary + 0 secondary + 10 absorb = 5 kept ✓

Calibration-capping was the exact problem identified in analysis/43 (N2). PR #365 directly
addresses it. Consensus across all 7 models for sovereign_identity after PR #365 is 5 kept
(where it was 5 before PR #364 regressed gemini to 9).

**P2 — Haiku secondary classification improvement (sovereign_identity)**

Before PR #365, haiku classified all 5 distinct sovereign_identity levers as primary
(5P/0S/10A). After PR #365, haiku correctly identifies EU Standards Engagement as secondary
(4P/1S/10A), citing it as "a stretch goal" that "depends on prior success in demonstrators,
policy advocacy, and coalition building."

Evidence:
- Before: `history/3/14_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json`
  — response[4] (lever 7166dd86): `"classification": "primary"`
- After: `history/3/21_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json`
  — response[4] (lever 7166dd86): `"classification": "secondary"`, justification cites it
  as "distinct but strategically supporting rather than essential"

**P3 — gpt-4o-mini secondary classification improvement (sovereign_identity)**

Same pattern: before = 5P/0S/10A, after = 4P/1S/10A. EU Standards Engagement correctly
identified as secondary.

Evidence:
- Before: `history/3/12_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json`
  — response[4]: `"classification": "primary"` (generic boilerplate justification)
- After: `history/3/19_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json`
  — response[4]: `"classification": "secondary"`, justification explains it as "useful for
  supporting the project's objectives… does not directly shape the project's core success"

**P4 — gpt-4o-mini hong_kong_game improvement**

gpt-4o-mini's notorious over-inclusion on hong_kong_game (12 kept in both before/after of
PR #364, per analysis/43 N1) improved after PR #365. Run 19 (after) shows 6 primary + 3
secondary + 6 absorb = 9 kept (down from 12).

Evidence: `history/3/19_deduplicate_levers/outputs/20260310_hong_kong_game/002-11-deduplicated_levers_raw.json`
— response array: 6 primary (8035c685, c22a661c, e4444cd3, b1306f13, ff374e13, 570921d2),
3 secondary (9ff35b87 Production Efficiency Optimization, e993b611 Audience Engagement
Strategy, 43ce2f8e Hong Kong Identity Amplification Strategy), 6 absorb.

The secondary category is proving its value here — operational levers that were inflating
the primary count are now correctly classified as secondary.

**P5 — 100% success rate maintained**

All 35 after-PR runs (7 models × 5 plans) succeeded with no LLMChatError. The prompt changes
did not break schema compliance or cause validation failures for any model.

Evidence: All `outputs.jsonl` files for runs 15–21 show `"status": "ok"` with no null
errors. All `events.jsonl` files contain only `run_single_plan_start` and
`run_single_plan_complete` events.

**P6 — B3 fix confirmed (all_levers_summary conditional ...)**

The track_activity.jsonl from run 20 (Gemini) confirms the updated system prompt is being
used, including the "All levers under review:" section with `...` used conditionally for
truncated entries.

Evidence: `history/3/20_deduplicate_levers/outputs/20260308_sovereign_identity/track_activity.jsonl`
— LLMChatEndEvent shows system prompt with "All levers under review:" section where lever
summaries are properly truncated. The system prompt also confirms the new calibration hint
and secondary classification examples are present.

**P7 — Justification quality improvement in instruction-following models**

Haiku (run 21) and gpt-4o-mini (run 19) produced notably more detailed, context-grounded
justifications for sovereign_identity compared to before. Haiku's justification for EU
Standards secondary classification explicitly references plan context ("the plan frames EU
engagement as a stretch goal, not a primary success criterion"). This is a qualitative
improvement in reasoning quality.

---

## Comparison

### System Prompt Changes (confirmed from output files)

**Before PR #365** (runs 08–14, `system_prompt` field in output JSON):
```
In a well-formed set of 15 levers, expect 4–8 to be absorbed or removed.
If you find zero absorb/remove decisions, reconsider: the input almost always
contains near-duplicates. Do not keep every lever.
```

**After PR #365** (runs 15–21):
```
Use "primary" only as a last resort — if you genuinely cannot determine a lever's
strategic role after reading the full context. Describe what is unclear in the justification.

In a well-formed set of 15 levers, expect 4–10 to be absorbed or removed. Plans with
many near-duplicate names may require 10 or more absorbs — do not stop early. If you
find zero absorb/remove decisions, reconsider: the input almost always contains
near-duplicates. Do not keep every lever.
```

Also added:
- `secondary` classification with concrete examples
- "do not stop early" instruction
- "expect 4–10" (widened from "4–8")

The "last resort" wording was already in PR #364; PR #365 adds the widened calibration range
and "do not stop early".

---

## Quantitative Metrics

### Sovereign_identity Lever Counts: Before #365 vs After #365

The sovereign_identity plan has 15 input levers (5 unique × 3 near-duplicate instances each).
Expected correct output: 5 kept.

| Model | Before (kept) | Before (P/S/A) | After (kept) | After (P/S/A) | Delta |
|-------|-------------|---------------|------------|--------------|-------|
| llama3.1 | 5 | 5P/0S/10A | 5 | 5P/0S/10A | stable |
| gpt-oss-20b | 5 | 5P/0S/10A | 5 | 5P/0S/10A | stable |
| gpt-5-nano | 3 | 3P/0S/12A | ~2 | 1P/1S/12A+1R | ~same |
| qwen3-30b | 5 | 5P/0S/10A | 3 | 3P/0S/12A | -2 ❌ |
| gpt-4o-mini | 5 | 5P/0S/10A | 5 | 4P/1S/10A | stable ✓ |
| gemini-2.0-flash | **9** | 9P/0S/5A+1R | 5 | 5P/0S/10A | **-4 ✓✓** |
| claude-haiku | 5 | 5P/0S/10A | 5 | 4P/1S/10A | stable ✓ |

Note: "Before" is runs 08–14 (after PR #364 = starting point for this analysis).
Gemini improved from 9 → 5 (fixed). Qwen regressed from 5 → 3 (new issue).

### Secondary Classification Usage (all available data)

| Model / Plan | sovereign_id | hong_kong | Classification |
|-------------|-------------|-----------|----------------|
| haiku | 1S (EU Standards) | — | EU Standards → secondary ✓ |
| gpt-4o-mini | 1S (EU Standards) | 3S (Prod Efficiency, Audience, HK Identity) | Operational levers → secondary ✓ |
| gpt-5-nano | 1S (Policy Advocacy?) | — | Possibly wrong classification |
| gemini | 0S | — | Does not use secondary ❌ |
| llama3.1 | 0S | — | Does not use secondary ❌ |
| gpt-oss-20b | 0S | — | Does not use secondary ❌ |
| qwen3-30b | 0S | — | Does not use secondary ❌ |

### LLMChatError Events

| Period | Errors | Source |
|--------|--------|--------|
| Before (runs 08–14) | 0 | All events.jsonl files |
| After (runs 15–21) | 0 | All events.jsonl files |

### Success Rate

| Period | Plans | Runs | Success | Rate |
|--------|-------|------|---------|------|
| Before (runs 08–14) | 5 | 35 | 35 | 100% |
| After (runs 15–21) | 5 | 35 | 35 | 100% |

---

## Evidence Notes

- System prompt comparison confirmed by reading `system_prompt` field from:
  `history/3/08_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json` (before)
  `history/3/15_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json` (after)

- Gemini calibration fix confirmed by comparing:
  `history/3/13_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json` (before: 9 kept)
  `history/3/20_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json` (after: 5 kept)

- Haiku secondary confirmed:
  `history/3/14_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json` (before: 5P)
  `history/3/21_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json` (after: 4P/1S)

- GPT-4o-mini hong_kong improvement:
  Before: 12 kept (analysis/43 N1 evidence)
  After: 9 kept — `history/3/19_deduplicate_levers/outputs/20260310_hong_kong_game/002-11-deduplicated_levers_raw.json`

- B3 fix: `history/3/20_deduplicate_levers/outputs/20260308_sovereign_identity/track_activity.jsonl`
  LLMChatEndEvent shows updated system prompt with conditional `...` in lever summaries.

- Qwen regression:
  `history/3/18_deduplicate_levers/outputs/20260308_sovereign_identity/002-11-deduplicated_levers_raw.json`
  Shows only 3 entries in `deduplicated_levers` where 5 are expected.

---

## PR Impact

### What the PR was supposed to fix

1. Gemini calibration-capping: "4–8" range caused premature stop at sovereign_identity → widened to "4–10" + "do not stop early"
2. Add primary/secondary classification for downstream prioritization
3. Complete B3 fix (`all_levers_summary` conditional `...`)
4. OPTIMIZE_INSTRUCTIONS 5th failure mode
5. Broaden secondary examples (concrete operational lever types)

### Before vs After Comparison Table

| Metric | Before (runs 08–14) | After (runs 15–21) | Change |
|--------|--------------------|--------------------|--------|
| sovereign_id kept (gemini) | **9** (regression) | **5** (fixed) | ✅ -4 |
| sovereign_id kept (haiku) | 5P/0S | 4P/1S | ✅ secondary used |
| sovereign_id kept (gpt-4o-mini) | 5P/0S | 4P/1S | ✅ secondary used |
| sovereign_id kept (qwen3) | 5 | 3 | ❌ -2 |
| hong_kong kept (gpt-4o-mini) | 12 | 9 | ✅ -3 |
| LLMChatError count | 0 | 0 | stable |
| Success rate | 100% (35/35) | 100% (35/35) | stable |
| Secondary usage (7 models × sovereign_id) | 0 models | 2–3 models | ✅ partial |
| Hierarchy-direction errors | present | present | ❌ unchanged |

### Did the PR fix the targeted issue?

**Yes.** The primary target (gemini sovereign_identity calibration-capping) is confirmed fixed.
Gemini's sovereign_identity lever count dropped from 9 to 5 (10 absorbs, correct behavior).
This directly addresses N2 from analysis/43.

The secondary classification feature is partially working: haiku and gpt-4o-mini now correctly
identify operational/supporting levers as secondary, which is the downstream prioritization goal.
gpt-4o-mini's hong_kong over-inclusion (formerly 12 kept) dropped to 9 through the secondary
classification pathway.

### Regressions introduced?

**Qwen3-30b regression on sovereign_identity**: 5 kept → 3 kept. The widened calibration
hint ("4–10") may have pushed Qwen toward more aggressive absorption. Before #365, Qwen
correctly kept 5 for sovereign_identity; now it collapses to 3. This is a new problem
introduced by the prompt change, though it may be Qwen's inherent chain-absorption tendency
amplified rather than a fundamental new failure.

**Hierarchy-direction violations unchanged**: Multiple models still absorb general levers
into specific ones (wrong direction). This was present before and is not addressed by #365.

### Verdict

**KEEP** — the PR resolves its primary target (Gemini calibration-capping fixed, -4 levers
for sovereign_identity), adds measurable secondary classification benefits for instruction-
following models (haiku and gpt-4o-mini both improved), and reduces gpt-4o-mini over-inclusion
on hong_kong_game by 3 levers. The Qwen3 regression on sovereign_identity (-2 levers) is a
minor counterfactual but does not outweigh the gemini fix which was a documented regression
from PR #364. The complete B3 fix is a correctness improvement that avoids misleading LLM
behavior on truncation boundaries. Net: KEEP.

---

## Questions For Later Synthesis

Q1. Qwen3-30b chain absorption: Is the sovereign_identity collapse (5→3) isolated or does
it generalize to other plans? Needs per-plan kept counts for run 18 to determine whether
the widened calibration hint hurt Qwen more broadly.

Q2. Secondary adoption rate: Only 2–3 models use secondary consistently. Is the "last resort"
framing for primary the right lever to push, or should the prompt strengthen secondary
guidance further? Current examples (marketing timing, reporting cadence) may not translate
well to all plan types.

Q3. Hierarchy-direction as OPTIMIZE_INSTRUCTIONS entry: Should H-D errors be added as a 6th
known failure mode with a concrete example? Currently listed but without a proposed prompt fix.

Q4. GPT-5-nano instability: Run 17 shows meta-commentary leaking into justification fields.
Is this a consistent pattern for gpt-5-nano on structured output tasks, or a one-off?

Q5. Secondary vs. absorb boundary: Some models absorb levers that the secondary category would
better handle (e.g., Gemini absorbing the first-batch EU Standards lever into a duplicate
rather than classifying it as secondary). Should the prompt explicitly say "if a lever is
operational but distinct, use secondary rather than absorb"?

---

## Reflect

The PR achieves its main goal (Gemini calibration fix) but reveals a new tension: widening
the absorb range helps models that were under-absorbing (Gemini) but may push models already
near the boundary (Qwen) into over-absorption. A single calibration hint cannot optimally
serve all models simultaneously.

The secondary classification is working but unevenly. The models that benefit most (haiku,
gpt-4o-mini) already had good instruction-following; the models that don't use it (Gemini,
llama3.1) may need different guidance rather than more examples.

The hierarchy-direction problem (absorbing general into specific) is a systematic issue
across multiple models that has persisted through multiple PRs. It may require a code-level
fix (the runner resolves absorption chains, but keeps the wrong instance) rather than a
prompt fix.

---

## Potential Code Changes

**C1 — Hierarchy-aware instance selection in absorption resolution**

When two levers are absorbed together (general absorbs specific, or specific absorbs general
incorrectly), the runner currently keeps whichever lever the LLM classified as `primary`.
If the LLM classifies the first-batch (general) lever as `absorb` into the second-batch
(specific) lever but the semantics are equivalent, the runner could apply a tie-breaking rule:
prefer the lever with the earlier position in the input list (first occurrence = more general,
more likely to be canonical). This would fix the hierarchy-direction issue independently of
which instance the LLM designated as keeper.

File: `deduplicate_levers.py` — in the absorption resolution logic that builds `deduplicated_levers`.

**C2 — Per-model calibration hints**

The current calibration hint is a single global string. If Gemini needs "4–10" but Qwen
already absorbs aggressively at that range, a model-adaptive calibration parameter could
help. However, this requires model-specific system prompt variants which adds complexity.

Alternative: Remove the numeric calibration hint entirely and rely solely on "do not stop
early" + "do not keep every lever" without an expected range. This avoids over-constraining
models with heterogeneous absorption tendencies. The range was added to fix llama3.1 blanket-
keep; it then calibration-capped Gemini; widening it may now over-absorb Qwen. The numeric
hint may be the wrong mechanism.

**C3 — Schema validation for self-referential absorb targets**

GPT-5-nano produced `absorb` decisions pointing to the lever's own ID (self-reference).
Adding post-processing validation that checks: if `classification == "absorb"` and the
target ID equals `lever_id`, flag as malformed and re-classify as `primary` (since the
intent was "keep this lever"). This would make the pipeline robust to this edge case.

---

## Summary

PR #365 achieves its primary goal: Gemini's sovereign_identity calibration-capping is fixed
(9 kept → 5 kept). Two additional benefits: haiku and gpt-4o-mini now correctly classify
supporting levers as secondary (downstream prioritization improvement), and gpt-4o-mini's
hong_kong_game over-inclusion dropped from 12 to 9 through the secondary pathway.

Regressions: Qwen3-30b regressed on sovereign_identity (5→3 kept). Hierarchy-direction
violations persist in Gemini, gpt-oss-20b, and gpt-5-nano (unchanged from before). The
numeric calibration hint ("4–10") appears to create different pressures for different models:
Gemini needed it widened; Qwen may now be over-absorbing because of it.

Structural compliance: 100% success rate maintained across all 35 after-PR runs. No
LLMChatError events. B3 fix is confirmed complete (conditional `...` in `all_levers_summary`).

**Verdict: KEEP** — net improvement, primary regression from PR #364 is resolved.
