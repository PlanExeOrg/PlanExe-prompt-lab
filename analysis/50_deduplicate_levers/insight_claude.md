# Insight Claude

Analysis of PR #373 — `feat: single-call Likert scoring for deduplicate_levers`

Runs examined (after PR #373): `history/3/57_deduplicate_levers` through `history/3/63_deduplicate_levers`.
Runs examined (before, PR #372): `history/3/50_deduplicate_levers` through `history/3/56_deduplicate_levers`.
Plans: `20250321_silo`, `20250329_gta_game`, `20260308_sovereign_identity`, `20260310_hong_kong_game`, `20260311_parasomnia_research_unit`.

## Model–Run Mapping

| Run | Model |
|-----|-------|
| 50 (before) | ollama-llama3.1 |
| 51 (before) | openrouter-openai-gpt-oss-20b |
| 52 (before) | openai-gpt-5-nano |
| 53 (before) | openrouter-qwen3-30b-a3b |
| 54 (before) | openrouter-openai-gpt-4o-mini |
| 55 (before) | openrouter-gemini-2.0-flash-001 |
| 56 (before) | anthropic-claude-haiku-4-5-pinned |
| 57 (after) | ollama-llama3.1 |
| 58 (after) | openrouter-openai-gpt-oss-20b |
| 59 (after) | openai-gpt-5-nano |
| 60 (after) | openrouter-qwen3-30b-a3b |
| 61 (after) | openrouter-openai-gpt-4o-mini |
| 62 (after) | openrouter-gemini-2.0-flash-001 |
| 63 (after) | anthropic-claude-haiku-4-5-pinned |

Source: `history/3/{run}_deduplicate_levers/meta.json`.

---

## Architecture Change

PR #373 replaces 18 sequential per-lever LLM calls with a single batch call. The model receives all levers at once and scores each on a 5-point Likert scale:

- **+2** (highly relevant): lever directly addresses a core challenge
- **+1** (somewhat relevant): lever addresses a real concern but is not central
- **0** (borderline): marginal relevance
- **-1** (low relevance): overlaps with a more relevant lever or peripheral
- **-2** (irrelevant): redundant, off-topic, or fully covered by other levers

Levers scoring ≥ 1 are kept; levers scoring ≤ 0 are removed. The code maps score 2 → `primary` and score 1 → `secondary` in the `classification` field of `deduplicated_levers`.

The system prompt also includes: "When two levers cover similar ground, score the more general one higher and the more specific one lower" and "Expect 25-50% of levers to score 0 or below."

Source: `history/3/57_deduplicate_levers/outputs/20250321_silo/002-11-deduplicated_levers_raw.json`, `system_prompt` field.

---

## Negative Things

**N1 — llama3.1 inverts the Likert scale on silo and gta_game, catastrophically over-removing levers.**

Run 57 (llama3.1) on the silo plan scores 17 out of 18 levers as -1 or -2. Only one lever (a6d45d69, Resource Allocation Strategy) scores 1. The deduplicated_levers list contains exactly 1 lever.

The critical tell: the justifications directly contradict the scores. Examples:
- Lever 9ed3015e (Agricultural System Design), score=-2: justification says "Agricultural system design is crucial for sustaining thousands of people, and it directly impacts the physical infrastructure of the silo. This lever is **highly relevant** to the project plan."
- Lever 125ce960 (Power Generation Strategy), score=-2: justification says "Power generation strategy directly impacts the silo's ability to sustain itself...This lever is **highly relevant** to the project plan."
- Lever 91eadbb9 (Community Governance Model), score=-2: justification says "Community governance model directly impacts how resources are allocated and decisions are made within the silo. This lever is **highly relevant** to the project plan."

The model writes "highly relevant" but assigns -2 (irrelevant). This is complete scale inversion. The same pattern holds for the gta_game plan (run 57): only 1 lever out of 18 kept.

Evidence: `history/3/57_deduplicate_levers/outputs/20250321_silo/002-11-deduplicated_levers_raw.json` lines 5-92.
Evidence: `history/3/57_deduplicate_levers/outputs/20250329_gta_game/002-11-deduplicated_levers_raw.json` lines 94-118.

**N2 — The Likert approach does not deduplicate: capable models keep nearly all 18 levers.**

The Likert prompt measures relevance, not redundancy. Most capable models score all or nearly all levers 1-2, keeping 16-18 out of 18 levers with no meaningful deduplication.

Comparison for the silo plan:
- Run 58 (gpt-oss-20b, after): All 18 levers scored 1 or 2. **0 levers removed.**
- Run 51 (gpt-oss-20b, before, PR #372): **2 levers correctly removed** with explicit overlap reasoning.
  - de8ff746 (Technological Integration Strategy) removed into 99e29b00 (Technological Advancement Protocol): "Both govern the silo's overall technology trajectory, including adoption, openness, and resilience. The Advancement Protocol is broader... Merging it into the Advancement Protocol preserves all strategic intent without duplication."
  - ee0996f6 (Information Dissemination Protocol) removed into b664e24a (Information Control Protocols): "Information Dissemination Protocol is a more specific variant of the broader governance lever... The Control Protocols lever already captures the strategic decision..."

In the after run, the gpt-oss-20b model assigns these same overlapping levers scores of 1-2 and keeps both. It implicitly recognizes overlap (ee0996f6 scores 1 "secondary to the overarching control lever"), but score=1 means kept, not removed.

Evidence: `history/3/58_deduplicate_levers/outputs/20250321_silo/002-11-deduplicated_levers_raw.json` (18 entries in `deduplicated_levers`).
Evidence: `history/3/51_deduplicate_levers/outputs/20250321_silo/002-11-deduplicated_levers_raw.json` (16 entries in `deduplicated_levers`, 2 removed).

**N3 — Conceptual flaw: relevance ≠ deduplication.**

The Likert prompt says "When two levers cover similar ground, score the more general one higher and the more specific one lower." But the threshold for removal is ≤ 0. A specific lever that partially overlaps a more general one still scores 1 (somewhat relevant), which keeps it. The only way to remove overlapping levers is if they score exactly 0 — but models rarely assign 0 when a lever addresses even a tangential concern.

In run 51 (gpt-oss-20b, before), the primary/secondary/remove taxonomy explicitly forced the model to ask "Is this redundant?" The `remove` classification was a binary decision that caught duplicates even when they were marginally relevant. The Likert approach conflates "relevance to the plan" with "uniqueness among levers," which are different questions.

**N4 — gpt-oss-20b ignores the 25-50% calibration guidance.**

The system prompt says "Expect 25-50% of levers to score 0 or below. If you score everything 1 or 2, reconsider." Run 58 (gpt-oss-20b, silo) scored all 18 levers 1 or 2 — exactly the case the prompt says to reconsider. Yet all 18 are kept. The calibration warning is not effective for this model.

Evidence: `history/3/58_deduplicate_levers/outputs/20250321_silo/002-11-deduplicated_levers_raw.json` — all 18 entries in `response` have score 1 or 2.

**N5 — llama3.1 produces a duplicate lever entry in the hong_kong_game response.**

Run 57 (llama3.1, hong_kong_game): lever_id `32ad06c5` appears twice in the `response` array (once as the primary score entry, once as a spurious duplicate at position 19). This is a structural error — the model hallucinated an extra entry. The `deduplication_justification` for the duplicate reads "This lever is a duplicate of another lever and should not be scored separately," which reveals the model noticed the duplicate but could not avoid outputting it.

Evidence: `history/3/57_deduplicate_levers/outputs/20260310_hong_kong_game/002-11-deduplicated_levers_raw.json`, lines 94-97 (duplicate entry).

**N6 — The approach supersedes PR #372 without addressing the issues identified in the prior synthesis.**

The `analysis/49_deduplicate_levers/cross_iteration_verdict.md` and `synthesis.md` identified three prompt-quality bugs to fix in the primary/secondary/remove taxonomy (B2: contradictory fallback, B3: template-lock in secondary definition, S1: calibration for 18 levers). PR #373 abandons the taxonomy entirely instead of fixing these bugs. The prior verdict was "The taxonomy is right. The remaining issues are prompt-quality problems."

---

## Positive Things

**P1 — 100% structural success rate across all 35 runs.**

All 7 runs × 5 plans show `"status": "ok"` with `"calls_succeeded": 1`. No LLMChatError entries in any events.jsonl. All responses parsed successfully into valid JSON with the expected `response` and `deduplicated_levers` fields.

Evidence: `history/3/57_deduplicate_levers/outputs.jsonl` through `history/3/63_deduplicate_levers/outputs.jsonl`.

**P2 — Substantial speed improvement: 18 calls → 1 call per plan.**

The PR achieves its stated goal of replacing 18 sequential calls with 1 batch call.

Duration comparison for the silo plan:
| Run | Model | Before duration (18 calls) | After duration (1 call) | Speedup |
|-----|-------|---------------------------|------------------------|---------|
| gpt-oss-20b (51→58) | 196.6s | 51.0s | 3.9× |
| gemini (55→62) | ? | 11.2s | >10× est. |
| haiku (56→63) | ? | 24.3s | >5× est. |

Source: `history/3/51_deduplicate_levers/outputs.jsonl` (silo: 196.61s), `history/3/58_deduplicate_levers/outputs.jsonl` (silo: 51.01s).

**P3 — The batch scoring is coherent for most capable models.**

Models like gpt-5-nano, gemini, haiku, and gpt-4o-mini produce sensible scores that distinguish high-relevance levers (score=2) from peripheral ones (score=1 or 0). The reasoning in justifications is grounded in plan context, not generic boilerplate.

Example from run 62 (gemini, silo): lever f93eac77 (External Engagement Policy) scores 0, justification: "The project explicitly aims for isolation from the outside world, making external engagement a marginal concern." This is plan-specific and correct.

Evidence: `history/3/62_deduplicate_levers/outputs/20250321_silo/002-11-deduplicated_levers_raw.json`.

**P4 — Score-to-classification mapping preserves the primary/secondary triage dimension.**

The code correctly maps score 2 → `primary` and score 1 → `secondary` in `deduplicated_levers.classification`. The triage signal from PR #372 is preserved for levers that do get kept.

---

## Comparison

### Architectural approach

| Aspect | Before (PR #372) | After (PR #373) |
|--------|-----------------|-----------------|
| LLM calls per plan | 18 (one per lever) | 1 (batch) |
| Duration per plan (est.) | ~180-200s | ~11-100s |
| Schema | primary/secondary/remove | Likert -2 to +2 |
| Deduplication mechanism | Explicit `remove` classification | Score ≤ 0 removal |
| Overlap detection | Explicit lever ID in justification | Lower score (may still keep) |
| Classification output | primary/secondary/remove | primary/secondary (no remove field) |

### Deduplication quality — silo plan (18 input levers)

| Run | Model | Levers removed (before) | Levers removed (after) | Change |
|-----|-------|------------------------|----------------------|--------|
| gpt-oss-20b (51→58) | 2 (sensible dedup) | 0 | **−2 regression** |
| llama3.1 (50→57) | 0 (no dedup) | 17 (scale inversion!) | **catastrophic** |
| gpt-5-nano (52→59) | ? | 2 (borderline only) | minimal dedup |
| qwen3 (53→60) | ? | 2 (borderline only) | minimal dedup |
| gpt-4o-mini (54→61) | ? | ~1 | minimal dedup |
| gemini (55→62) | ? | 1 | minimal dedup |
| haiku (56→63) | ? | 1 | minimal dedup |

Source: Counting entries in `deduplicated_levers` vs `response` arrays in the respective output files.

### Deduplication quality — hong_kong_game (18 input levers)

| Run (after) | Model | Score distribution | Removed | Kept |
|-------------|-------|-------------------|---------|------|
| 57 (llama3.1) | -2: 3, -1: 0, 0: 1, 1: 13, 2: 2 | 4 | 14 |
| 58 (gpt-oss-20b) | -2: 0, -1: 0, 0: 0, 1: 11, 2: 7 | 0 | 18 |
| 62 (gemini) | mix, some 0 | ~2 | ~16 |
| 63 (haiku) | mix, some 0 | ~1 | ~17 |

For reference, before (PR #372) on hong_kong_game: haiku removed 7/18 (39%), llama3.1 removed 7/18 (39%), gemini removed ~8/18 (44%). Source: `analysis/49_deduplicate_levers/insight_claude.md`.

---

## Quantitative Metrics

### Success Rate

| Run | Model | Plans OK | Calls per plan | LLMChatErrors |
|-----|-------|----------|---------------|---------------|
| 57 | llama3.1 | 5/5 | 1 | 0 |
| 58 | gpt-oss-20b | 5/5 | 1 | 0 |
| 59 | gpt-5-nano | 5/5 | 1 | 0 |
| 60 | qwen3-30b-a3b | 5/5 | 1 | 0 |
| 61 | gpt-4o-mini | 5/5 | 1 | 0 |
| 62 | gemini-2.0-flash-001 | 5/5 | 1 | 0 |
| 63 | haiku-4-5-pinned | 5/5 | 1 | 0 |

Total: 35/35 successful. No LLMChatErrors. Source: `outputs.jsonl` for each run.

### Deduplication Rate — silo plan

| Run | Model | Input levers | Kept | Removed | Removal % |
|-----|-------|-------------|------|---------|-----------|
| 50 (before) | llama3.1 | 18 | 18 | 0 | 0% |
| 51 (before) | gpt-oss-20b | 18 | 16 | 2 | 11% |
| 57 (after) | llama3.1 | 18 | **1** | **17** | **94% (inverted!)** |
| 58 (after) | gpt-oss-20b | 18 | **18** | **0** | **0%** |
| 59 (after) | gpt-5-nano | 18 | 16 | 2 | 11% |
| 60 (after) | qwen3 | 18 | 16 | 2 | 11% |
| 62 (after) | gemini | 18 | 17 | 1 | 6% |
| 63 (after) | haiku | 18 | 17 | 1 | 6% |

Source: Counting entries in `deduplicated_levers` arrays.

Note: The before (PR #372) average levers kept across all 35 runs was ~15.3/18 (from `analysis/49_deduplicate_levers/cross_iteration_verdict.md`), with avg removal ~2.7. The after (PR #373) average for capable models is ~17/18 (far higher retention, less dedup), with llama3.1 as an outlier at ~1/18 for some plans.

### Score Distribution Patterns — silo plan

| Model (run) | Score -2 | Score -1 | Score 0 | Score 1 | Score 2 |
|------------|----------|----------|---------|---------|---------|
| llama3.1 (57) | 13 | 4 | 0 | 1 | 0 |
| gpt-oss-20b (58) | 0 | 0 | 0 | 9 | 9 |
| gpt-5-nano (59) | 0 | 0 | 2 | 2 | 14 |
| qwen3 (60) | 0 | 0 | 2 | 0 | 16 |
| gemini (62) | 0 | 0 | 1 | 0 | 17 |
| haiku (63) | 0 | 0 | 1 | 5 | 12 |

llama3.1 is a severe outlier. All other models stay in the 0-2 range and keep 16-18 levers. Source: Counting scores from the `response` arrays in respective output files.

### Duration Improvement

| Plan | Before (run 51, gpt-oss-20b, 18 calls) | After (run 58, gpt-oss-20b, 1 call) | Speedup |
|------|-----------------------------------------|--------------------------------------|---------|
| silo | 196.6s | 51.0s | 3.9× |
| gta_game | 159.9s | 104.2s | 1.5× |
| sovereign_identity | 185.3s | 47.4s | 3.9× |
| hong_kong_game | 197.8s | 81.2s | 2.4× |
| parasomnia | 193.4s | 30.6s | 6.3× |

Source: `history/3/51_deduplicate_levers/outputs.jsonl` and `history/3/58_deduplicate_levers/outputs.jsonl`.

---

## Evidence Notes

- Scale inversion for llama3.1: `history/3/57_deduplicate_levers/outputs/20250321_silo/002-11-deduplicated_levers_raw.json` — lever 9ed3015e has score=-2 and justification "This lever is highly relevant to the project plan."
- gpt-oss-20b keeps all 18 levers: `history/3/58_deduplicate_levers/outputs/20250321_silo/002-11-deduplicated_levers_raw.json` — `deduplicated_levers` has 18 entries.
- gpt-oss-20b before run removed 2: `history/3/51_deduplicate_levers/outputs/20250321_silo/002-11-deduplicated_levers_raw.json` — entries de8ff746 and ee0996f6 classified as `remove` with explicit overlap justifications.
- Duplicate lever entry: `history/3/57_deduplicate_levers/outputs/20260310_hong_kong_game/002-11-deduplicated_levers_raw.json` — lever 32ad06c5 appears at positions 0 and 18 of the `response` array.
- Cross-iteration context: `analysis/49_deduplicate_levers/cross_iteration_verdict.md` — before average was 15.3 levers kept/18, 2.7 removed. PR #373 after for capable models: ~17/18 kept.
- System prompt from after run: `history/3/57_deduplicate_levers/outputs/20250321_silo/002-11-deduplicated_levers_raw.json`, `system_prompt` field — confirms Likert scale definition.

---

## PR Impact

**What PR #373 was supposed to fix:**
Replace 18 sequential per-lever LLM calls with a single batch call using Likert relevance scoring (-2 to +2). Keep levers scoring ≥ 1; remove levers scoring ≤ 0.

**Before vs. after comparison:**

| Metric | Before (runs 50–56, PR #372) | After (runs 57–63, PR #373) | Change |
|--------|------------------------------|------------------------------|--------|
| LLM calls per plan | 18 | 1 | **18× reduction ✓** |
| Speed (silo, gpt-oss-20b) | 196.6s | 51.0s | **3.9× faster ✓** |
| Success rate | 35/35 | 35/35 | = |
| LLMChatErrors | 0 | 0 | = |
| Avg levers kept (capable models, silo) | ~16 | ~17 | slight regression |
| Semantic dedup quality (gpt-oss-20b, silo) | 2 overlapping levers removed | 0 overlapping levers removed | **regression ✗** |
| llama3.1 silo output | 18 levers kept | 1 lever kept (inverted scale) | **catastrophic ✗** |
| llama3.1 gta_game output | ? | 1 lever kept (inverted scale) | **catastrophic ✗** |
| primary/secondary triage preserved | yes | yes (via score mapping) | = |

**Did the PR fix the targeted issue?**
Partially. The PR achieves its stated performance goal: 1 call instead of 18, and speed improvements of 1.5–6× depending on the plan. Structurally, all runs succeed (35/35).

However, the PR introduces two significant quality regressions:

1. **Deduplication failure for capable models**: The Likert approach measures relevance, not redundancy. Models score overlapping levers as 1 (somewhat relevant) and keep both, where PR #372 would have used `remove` with an explicit overlap justification. The step is no longer effectively deduplicating.

2. **Catastrophic scale inversion for llama3.1**: On at least 2 of 5 plans (silo, gta_game), llama3.1 inverts the Likert scale, keeping only 1 lever out of 18. The downstream plan would be built on a single lever, which is a catastrophic quality failure for that model.

**Regressions:**
- Semantic deduplication is broken for all capable models tested.
- llama3.1 produces pathological single-lever output on at least 40% of plans.

**Verdict: REVERT**

The speed improvement is real and valuable, but the deduplication quality regression is too severe. For capable models, the step no longer deduplicates overlapping levers. For llama3.1, the step catastrophically over-removes. The taxonomy-based approach from PR #372 (primary/secondary/remove) should be restored. The speed goal could be revisited as a follow-up — either by batching the 18 calls differently or restructuring the approach without abandoning the dedup mechanism.

---

## Questions For Later Synthesis

Q1 — Is the speed goal (1 call vs 18 calls) worth pursuing separately from the deduplication design? The Likert approach achieves the speed goal but loses dedup quality. Could a batch primary/secondary/remove call achieve both?

Q2 — Why does llama3.1 invert the scale on some plans (silo, gta_game) but not others (hong_kong_game)? Is it a context-length issue, a token-counting issue with the Likert description, or a prompt misunderstanding specific to certain input formats?

Q3 — The system prompt says "Expect 25-50% of levers to score 0 or below." This guidance is ignored by several models (gpt-oss-20b, qwen3 all score ≥ 1). Would a stronger enforcement ("You MUST assign score ≤ 0 to at least 4 of the 18 levers") produce better calibration?

Q4 — The `analysis/49_deduplicate_levers/cross_iteration_verdict.md` identified 3 specific prompt fixes (B2, B3, S1) for the primary/secondary/remove taxonomy. None of those were attempted before PR #373 superseded PR #372. Should those fixes be implemented on a reverted PR #372 base?

Q5 — The gpt-oss-20b output for the silo plan (run 58) noted that ee0996f6 (Information Dissemination Protocol) "is a specific aspect of information control; it is relevant but secondary to the overarching control lever." The model recognizes the overlap but still keeps it at score=1. Would changing the threshold from ≥ 1 to ≥ 2 produce better deduplication, at the cost of keeping fewer levers?

---

## Reflect

The cross-experiment comparison prerequisites are satisfied: both `analysis/49_deduplicate_levers/meta.json` and `analysis/50_deduplicate_levers/meta.json` use `input: "snapshot/0_identify_potential_levers"` and the same `deduplicate_levers` step.

The core tension in this PR is: the Likert approach asks "Is this lever relevant to this plan?" while the deduplication step's purpose is "Is this lever redundant with another lever?" These are related but different questions. A lever can be highly relevant to a plan AND redundant with another lever. The Likert approach cannot distinguish these cases.

The prior taxonomy (primary/secondary/remove) forced a ternary decision where `remove` explicitly meant "redundant." The synthesis from iter 49 concluded that all three categories were meaningfully exercised (primary: 58%, secondary: 27%, remove: 15%). PR #373 replaces this proven mechanism with an approach that produces ~0% effective removal for capable models.

The speed improvement (18× fewer API calls) is architecturally valuable and should be pursued in a follow-up. However, the implementation must preserve the deduplication mechanism. A promising direction: batch all 18 levers in a single call, but use the primary/secondary/remove schema from PR #372, not Likert scoring.

---

## Hypotheses

**H1 — The Likert threshold ≤ 0 is not strict enough to deduplicate semantically overlapping levers.**
Evidence: gpt-oss-20b scores ee0996f6 (Information Dissemination Protocol) = 1 even while noting it "is a specific aspect of information control...secondary to the overarching control lever." Score 1 means kept. The before run correctly classifies it as `remove`.
Prediction: Changing the threshold to ≥ 2 (keep only "highly relevant" levers) would increase deduplication but risk over-removing levers that are genuinely useful.

**H2 — The Likert prompt should explicitly separate "relevance" from "uniqueness" into two scoring dimensions.**
Evidence: The current prompt conflates both into a single score. "This lever is highly relevant but duplicates another" cannot be expressed — it would be scored 2 and kept.
Prediction: A two-pass approach (first score relevance, then score uniqueness among relevance-passing levers) would better capture both dimensions.

**C1 — Batch the primary/secondary/remove call as a single LLM request (all 18 levers at once).**
Evidence: PR #373 proves a batch call is feasible — all models successfully score all 18 levers in one call. The issue is the scoring schema, not the batching architecture.
Prediction: Replacing the Likert schema with the primary/secondary/remove schema from PR #372 in a single batch call would achieve both the speed goal and deduplication quality. This requires verifying that the per-lever classification (not per-response-as-a-whole) still works when all levers are scored simultaneously.

**C2 — Add a floor check on deduplicated_levers count.**
Evidence: llama3.1 produces 1-lever output for silo and gta_game after scale inversion. The downstream `focus_on_vital_few_levers` step is designed to receive a set of levers, not a single lever.
Prediction: A post-hoc check that raises a validation error (or triggers a retry) when `len(deduplicated_levers) < 5` would catch the catastrophic failure and prompt a retry or fallback.

---

## Potential Code Changes

**C1 — Revert to primary/secondary/remove taxonomy, but batch all levers in a single call.**
The PR's architecture innovation (batch call) is valuable. The schema change (Likert) is not. The fix is to use the PR #372 system prompt within a batch call structure. This requires verifying that the primary/secondary/remove per-lever classification degrades gracefully when all 18 levers appear simultaneously.

**C2 — Add minimum deduplicated_levers count validation.**
After parsing the model's response, validate `len(deduplicated_levers) >= min_expected_count` (suggested: 5, or 25% of input). If the check fails, log a warning and consider a retry. This catches scale-inversion failures before the output is saved.

**C3 — Add a sanity check: if all scores cluster at -1 or -2, flag as potential scale inversion.**
If >75% of levers score ≤ -1 in a single call, the model may have inverted the scale. Log a warning with the score distribution for debugging.

---

## Summary

PR #373 achieves its stated goal: 1 LLM call per plan instead of 18, with 1.5–6× speed improvement and 100% structural success. However, it introduces two severe quality regressions:

1. **Deduplication failure**: The Likert relevance scoring does not effectively deduplicate overlapping levers. Capable models keep 16-18 out of 18 levers (before: ~15.3/18). The semantically redundant pairs correctly removed by PR #372 (e.g., Information Dissemination Protocol as a duplicate of Information Control Protocols) are now kept by all capable models.

2. **llama3.1 scale inversion**: On at least 2 of 5 plans, llama3.1 inverts the Likert scale entirely, writing "highly relevant" in justifications but assigning -2 scores. Result: only 1 lever out of 18 is kept, which is catastrophic for the downstream plan quality.

The taxonomy-based approach from PR #372 (primary/secondary/remove) should be restored. The speed goal (1 batch call) is worth pursuing as a follow-up with the PR #372 schema.

**Verdict: REVERT**
