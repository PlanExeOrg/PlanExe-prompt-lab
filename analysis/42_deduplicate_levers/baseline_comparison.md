# Baseline Comparison: deduplicate_levers

## Overview

PR #363 introduced a new `classification` field in `deduplicated_levers` output, splitting the old single `keep` classification into `primary` (essential strategic levers — methodology, governance, high-stakes execution) and `secondary` (supporting/operational — communications, presentation, routine process). The response classification vocabulary also changed: old prompt used `keep`/`absorb`/`remove`; new prompt uses `primary`/`secondary`/`absorb`/`remove`.

7 models were tested across 5 plans each (35 total runs), all succeeded.

---

## Success Rate

| Model | Run | Succeeded | Total | Rate | Failures |
|-------|-----|-----------|-------|------|----------|
| ollama-llama3.1 | 01 | 5 | 5 | 100% | none |
| openrouter-openai-gpt-oss-20b | 02 | 5 | 5 | 100% | none |
| openai-gpt-5-nano | 03 | 5 | 5 | 100% | none |
| openrouter-qwen3-30b-a3b | 04 | 5 | 5 | 100% | none |
| openrouter-openai-gpt-4o-mini | 05 | 5 | 5 | 100% | none |
| openrouter-gemini-2.0-flash-001 | 06 | 5 | 5 | 100% | none |
| anthropic-claude-haiku-4-5-pinned | 07 | 5 | 5 | 100% | none |

All 7 models achieved 100% success rate with no failures across all 5 plans.

---

## Quantitative Comparison

### Lever Count and Reduction

| Metric | Baseline (gemini-2.0-flash-001, old prompt) | llama3.1 | gpt-oss-20b | gpt-5-nano | qwen3-30b-a3b | gpt-4o-mini | gemini-2.0-flash-001 | claude-haiku-4-5 |
|--------|---------------------------------------------|----------|-------------|------------|---------------|-------------|----------------------|-----------------|
| Avg kept levers | 7.0 | 10.6 | 7.2 | 5.0 | 8.6 | 9.4 | 7.0 | 6.8 |
| Input levers | 15 | 15 | 15 | 15 | 15 | 15 | 15 | 15 |
| Reduction ratio | 53.3% | 29.3% | 52.0% | 66.7% | 42.7% | 37.3% | 53.3% | 54.7% |

**Baseline target: 7.0 kept levers per plan (53% reduction)**

### Per-Plan Lever Counts

| Plan | Baseline | llama3.1 | gpt-oss-20b | gpt-5-nano | qwen3-30b-a3b | gpt-4o-mini | gemini-flash | claude-haiku |
|------|----------|----------|-------------|------------|---------------|-------------|--------------|--------------|
| 20250321_silo | 7 | 15 | 7 | 4 | 10 | 10 | 7 | 6 |
| 20250329_gta_game | 8 | 9 | 7 | 5 | 12 | 9 | 8 | 9 |
| 20260308_sovereign_identity | 5 | 6 | 6 | 4 | 3 | 5 | 5 | 5 |
| 20260310_hong_kong_game | 7 | 15 | 8 | 4 | 7 | 12 | 7 | 7 |
| 20260311_parasomnia | 8 | 8 | 8 | 8 | 11 | 11 | 8 | 7 |

### Classification Distribution in Response

All 7 models used the new `primary`/`secondary`/`absorb`/`remove` vocabulary. The baseline used the old `keep`/`absorb` vocabulary.

| Model | primary% | secondary% | absorb% | remove% |
|-------|----------|------------|---------|---------|
| Baseline (old prompt) | keep: 47% | — | 53% | 0% |
| llama3.1 (01) | 67% | 4% | 29% | 0% |
| gpt-oss-20b (02) | 45% | 3% | 51% | 1% |
| gpt-5-nano (03) | 29% | 4% | 67% | 0% |
| qwen3-30b-a3b (04) | 55% | 3% | 43% | 0% |
| gpt-4o-mini (05) | 52% | 11% | 37% | 0% |
| gemini-2.0-flash-001 (06) | 44% | 3% | 53% | 0% |
| claude-haiku-4-5 (07) | 35% | 11% | 49% | 5% |

### New `classification` Field in deduplicated_levers

| Model | Has `classification` field? | Values observed |
|-------|-----------------------------|-----------------|
| Baseline | NO | (absent — old prompt) |
| llama3.1 (01) | YES | primary, secondary |
| gpt-oss-20b (02) | YES | primary, secondary |
| gpt-5-nano (03) | YES | primary, secondary |
| qwen3-30b-a3b (04) | YES | primary, secondary |
| gpt-4o-mini (05) | YES | primary, secondary |
| gemini-2.0-flash-001 (06) | YES | primary, secondary |
| claude-haiku-4-5 (07) | YES | primary, secondary |

All 7 experiment models correctly output the new `classification` field with `primary`/`secondary` values in the `deduplicated_levers` objects, confirming the new schema flows correctly.

### % Secondary (of kept levers)

| Model | Primary kept | Secondary kept | % Secondary |
|-------|-------------|----------------|-------------|
| llama3.1 (01) | 50 | 3 | 5.7% |
| gpt-oss-20b (02) | 34 | 2 | 5.6% |
| gpt-5-nano (03) | 22 | 3 | 12.0% |
| qwen3-30b-a3b (04) | 41 | 2 | 4.7% |
| gpt-4o-mini (05) | 39 | 8 | 17.0% |
| gemini-flash (06) | 33 | 2 | 5.7% |
| claude-haiku-4-5 (07) | 26 | 8 | 23.5% |

### Output Quality Metrics (averaged across 5 plans)

| Model | Avg name len | Avg consequences len | Avg justification len |
|-------|-------------|----------------------|-----------------------|
| Baseline | 28 chars | 275 chars | 283 chars |
| llama3.1 (01) | 28 chars | 280 chars | 295 chars |
| gpt-oss-20b (02) | 28 chars | 278 chars | 422 chars |
| gpt-5-nano (03) | 29 chars | 284 chars | 598 chars |
| qwen3-30b-a3b (04) | 28 chars | 283 chars | 525 chars |
| gpt-4o-mini (05) | 28 chars | 287 chars | 488 chars |
| gemini-flash (06) | 29 chars | 275 chars | 339 chars |
| claude-haiku-4-5 (07) | 28 chars | 284 chars | 699 chars |

---

## Quality Assessment

### A. Schema Compliance and New Feature Adoption

All 7 experiment models correctly implemented PR #363's changes:
- New vocabulary (`primary`/`secondary`/`absorb`/`remove`) used in the response array
- New `classification` field added to each object in `deduplicated_levers`
- `classification` values are exclusively `primary` or `secondary` in the output (as intended — absorbed/removed levers do not appear in `deduplicated_levers`)

The PR description mentions `keep-core`/`keep-secondary` as conceptual names, but the actual implementation uses `primary`/`secondary` in both the system prompt and model outputs, which is internally consistent.

### B. Deduplication Quality — Reduction Ratio

The baseline (gemini-2.0-flash-001 with old prompt) reduced 15 input levers to 7.0 kept on average (53% reduction). Among the 7 experiment models:

- **gemini-2.0-flash-001** (run 06): 7.0 avg kept — **identical to baseline**, matching per-plan counts exactly across all 5 plans. This is the same model but with the new prompt, confirming the prompt change does not alter deduplication quality for this model.
- **claude-haiku-4-5** (run 07): 6.8 avg kept — very close to baseline, with 54.7% reduction. Appropriate use of `remove` (5% of decisions) for fully redundant duplicates.
- **gpt-oss-20b** (run 02): 7.2 avg kept, 52% reduction — close to baseline.
- **qwen3-30b-a3b** (run 04): 8.6 avg kept, 42.7% reduction — moderately over-conservative.
- **gpt-4o-mini** (run 05): 9.4 avg kept, 37.3% reduction — under-consolidating, keeps too many duplicates.
- **llama3.1** (run 01): 10.6 avg kept, 29.3% reduction — significantly under-consolidating. For the silo plan (15/15 kept) and hong_kong_game (15/15 kept), it classified every lever as `primary` without performing deduplication at all.
- **gpt-5-nano** (run 03): 5.0 avg kept, 66.7% reduction — over-aggressive consolidation, potentially discarding meaningful distinctions.

### C. Completeness and Lever Coverage

For plans where the baseline kept 7-8 levers, the following models matched closely:
- gemini-2.0-flash-001 matched baseline exactly on all 5 plans (same counts)
- claude-haiku-4-5 was within ±1 on 4/5 plans
- gpt-oss-20b was within ±1 on 3/5 plans

Models producing the same lever names and IDs as the baseline were preferred. Qualitative review shows:
- **gemini-2.0-flash-001** and **claude-haiku-4-5** produce justifications that explicitly cite lever IDs and explain hierarchy (e.g., "specific lever absorbed into more general lever"), matching the baseline's style
- **llama3.1** tends to classify nearly everything as `primary` without performing consolidation, indicating the model misunderstood the task (treating `primary` as equivalent to old `keep`)
- **gpt-5-nano** writes long justifications but over-consolidates, sometimes merging levers that should remain distinct
- **gpt-4o-mini** and **qwen3-30b-a3b** produce reasonable but verbose justifications with slightly too many kept levers

### D. Specificity of Justifications

Justification quality (by average length and specificity observed in samples):
- **claude-haiku-4-5** (699 avg chars): Highest quality — detailed, specific to the plan's context, cites plan-specific elements (e.g., HK$195 million P&A budget, HK$470 million production budget for hong_kong_game). Correctly distinguishes `secondary` levers like "Production Efficiency Optimization" and "Audience Engagement Strategy" as operational vs. strategic.
- **gpt-5-nano** (598 avg chars): Long but sometimes formulaic.
- **qwen3-30b-a3b** (525 avg chars): Good specificity, mentions lever IDs clearly.
- **gpt-4o-mini** (488 avg chars): Good but less specific to plan context.
- **gpt-oss-20b** (422 avg chars): Moderate, clear reasoning.
- **gemini-2.0-flash-001** (339 avg chars): Matches baseline quality closely, concise and accurate.
- **llama3.1** (295 avg chars): Short justifications, often generic ("directly impacts the project's success or failure").
- **Baseline** (283 avg chars): Reference benchmark.

### E. Secondary Classification Usage

The new `secondary` classification enables downstream prioritization. Two models stand out for meaningful use:
- **claude-haiku-4-5**: 23.5% secondary — actively distinguishes operational levers (e.g., "Production Efficiency Optimization", "Audience Engagement Strategy" in hong_kong_game correctly classified as secondary)
- **gpt-4o-mini**: 17.0% secondary — reasonable secondary usage
- Most other models (3-6%) are conservative with `secondary`, tending to default to `primary` for any lever they keep

---

## Model Ranking

1. **gemini-2.0-flash-001** (run 06) — Best match to baseline deduplication behavior. Identical lever counts to baseline on all 5 plans (7.0 avg). Correct new vocabulary, consistent reduction ratio (53.3%), appropriate justifications. Minor weakness: only 5.7% secondary classification, conservative use of the new feature.

2. **claude-haiku-4-5-pinned** (run 07) — Near-baseline reduction (6.8 avg, 54.7%). Best justification quality with plan-specific detail. Most sophisticated `secondary` classification usage (23.5%), correctly identifies operational vs. strategic levers. Uses `remove` appropriately for genuinely redundant duplicates (5%). Closest model to the intended design of PR #363.

3. **gpt-oss-20b** (run 02) — Close to baseline (7.2 avg, 52% reduction). Good deduplication, adequate justifications. Minimal `secondary` usage (5.6%).

4. **qwen3-30b-a3b** (run 04) — Moderate (8.6 avg, 42.7% reduction). Good justification quality. Slight over-retention but acceptable. Very low secondary usage (4.7%).

5. **gpt-4o-mini** (run 05) — Under-consolidating (9.4 avg, 37.3% reduction). Keeps too many near-duplicates. But reasonable `secondary` usage (17%) and good justification specificity.

6. **gpt-5-nano** (run 03) — Over-aggressive (5.0 avg, 66.7% reduction). Merges levers that should remain distinct, losing strategic nuance. Long justifications but over-consolidation is a quality concern.

7. **ollama-llama3.1** (run 01) — Worst performer (10.6 avg, 29.3% reduction). Failed to deduplicate on the silo and hong_kong_game plans (15/15 kept = no reduction). Appears to treat `primary` as equivalent to the old `keep` without understanding that deduplication is still required. Nearly zero `secondary` usage. Justifications are generic and do not reference specific lever IDs being compared.

---

## Overall Verdict

**MIXED**: The new `primary`/`secondary`/`absorb`/`remove` schema is universally adopted across all 7 models (100% schema compliance). However, model behavior on the deduplication task itself is highly variable:

- gemini-2.0-flash-001 performs equivalently to baseline (COMPARABLE)
- claude-haiku-4-5 and gpt-oss-20b perform close to baseline and add meaningful classification depth (COMPARABLE to BETTER)
- llama3.1 fails the core deduplication task (WORSE)
- gpt-5-nano over-consolidates aggressively (WORSE)
- gpt-4o-mini and qwen3-30b-a3b under-consolidate moderately (MIXED)

The `secondary` classification feature (the main new capability from PR #363) is only meaningfully used by claude-haiku-4-5 (23.5%) and gpt-4o-mini (17%). Most models default to `primary` for any kept lever.

---

## Recommendations

1. **Adopt gemini-2.0-flash-001 or claude-haiku-4-5 as reference models** for this step. gemini-2.0-flash-001 is the most consistent with baseline behavior; claude-haiku-4-5 best demonstrates the intent of PR #363's classification feature.

2. **Investigate llama3.1 failure mode**: The model treats `primary` as equivalent to the old `keep` and skips deduplication entirely on some plans. The prompt text needs to make the deduplication responsibility more explicit for this model, or llama3.1 should not be used for this step.

3. **Consider prompt refinement to encourage `secondary` usage**: Most models (5 of 7) assign `secondary` to fewer than 6% of kept levers. The intended design of PR #363 splits the `keep` label meaningfully, but most models effectively ignore this distinction. A few illustrative examples in the prompt (few-shot) could improve adoption.

4. **Monitor gpt-5-nano's over-consolidation**: At 5.0 avg kept levers (vs. baseline 7.0), this model may discard strategically important distinctions. Recommend a minimum kept lever threshold or stronger "prefer keep/primary over absorb" language in the prompt for this model.

5. **The `remove` classification** is used sparingly by claude-haiku-4-5 (5%) and gpt-oss-20b (1%), which is appropriate given the prompt instruction to "use this sparingly." Other models avoid it entirely, which is acceptable.

6. **Per-plan variance is high for qwen3-30b-a3b**: The sovereign_identity plan yielded only 3 kept levers (vs. baseline 5), while gta_game yielded 12 (vs. baseline 8). This suggests inconsistent consolidation aggressiveness across different domain types.
