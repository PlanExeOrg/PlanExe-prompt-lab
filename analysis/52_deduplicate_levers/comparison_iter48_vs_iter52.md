# Deduplicate Levers: Iteration 48 vs Iteration 52 Comparison

**Date**: 2026-03-21
**Step**: `deduplicate_levers`
**Input**: `snapshot/0_identify_potential_levers` (same for both iterations, 18 levers per plan)
**Plans**: 5 (silo, gta_game, sovereign_identity, hong_kong_game, parasomnia_research_unit)
**Models**: 7

| Attribute | Iteration 48 (PR baseline) | Iteration 52 (PR #375) |
|---|---|---|
| Classification scheme | keep / absorb / remove | primary / secondary / remove |
| Survived levers | keep only | primary + secondary |
| Architecture | 18 sequential LLM calls (one per lever) | 1 batch LLM call (all levers at once) |
| History runs | 3/43 through 3/49 | 3/71 through 3/77 |

---

## 1. Summary Table

| Model | Iter 48 avg kept | Iter 52 avg kept | Iter 48 avg removed | Iter 52 avg removed | Delta kept | Avg duration 48 | Avg duration 52 | Speedup |
|---|---|---|---|---|---|---|---|---|
| ollama-llama3.1 | 13.8 | 16.4 | 4.2 | 1.6 | +2.6 | 87.1s | 83.6s | 1.0x |
| openrouter-openai-gpt-oss-20b | 13.4 | 13.0 | 4.6 | 5.0 | -0.4 | 171.7s | 33.1s | 5.2x |
| openai-gpt-5-nano | 9.2 | 14.8 | 8.8 | 3.2 | +5.6 | 205.8s | 63.3s | 3.3x |
| openrouter-qwen3-30b-a3b | 15.2 | 17.0 | 2.8 | 1.0 | +1.8 | 256.8s | 41.3s | 6.2x |
| openrouter-openai-gpt-4o-mini | 16.2 | 16.6 | 1.8 | 1.4 | +0.4 | 48.1s | 27.9s | 1.7x |
| openrouter-gemini-2.0-flash-001 | 15.0 | 15.6 | 3.0 | 2.4 | +0.6 | 20.5s | 10.7s | 1.9x |
| anthropic-claude-haiku-4-5-pinned | 14.2 | 16.0 | 3.8 | 2.0 | +1.8 | 53.4s | 22.2s | 2.4x |
| **Overall average** | **13.9** | **15.6** | **4.1** | **2.4** | **+1.7** | **120.5s** | **40.3s** | **3.0x** |

---

## 2. Per-Model Breakdown

### ollama-llama3.1

**Iteration 48 (keep/absorb/remove):**

| Plan | keep | absorb | remove | Survived |
|---|---|---|---|---|
| silo | 15 | 3 | 0 | 15 |
| gta_game | 14 | 4 | 0 | 14 |
| sovereign_identity | 11 | 7 | 0 | 11 |
| hong_kong_game | 15 | 3 | 0 | 15 |
| parasomnia_research_unit | 14 | 4 | 0 | 14 |
| **Average** | **13.8** | **4.2** | **0.0** | **13.8** |

**Iteration 52 (primary/secondary/remove):**

| Plan | primary | secondary | remove | Survived |
|---|---|---|---|---|
| silo | 11 | 7 | 0 | 18 |
| gta_game | 5 | 10 | 3 | 15 |
| sovereign_identity | 7 | 8 | 3 | 15 |
| hong_kong_game | 18 | 0 | 0 | 18 |
| parasomnia_research_unit | 4 | 12 | 2 | 16 |
| **Average** | **9.0** | **7.4** | **1.6** | **16.4** |

Duration: 87.1s avg -> 83.6s avg (1.0x, minimal change -- local model, no parallelization benefit)

---

### openrouter-openai-gpt-oss-20b

**Iteration 48 (keep/absorb/remove):**

| Plan | keep | absorb | remove | Survived |
|---|---|---|---|---|
| silo | 11 | 7 | 0 | 11 |
| gta_game | 18 | 0 | 0 | 18 |
| sovereign_identity | 13 | 5 | 0 | 13 |
| hong_kong_game | 13 | 5 | 0 | 13 |
| parasomnia_research_unit | 12 | 6 | 0 | 12 |
| **Average** | **13.4** | **4.6** | **0.0** | **13.4** |

**Iteration 52 (primary/secondary/remove):**

| Plan | primary | secondary | remove | Survived |
|---|---|---|---|---|
| silo | 10 | 5 | 3 | 15 |
| gta_game | 11 | 2 | 5 | 13 |
| sovereign_identity | 7 | 2 | 9 | 9 |
| hong_kong_game | 11 | 4 | 3 | 15 |
| parasomnia_research_unit | 9 | 4 | 5 | 13 |
| **Average** | **9.6** | **3.4** | **5.0** | **13.0** |

Duration: 171.7s avg -> 33.1s avg (5.2x speedup)

Note: This model is the most aggressive remover in iter 52 (avg 5.0 removed). sovereign_identity saw 9 removals.

---

### openai-gpt-5-nano

**Iteration 48 (keep/absorb/remove):**

| Plan | keep | absorb | remove | Survived |
|---|---|---|---|---|
| silo | 9 | 9 | 0 | 9 |
| gta_game | 10 | 8 | 0 | 10 |
| sovereign_identity | 9 | 8 | 1 | 9 |
| hong_kong_game | 9 | 9 | 0 | 9 |
| parasomnia_research_unit | 9 | 9 | 0 | 9 |
| **Average** | **9.2** | **8.6** | **0.2** | **9.2** |

**Iteration 52 (primary/secondary/remove):**

| Plan | primary | secondary | remove | Survived |
|---|---|---|---|---|
| silo | 16 | 0 | 2 | 16 |
| gta_game | 11 | 7 | 0 | 18 |
| sovereign_identity | 10 | 7 | 1 | 17 |
| hong_kong_game | 11 | 2 | 5 | 13 |
| parasomnia_research_unit | 8 | 2 | 8 | 10 |
| **Average** | **11.2** | **3.6** | **3.2** | **14.8** |

Duration: 205.8s avg -> 63.3s avg (3.3x speedup)

Note: Biggest improvement in survival count. Iter 48 was excessively aggressive with absorb (avg 8.6), keeping only ~9 levers. Iter 52 keeps 14.8 on average.

---

### openrouter-qwen3-30b-a3b

**Iteration 48 (keep/absorb/remove):**

| Plan | keep | absorb | remove | Survived |
|---|---|---|---|---|
| silo | 16 | 2 | 0 | 16 |
| gta_game | 17 | 1 | 0 | 17 |
| sovereign_identity | 12 | 6 | 0 | 12 |
| hong_kong_game | 14 | 4 | 0 | 14 |
| parasomnia_research_unit | 17 | 1 | 0 | 17 |
| **Average** | **15.2** | **2.8** | **0.0** | **15.2** |

**Iteration 52 (primary/secondary/remove):**

| Plan | primary | secondary | remove | Survived |
|---|---|---|---|---|
| silo | 16 | 0 | 2 | 16 |
| gta_game | 12 | 6 | 0 | 18 |
| sovereign_identity | 12 | 6 | 0 | 18 |
| hong_kong_game | 14 | 1 | 3 | 15 |
| parasomnia_research_unit | 11 | 7 | 0 | 18 |
| **Average** | **13.0** | **4.0** | **1.0** | **17.0** |

Duration: 256.8s avg -> 41.3s avg (6.2x speedup -- largest speedup of any model)

---

### openrouter-openai-gpt-4o-mini

**Iteration 48 (keep/absorb/remove):**

| Plan | keep | absorb | remove | Survived |
|---|---|---|---|---|
| silo | 16 | 2 | 0 | 16 |
| gta_game | 18 | 0 | 0 | 18 |
| sovereign_identity | 16 | 2 | 0 | 16 |
| hong_kong_game | 14 | 4 | 0 | 14 |
| parasomnia_research_unit | 17 | 1 | 0 | 17 |
| **Average** | **16.2** | **1.8** | **0.0** | **16.2** |

**Iteration 52 (primary/secondary/remove):**

| Plan | primary | secondary | remove | Survived |
|---|---|---|---|---|
| silo | 7 | 8 | 3 | 15 |
| gta_game | 9 | 9 | 0 | 18 |
| sovereign_identity | 11 | 6 | 1 | 17 |
| hong_kong_game | 9 | 7 | 2 | 16 |
| parasomnia_research_unit | 4 | 13 | 1 | 17 |
| **Average** | **8.0** | **8.6** | **1.4** | **16.6** |

Duration: 48.1s avg -> 27.9s avg (1.7x speedup)

---

### openrouter-gemini-2.0-flash-001

**Iteration 48 (keep/absorb/remove):**

| Plan | keep | absorb | remove | Survived |
|---|---|---|---|---|
| silo | 14 | 4 | 0 | 14 |
| gta_game | 18 | 0 | 0 | 18 |
| sovereign_identity | 13 | 5 | 0 | 13 |
| hong_kong_game | 14 | 4 | 0 | 14 |
| parasomnia_research_unit | 16 | 2 | 0 | 16 |
| **Average** | **15.0** | **3.0** | **0.0** | **15.0** |

**Iteration 52 (primary/secondary/remove):**

| Plan | primary | secondary | remove | Survived |
|---|---|---|---|---|
| silo | 10 | 5 | 3 | 15 |
| gta_game | 6 | 10 | 2 | 16 |
| sovereign_identity | 4 | 10 | 4 | 14 |
| hong_kong_game | 5 | 10 | 3 | 15 |
| parasomnia_research_unit | 8 | 10 | 0 | 18 |
| **Average** | **6.6** | **9.0** | **2.4** | **15.6** |

Duration: 20.5s avg -> 10.7s avg (1.9x speedup)

Note: Gemini heavily favors "secondary" classification (avg 9.0), more than any other model.

---

### anthropic-claude-haiku-4-5-pinned

**Iteration 48 (keep/absorb/remove):**

| Plan | keep | absorb | remove | Survived |
|---|---|---|---|---|
| silo | 14 | 4 | 0 | 14 |
| gta_game | 17 | 1 | 0 | 17 |
| sovereign_identity | 13 | 5 | 0 | 13 |
| hong_kong_game | 11 | 6 | 1 | 11 |
| parasomnia_research_unit | 16 | 2 | 0 | 16 |
| **Average** | **14.2** | **3.6** | **0.2** | **14.2** |

**Iteration 52 (primary/secondary/remove):**

| Plan | primary | secondary | remove | Survived |
|---|---|---|---|---|
| silo | 10 | 6 | 2 | 16 |
| gta_game | 10 | 6 | 2 | 16 |
| sovereign_identity | 10 | 7 | 1 | 17 |
| hong_kong_game | 10 | 5 | 3 | 15 |
| parasomnia_research_unit | 7 | 9 | 2 | 16 |
| **Average** | **9.4** | **6.6** | **2.0** | **16.0** |

Duration: 53.4s avg -> 22.2s avg (2.4x speedup)

Note: Very consistent -- primary count is almost always 10. Most balanced use of primary/secondary across models.

---

## 3. Architecture Comparison: Duration per Model per Plan

### Duration in seconds (Iter 48 -> Iter 52)

| Model | silo | gta_game | sovereign_id | hong_kong | parasomnia | Avg 48 | Avg 52 | Speedup |
|---|---|---|---|---|---|---|---|---|
| ollama-llama3.1 | 100.6 -> 114.8 | 104.2 -> 68.6 | 80.6 -> 70.5 | 74.8 -> 92.5 | 75.6 -> 71.9 | 87.1 | 83.6 | 1.0x |
| gpt-oss-20b | 268.8 -> 31.2 | 92.7 -> 25.2 | 205.4 -> 86.8 | 113.2 -> 13.5 | 178.3 -> 8.9 | 171.7 | 33.1 | **5.2x** |
| gpt-5-nano | 237.2 -> 61.6 | 180.3 -> 44.7 | 222.5 -> 73.8 | 217.2 -> 59.7 | 172.0 -> 76.8 | 205.8 | 63.3 | **3.3x** |
| qwen3-30b-a3b | 259.1 -> 33.8 | 215.1 -> 53.0 | 306.3 -> 32.3 | 296.4 -> 37.5 | 207.2 -> 50.0 | 256.8 | 41.3 | **6.2x** |
| gpt-4o-mini | 52.3 -> 22.0 | 43.6 -> 29.4 | 41.3 -> 30.7 | 50.3 -> 27.2 | 52.9 -> 30.3 | 48.1 | 27.9 | **1.7x** |
| gemini-2.0-flash | 20.3 -> 12.0 | 19.9 -> 11.7 | 19.5 -> 10.5 | 21.4 -> 10.2 | 21.4 -> 9.0 | 20.5 | 10.7 | **1.9x** |
| claude-haiku-4.5 | 44.7 -> 19.8 | 50.8 -> 21.0 | 56.4 -> 22.7 | 54.7 -> 22.8 | 60.3 -> 25.0 | 53.4 | 22.2 | **2.4x** |

**Key observations on speed:**
- The batch approach (1 call) is universally faster than 18 sequential calls.
- Models that were slowest per-call (qwen3, gpt-oss-20b, gpt-5-nano) benefit the most: 3.3x-6.2x speedup.
- ollama-llama3.1 shows negligible speedup (1.0x) because it runs locally with workers=1 -- a single large prompt may be comparable to 18 small prompts on local inference.
- Already-fast models (gemini-flash, gpt-4o-mini, claude-haiku) still gain 1.7x-2.4x.
- Total wall-clock time across all 35 plan-model combos: 4,219s (iter 48) -> 1,411s (iter 52), saving 2,808s (47 minutes).

---

## 4. Classification Distribution in Iteration 52

### Aggregate across all 7 models x 5 plans = 35 runs (630 total lever classifications)

| Classification | Count | Percentage |
|---|---|---|
| primary | 340 | 54.0% |
| secondary | 195 | 31.0% |
| remove | 95 | 15.1% |

### Per-model distribution (totals across 5 plans, 90 levers each)

| Model | primary | secondary | remove | % primary | % secondary | % remove |
|---|---|---|---|---|---|---|
| ollama-llama3.1 | 45 | 37 | 8 | 50.0% | 41.1% | 8.9% |
| gpt-oss-20b | 48 | 17 | 25 | 53.3% | 18.9% | 27.8% |
| gpt-5-nano | 56 | 18 | 16 | 62.2% | 20.0% | 17.8% |
| qwen3-30b-a3b | 65 | 20 | 5 | 72.2% | 22.2% | 5.6% |
| gpt-4o-mini | 40 | 43 | 7 | 44.4% | 47.8% | 7.8% |
| gemini-2.0-flash | 33 | 45 | 12 | 36.7% | 50.0% | 13.3% |
| claude-haiku-4.5 | 47 | 33 | 10 | 52.2% | 36.7% | 11.1% |

**Distribution patterns:**
- **qwen3-30b-a3b**: Most conservative remover (5.6% remove), strongly favors "primary" (72.2%)
- **gpt-oss-20b**: Most aggressive remover (27.8% remove), lowest secondary usage (18.9%)
- **gemini-2.0-flash**: Highest secondary usage (50.0%), lowest primary (36.7%) -- prefers to downgrade rather than remove
- **gpt-4o-mini**: Nearly equal primary/secondary split (44.4%/47.8%), very few removals (7.8%)
- **claude-haiku-4.5**: Most balanced across all three categories

---

## 5. Key Observations

### What improved

1. **Speed is dramatically better.** The single-batch architecture delivers a 3.0x average speedup across all models. Slowest models benefit most (qwen3: 6.2x, gpt-oss-20b: 5.2x). Total processing time drops from ~70 minutes to ~24 minutes across all 35 runs.

2. **Lever survival rate increased.** Average survived levers rose from 13.9 to 15.6 (+1.7 levers, +12%). The primary/secondary scheme retains more information by keeping "secondary" levers that would have been "absorbed" (and lost) in iter 48.

3. **gpt-5-nano dramatically improved.** In iter 48, it aggressively absorbed levers (avg 8.6 absorb), keeping only 9.2 of 18. In iter 52, it keeps 14.8 -- a +5.6 improvement, the largest single-model gain.

4. **Richer classification signal.** The primary/secondary distinction provides a priority ranking that downstream steps can use, whereas keep/absorb was binary (you either survived or you didn't).

### What regressed or stayed flat

1. **gpt-oss-20b survival slightly decreased** (-0.4 levers). It is the most aggressive remover in iter 52 (27.8% remove rate), particularly on sovereign_identity (9 of 18 removed). This model may need guardrails or a higher threshold for removal.

2. **ollama-llama3.1 saw no speed improvement** (1.0x). Expected for a local model with workers=1 -- the bottleneck is inference throughput, not call overhead.

3. **Higher variance in iter 52.** Some models keep 18/18 for certain plans (qwen3 on 3 plans, llama3.1 on 2 plans) while removing aggressively on others. Iter 48 was more uniformly conservative.

### Overall verdict

**Iteration 52 is a clear improvement.** The batch architecture delivers substantial speed gains (3.0x overall) while preserving more levers (+12% survival rate). The primary/secondary classification adds useful granularity. The only concern is model-specific variance in removal aggressiveness (especially gpt-oss-20b), which could be addressed with prompt tuning or post-hoc validation.

---

## Appendix: Data Sources

| Iteration | Run | Model | History Path |
|---|---|---|---|
| 48 | 3/43 | ollama-llama3.1 | `history/3/43_deduplicate_levers/` |
| 48 | 3/44 | openrouter-openai-gpt-oss-20b | `history/3/44_deduplicate_levers/` |
| 48 | 3/45 | openai-gpt-5-nano | `history/3/45_deduplicate_levers/` |
| 48 | 3/46 | openrouter-qwen3-30b-a3b | `history/3/46_deduplicate_levers/` |
| 48 | 3/47 | openrouter-openai-gpt-4o-mini | `history/3/47_deduplicate_levers/` |
| 48 | 3/48 | openrouter-gemini-2.0-flash-001 | `history/3/48_deduplicate_levers/` |
| 48 | 3/49 | anthropic-claude-haiku-4-5-pinned | `history/3/49_deduplicate_levers/` |
| 52 | 3/71 | ollama-llama3.1 | `history/3/71_deduplicate_levers/` |
| 52 | 3/72 | openrouter-openai-gpt-oss-20b | `history/3/72_deduplicate_levers/` |
| 52 | 3/73 | openai-gpt-5-nano | `history/3/73_deduplicate_levers/` |
| 52 | 3/74 | openrouter-qwen3-30b-a3b | `history/3/74_deduplicate_levers/` |
| 52 | 3/75 | openrouter-openai-gpt-4o-mini | `history/3/75_deduplicate_levers/` |
| 52 | 3/76 | openrouter-gemini-2.0-flash-001 | `history/3/76_deduplicate_levers/` |
| 52 | 3/77 | anthropic-claude-haiku-4-5-pinned | `history/3/77_deduplicate_levers/` |

Output files per plan: `outputs/{plan_name}/002-11-deduplicated_levers_raw.json`
Duration data: `events.jsonl` (`run_single_plan_complete` events)
