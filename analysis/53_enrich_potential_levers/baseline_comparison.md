# Baseline Comparison: enrich_potential_levers

## Overview

- **Step**: `enrich_potential_levers`
- **Baseline model**: google/gemini-2.0-flash-001 (used to produce training data)
- **Plans**: 20250321_silo, 20250329_gta_game, 20260308_sovereign_identity, 20260310_hong_kong_game, 20260311_parasomnia_research_unit
- **Runs analyzed**: 78–84 (run 79 failed entirely; 7 runs total, 6 with data)

---

## Success Rate

| Run | Model | Succeeded | Total | Success Rate | Notes |
|-----|-------|-----------|-------|-------------|-------|
| 78 | ollama-llama3.1 | 5 | 5 | 100% | — |
| 79 | openrouter-openai-gpt-oss-20b | 0 | 5 | 0% | All plans failed with "LLM batch interaction failed" or timeout |
| 80 | openai-gpt-5-nano | 5 | 5 | 100% | — |
| 81 | openrouter-qwen3-30b-a3b | 5 | 5 | 100% | — |
| 82 | openrouter-openai-gpt-4o-mini | 5 | 5 | 100% | — |
| 83 | openrouter-gemini-2.0-flash-001 | 5 | 5 | 100% | Same family as baseline model |
| 84 | anthropic-claude-haiku-4-5-pinned | 5 | 5 | 100% | — |

Run 79 (gpt-oss-20b) is excluded from quantitative comparison due to complete failure.

---

## Quantitative Comparison

Averages computed across all 5 plans per model (or 5/5 succeeded plans where applicable). Baseline uses the same 5 plans from `baseline/train/`.

| Metric | Baseline | llama3.1 | gpt-5-nano | qwen3-30b | gpt-4o-mini | gemini-2.0-flash | claude-haiku |
|--------|----------|----------|------------|-----------|-------------|-----------------|--------------|
| **Lever count (avg)** | 7.0 | 15.6 | 15.6 | 15.4 | 15.6 | 15.6 | 15.6 |
| **Option violations (non-3 options)** | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| **Name uniqueness ratio** | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| **Avg description length (chars)** | 484 | 385 | 664 | 382 | 513 | 481 | 576 |
| **Avg synergy_text length (chars)** | 287 | 374 | 343 | 199 | 269 | 290 | 451 |
| **Avg conflict_text length (chars)** | 300 | 384 | 344 | 220 | 286 | 308 | 484 |
| **Avg consequences length (chars)** | 275 | 339 | 339 | 339 | 339 | 339 | 339 |
| **Avg option description length (chars)** | 140 | 175 | 175 | 174 | 175 | 175 | 175 |
| **Template leakage detected** | No | No | Yes* | No | No | No | No |
| **Avg processing time (seconds/plan)** | — | 173.0 | 240.8 | 89.9 | 75.9 | 28.5 | 88.8 |

\* gpt-5-nano: one lever in the parasomnia plan references "option 1", "option 2", "option 3" by label within the description text (not actual placeholder template abuse, but a textual reference to option labels rather than their content).

**Key observations on lever count**: All experiment models produce approximately 15–16 levers per plan, roughly double the baseline's 7–8. This is expected because the baseline deduplicated aggressively to the most important levers, while the experiment models are receiving the full deduplicated-but-not-reduced lever list as input from the `deduplicate_levers` step (snapshot/1_deduplicate_levers). The lever count difference reflects input data differences, not model quality differences.

---

## Quality Assessment

### Option Compliance (3 options per lever)
All 6 successful models achieve **perfect compliance** (0 violations across all plans and levers). Every lever has exactly 3 options. This matches the baseline perfectly.

### Name Uniqueness
All models achieve a **perfect 1.000 uniqueness ratio** — no duplicate lever names within any plan output. This matches the baseline.

### Description Depth
- **claude-haiku** produces the longest descriptions (avg 576 chars), well above baseline (484). Synergy and conflict texts are also the richest (451 and 484 chars respectively, vs. baseline 287/300).
- **gpt-5-nano** produces very long descriptions (664 chars avg), substantially above baseline. Synergy and conflict texts are moderate.
- **gemini-2.0-flash** (same family as the baseline model) achieves near-identical description length (481 vs. 484 baseline) and nearly identical synergy/conflict lengths (290 vs. 287, 308 vs. 300). This is the closest match to baseline style.
- **gpt-4o-mini** produces slightly longer descriptions than baseline (513 vs. 484) with slightly shorter synergy/conflict texts (269/286 vs. 287/300). Close to baseline.
- **llama3.1** produces shorter descriptions (385 vs. 484) but longer synergy/conflict texts (374/384 vs. 287/300). Different stylistic balance.
- **qwen3-30b** produces the shortest descriptions (382 chars) with notably shorter synergy/conflict texts (199/220 vs. 287/300). The synergy/conflict sections are approximately 30% shorter than baseline.

### Consequences Field
All experiment models produce identical average consequences length (339 chars vs. baseline 275). This slight increase is uniform across all models, suggesting the input levers from the snapshot already had slightly longer consequences than the baseline training data.

### Option Text Length
All experiment models produce option text of approximately 175 chars on average, compared to 140 chars in the baseline. This 25% increase is uniform across all models, again suggesting this reflects the input data rather than model behavior.

### Template Leakage
No genuine template leakage detected. The gpt-5-nano "option 1/2/3" references are in descriptive prose referring to the options by ordinal number, not copied placeholder text. This is a minor stylistic issue, not a structural defect.

### Structural Completeness
All models produce the required fields: `lever_id`, `name`, `consequences`, `options`, `review`, `description`, `synergy_text`, `conflict_text`. The `deduplication_justification` and `classification` fields inherited from the deduplicate step are preserved.

---

## Model Ranking

Ranking is based on: description quality, synergy/conflict richness, option compliance, and overall alignment with baseline style.

1. **gemini-2.0-flash-001** — Near-perfect match to baseline style and length across all metrics. Zero violations, 100% success. As the same model family as the baseline, it demonstrates consistent behavior. Best for baseline fidelity.

2. **claude-haiku-4-5** — Richest descriptions and synergy/conflict texts of all models. Substantially more verbose than baseline but in a way that adds useful content (detailed synergies, multi-lever conflict analysis). Zero violations, 100% success.

3. **gpt-4o-mini** — Description length close to baseline, synergy/conflict slightly shorter. Clean output, no leakage, 100% success. Reliable and balanced.

4. **gpt-5-nano** — Excellent description depth but slightly verbose. Minor "option 1/2/3" reference in one plan's descriptions is a negligible stylistic quirk. 100% success but slowest among cloud models.

5. **llama3.1** — 100% success (local model). Shorter descriptions but richer synergy/conflict texts. Slower than most cloud models (173s avg) but fully capable. Output quality acceptable.

6. **qwen3-30b** — 100% success, fast (90s avg). However, synergy and conflict texts are noticeably shorter (199/220 vs. baseline 287/300). Descriptions are also below baseline. Structurally correct but depth is reduced.

7. **openrouter-openai-gpt-oss-20b** — **Excluded from ranking**: 0/5 success rate. Complete failure due to "LLM batch interaction failed" or timeout errors. Not viable for this step.

---

## Overall Verdict

**COMPARABLE / MIXED**: Most models produce structurally correct, high-quality output with zero option violations and perfect name uniqueness. The lever count difference (15–16 vs. 7–8 in baseline) is explained by input differences (the snapshot used contains more levers per plan than the baseline training data). gemini-2.0-flash shows baseline-identical quality, and claude-haiku and gpt-4o-mini are close. qwen3-30b is structurally correct but noticeably less detailed in synergy/conflict sections. The main failure case is gpt-oss-20b (complete failure, 0% success rate), which should be considered non-viable for this step.

---

## Recommendations

1. **Prefer gemini-2.0-flash or claude-haiku** for highest quality: gemini matches baseline style precisely; claude-haiku provides the richest enrichment overall.

2. **gpt-4o-mini is a strong cost-efficient choice**: 76s avg per plan, near-baseline quality, zero violations.

3. **Avoid gpt-oss-20b** for this step: it failed completely across all 5 plans. The errors suggest this model struggles with the batch interaction pattern used by the step.

4. **qwen3-30b** is fast but produces shallower synergy/conflict analysis (~30% shorter than baseline). Acceptable if speed is critical, but enrichment quality is reduced.

5. **llama3.1** is viable as a local/offline option. Output quality is acceptable though descriptions are shorter. Very slow (173s avg) for a local model.

6. **gpt-5-nano** produces verbose, high-quality descriptions but is the slowest cloud model (241s avg). The minor "option N" reference in descriptions is worth monitoring but is not a blocker.
