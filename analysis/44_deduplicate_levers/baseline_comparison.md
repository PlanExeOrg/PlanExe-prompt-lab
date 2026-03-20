# Baseline Comparison: deduplicate_levers (Iteration 44)

## Overview

Iteration 44 widens the calibration range to 4–10 absorb/remove (safety valve) in the system prompt. This comparison evaluates 7 models across 5 plans against the baseline (gemini-2.0-flash-001 running the full PlanExe pipeline with the old prompt format).

Note: The baseline uses the old prompt schema (`keep`/`absorb`/`remove`) — it has no `primary`/`secondary` distinction. The new prompt schema uses `primary`/`secondary`/`absorb`/`remove`. Deduped count (levers surviving deduplication) is the primary calibration metric.

Plans tested:
- 20250321_silo
- 20250329_gta_game
- 20260308_sovereign_identity
- 20260310_hong_kong_game
- 20260311_parasomnia_research_unit

---

## Success Rate

All 35 runs (7 models × 5 plans) completed successfully with status `ok`.

| Run | Model | Plans OK | Plans Failed |
|-----|-------|----------|--------------|
| 15 | ollama-llama3.1 | 5/5 | 0 |
| 16 | openrouter-openai-gpt-oss-20b | 5/5 | 0 |
| 17 | openai-gpt-5-nano | 5/5 | 0 |
| 18 | openrouter-qwen3-30b-a3b | 5/5 | 0 |
| 19 | openrouter-openai-gpt-4o-mini | 5/5 | 0 |
| 20 | openrouter-gemini-2.0-flash-001 | 5/5 | 0 |
| 21 | anthropic-claude-haiku-4-5-pinned | 5/5 | 0 |

---

## Quantitative Comparison

### Baseline (gold standard)

| Plan | Response | Absorb/Remove | Deduped | Keep |
|------|----------|--------------|---------|------|
| silo | 15 | 8 | 7 | 7 |
| gta_game | 15 | 7 | 8 | 8 |
| sovereign_identity | 15 | 10 | 5 | 5 |
| hong_kong_game | 15 | 8 | 7 | 7 |
| parasomnia_research_unit | 15 | 7 | 8 | 8 |
| **AVERAGE** | **15.0** | **8.0** | **7.0** | **7.0** |

### Run 15: ollama-llama3.1

| Plan | Response | Absorb/Remove | Deduped | Primary | Secondary |
|------|----------|--------------|---------|---------|-----------|
| silo | 15 | 6 | 9 | 9 | 0 |
| gta_game | 15 | 9 | 6 | 6 | 0 |
| sovereign_identity | 15 | 10 | 5 | 5 | 0 |
| hong_kong_game | 15 | 6 | 9 | 6 | 3 |
| parasomnia_research_unit | 15 | 8 | 7 | 3 | 4 |
| **AVERAGE** | **15.0** | **7.8** | **7.2** | **5.8** | **1.4** |

### Run 16: openrouter-openai-gpt-oss-20b

| Plan | Response | Absorb/Remove | Deduped | Primary | Secondary |
|------|----------|--------------|---------|---------|-----------|
| silo | 15 | 10 | 5 | 5 | 0 |
| gta_game | 15 | 8 | 7 | 7 | 0 |
| sovereign_identity | 15 | 11 | 4 | 4 | 0 |
| hong_kong_game | 15 | 8 | 7 | 5 | 2 |
| parasomnia_research_unit | 15 | 7 | 8 | 7 | 1 |
| **AVERAGE** | **15.0** | **8.8** | **6.2** | **5.6** | **0.6** |

### Run 17: openai-gpt-5-nano

| Plan | Response | Absorb/Remove | Deduped | Primary | Secondary |
|------|----------|--------------|---------|---------|-----------|
| silo | 15 | 8 | 7 | 7 | 0 |
| gta_game | 15 | 10 | 5 | 5 | 0 |
| sovereign_identity | 15 | 13 | 2 | 1 | 1 |
| hong_kong_game | 15 | 9 | 6 | 4 | 2 |
| parasomnia_research_unit | 15 | 8 | 7 | 5 | 2 |
| **AVERAGE** | **15.0** | **9.6** | **5.4** | **4.4** | **1.0** |

### Run 18: openrouter-qwen3-30b-a3b

| Plan | Response | Absorb/Remove | Deduped | Primary | Secondary |
|------|----------|--------------|---------|---------|-----------|
| silo | 15 | 8 | 7 | 7 | 0 |
| gta_game | 15 | 5 | 10 | 10 | 0 |
| sovereign_identity | 15 | 12 | 3 | 3 | 0 |
| hong_kong_game | 15 | 8 | 7 | 5 | 2 |
| parasomnia_research_unit | 15 | 7 | 8 | 8 | 0 |
| **AVERAGE** | **15.0** | **8.0** | **7.0** | **6.6** | **0.4** |

### Run 19: openrouter-openai-gpt-4o-mini

| Plan | Response | Absorb/Remove | Deduped | Primary | Secondary |
|------|----------|--------------|---------|---------|-----------|
| silo | 15 | 5 | 10 | 10 | 0 |
| gta_game | 15 | 6 | 9 | 8 | 1 |
| sovereign_identity | 15 | 10 | 5 | 4 | 1 |
| hong_kong_game | 15 | 6 | 9 | 6 | 3 |
| parasomnia_research_unit | 15 | 5 | 10 | 6 | 4 |
| **AVERAGE** | **15.0** | **6.4** | **8.6** | **6.8** | **1.8** |

### Run 20: openrouter-gemini-2.0-flash-001

| Plan | Response | Absorb/Remove | Deduped | Primary | Secondary |
|------|----------|--------------|---------|---------|-----------|
| silo | 15 | 8 | 7 | 7 | 0 |
| gta_game | 15 | 7 | 8 | 8 | 0 |
| sovereign_identity | 15 | 10 | 5 | 5 | 0 |
| hong_kong_game | 15 | 8 | 7 | 5 | 2 |
| parasomnia_research_unit | 15 | 7 | 8 | 1 | 7 |
| **AVERAGE** | **15.0** | **8.0** | **7.0** | **5.2** | **1.8** |

### Run 21: anthropic-claude-haiku-4-5-pinned

| Plan | Response | Absorb/Remove | Deduped | Primary | Secondary |
|------|----------|--------------|---------|---------|-----------|
| silo | 15 | 9 | 6 | 6 | 0 |
| gta_game | 15 | 8 | 7 | 6 | 1 |
| sovereign_identity | 15 | 10 | 5 | 4 | 1 |
| hong_kong_game | 15 | 8 | 7 | 5 | 2 |
| parasomnia_research_unit | 15 | 8 | 7 | 4 | 3 |
| **AVERAGE** | **15.0** | **8.6** | **6.4** | **5.0** | **1.4** |

### Summary table (averages across 5 plans)

| Model | Avg Deduped | Avg Absorb/Remove | Avg Primary | Avg Secondary | Delta Deduped vs Baseline |
|-------|-------------|-------------------|-------------|---------------|--------------------------|
| Baseline | 7.0 | 8.0 | N/A | N/A | — |
| ollama-llama3.1 | 7.2 | 7.8 | 5.8 | 1.4 | +0.2 |
| openrouter-openai-gpt-oss-20b | 6.2 | 8.8 | 5.6 | 0.6 | -0.8 |
| openai-gpt-5-nano | 5.4 | 9.6 | 4.4 | 1.0 | -1.6 |
| openrouter-qwen3-30b-a3b | 7.0 | 8.0 | 6.6 | 0.4 | 0.0 |
| openrouter-openai-gpt-4o-mini | 8.6 | 6.4 | 6.8 | 1.8 | +1.6 |
| openrouter-gemini-2.0-flash-001 | 7.0 | 8.0 | 5.2 | 1.8 | 0.0 |
| anthropic-claude-haiku-4-5-pinned | 6.4 | 8.6 | 5.0 | 1.4 | -0.6 |

---

## Quality Assessment

### ollama-llama3.1 (Run 15)
- Average deduped count of 7.2 is very close to baseline 7.0. Calibration is slightly loose.
- Most plans use only `primary` (no secondary). The parasomnia plan is an exception: 3 primary + 4 secondary, which is unusual — suggests mixed understanding of the primary/secondary distinction.
- silo: 9 deduped vs baseline 7 — slightly too conservative on absorbing.
- No major failure modes observed.

### openrouter-openai-gpt-oss-20b (Run 16)
- Average deduped 6.2 is below baseline 7.0. Model tends to over-absorb.
- sovereign_identity: only 4 deduped (vs baseline 5) — mild over-absorption.
- Nearly all kept levers classified as primary only (secondary=0.6 avg), suggesting weak use of the secondary tier.
- No catastrophic failures, but calibration skews toward aggressive absorption.

### openai-gpt-5-nano (Run 17)
- Average deduped 5.4 is significantly below baseline 7.0 — worst calibration of all models.
- sovereign_identity: only 2 deduped (13 absorbed/removed out of 15) — severe over-absorption. The justification text for this plan contained garbled/self-referential content, indicating the model struggled with structured JSON generation for this plan.
- gta_game: 5 deduped vs baseline 8 — also over-absorbed.
- Secondary usage minimal (avg 1.0), inconsistent primary/secondary split.
- This model is the weakest performer in this iteration.

### openrouter-qwen3-30b-a3b (Run 18)
- Average deduped 7.0 exactly matches baseline. Absorb/remove average also matches at 8.0.
- However, variance across plans is high: gta_game gets 10 deduped (only 5 absorbed, well below expected ~7), while sovereign_identity gets only 3 deduped (12 absorbed).
- gta_game calibration capping: only 5 absorb/remove when ~7 is expected — model stopped absorbing too soon.
- Very low secondary usage (avg 0.4) — model heavily favors primary.
- Mean matches baseline but per-plan variance is a concern.

### openrouter-openai-gpt-4o-mini (Run 19)
- Average deduped 8.6 is above baseline 7.0 — systematic under-absorption (calibration capping).
- silo: 10 deduped (only 5 absorb/remove, baseline was 8). parasomnia: 10 deduped (only 5 absorb/remove, baseline was 7).
- The model consistently stops absorbing before reaching the target range, leaving too many levers.
- sovereign_identity is the exception (5 deduped, matches baseline 5) — suggesting the model is plan-sensitive.
- Higher secondary usage (avg 1.8) indicates it does use the secondary tier when it does absorb.
- Overall: prompt's "4–10 absorb/remove" guidance is not binding enough for this model.

### openrouter-gemini-2.0-flash-001 (Run 20)
- Average deduped 7.0 and absorb/remove 8.0 match baseline exactly.
- 4 out of 5 plans are calibrated perfectly (deduped matches baseline).
- parasomnia_research_unit: blanket-secondary failure — 1 primary + 7 secondary (8 deduped total matches baseline 8, but the primary/secondary split is extreme). Model appears to have labeled nearly everything secondary rather than applying judgment.
- Best overall calibration among all 7 models on the deduped count metric.

### anthropic-claude-haiku-4-5-pinned (Run 21)
- Average deduped 6.4 is below baseline 7.0 — mild over-absorption.
- Results are consistent across plans (deduped: 6, 7, 5, 7, 7) with no extreme outliers.
- sovereign_identity deduped=5 matches baseline exactly.
- Secondary usage avg 1.4 indicates moderate use of the secondary tier.
- Reliable but slightly over-aggressive on absorption.

---

## Model Ranking

Ranked by closeness to baseline calibration (deduped=7.0, absorb_remove=8.0) and absence of failure modes:

| Rank | Model | Avg Deduped | Delta | Notes |
|------|-------|-------------|-------|-------|
| 1 | openrouter-gemini-2.0-flash-001 | 7.0 | 0.0 | Best calibration; one parasomnia blanket-secondary anomaly |
| 2 | openrouter-qwen3-30b-a3b | 7.0 | 0.0 | Exact average match; high per-plan variance |
| 3 | ollama-llama3.1 | 7.2 | +0.2 | Near-baseline; slightly loose; inconsistent secondary usage |
| 4 | anthropic-claude-haiku-4-5-pinned | 6.4 | -0.6 | Slightly over-absorbed; consistent, no severe outliers |
| 5 | openrouter-openai-gpt-oss-20b | 6.2 | -0.8 | Over-absorbs; minimal secondary tier usage |
| 6 | openrouter-openai-gpt-4o-mini | 8.6 | +1.6 | Calibration capping; under-absorbs in most plans |
| 7 | openai-gpt-5-nano | 5.4 | -1.6 | Severe over-absorption; sovereign_identity only 2 deduped; garbled output |

---

## Overall Verdict

The iteration 44 prompt (widened calibration range 4–10) achieves correct average calibration for 2 models (gemini-2.0-flash-001, qwen3-30b-a3b) with deduped=7.0 and absorb_remove=8.0 matching baseline exactly. Three additional models (llama3.1, haiku-4-5, gpt-oss-20b) are within ±1 of the target on average.

Two models exhibit systematic failure modes:
- **gpt-4o-mini**: Calibration capping — consistently stops absorbing too early, leaving ~8–10 levers instead of 7.
- **gpt-5-nano**: Over-absorption — absorbs too aggressively, with one catastrophic case (2 levers remaining). Also produced garbled structured output for one plan.

The new `primary`/`secondary` classification tier is working (all 35 runs use the new schema, no `keep` classifications appear), but the secondary tier is underused by most models (avg secondary 0.4–1.8 vs primary 4.4–6.8). gemini-2.0-flash-001's parasomnia plan shows an inverted primary/secondary ratio (1:7), indicating the distinction is not consistently understood.

---

## Recommendations

1. **gemini-2.0-flash-001 is the reference model** for this step — its calibration is near-perfect on 4/5 plans. The parasomnia blanket-secondary issue should be investigated (possibly a prompt wording issue with how secondary is defined).

2. **gpt-4o-mini needs tighter upper-bound guidance** — the "expect 4–10 absorb/remove" range may be too permissive. Consider adding explicit text like "aim to keep no more than 8 levers" or tightening the range to "5–9 absorb/remove".

3. **gpt-5-nano is not suitable** for this step in its current form. Severe over-absorption and garbled JSON output for sovereign_identity disqualify it. No tuning within this prompt framework is likely to fix the JSON generation issue.

4. **Primary/secondary clarity**: Most models use secondary sparingly. Consider adding an example or target ratio (e.g., "expect roughly 50–70% of kept levers to be primary"). The gemini parasomnia inversion suggests the current definition allows over-use of secondary.

5. **Per-plan variance**: qwen3-30b-a3b has perfect average calibration but high variance (3–10 deduped across plans). Average-matching is not sufficient — per-plan calibration consistency should be tracked in future iterations.
