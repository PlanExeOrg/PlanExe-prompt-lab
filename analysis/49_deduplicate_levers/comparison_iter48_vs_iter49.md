# Comparison: Iteration 48 vs Iteration 49 -- deduplicate_levers

**Date**: 2026-03-20

**Iter 48** (main baseline): keep / absorb / remove taxonomy  
**Iter 49** (PR #372): primary / secondary / remove taxonomy

All plans have 18 input levers. Each model processed all 5 plans in both iterations.

---

## 1. Summary Table

Average counts across 5 plans per model (all plans have 18 input levers).

| Model | Iter48 avg kept | Iter49 avg kept | Iter48 avg removed | Iter49 avg removed | Delta kept |
|-------|----------------:|----------------:|-------------------:|-------------------:|-----------:|
| llama3.1 | 13.8 | 16.6 | 4.2 | 1.4 | +2.8 |
| gpt-oss-20b | 13.4 | 15.0 | 4.6 | 3.0 | +1.6 |
| gpt-5-nano | 9.2 | 14.0 | 8.8 | 4.0 | +4.8 |
| qwen3-30b-a3b | 15.2 | 15.6 | 2.8 | 2.4 | +0.4 |
| gpt-4o-mini | 16.2 | 17.6 | 1.8 | 0.4 | +1.4 |
| gemini-2.0-flash | 15.0 | 15.0 | 3.0 | 3.0 | 0.0 |
| claude-haiku-4.5 | 14.2 | 13.2 | 3.8 | 4.8 | -1.0 |
| **ALL MODELS** | **13.9** | **15.3** | **4.1** | **2.7** | **+1.4** |

> "Kept" = levers in `deduplicated_levers` array (survived dedup).  
> "Removed" = 18 minus kept (levers that were absorbed or removed).

---

## 2. Per-Model Breakdown

Classification distribution across all 5 plans for each model in both iterations.

### llama3.1

**Iteration 48** (keep / absorb / remove)

| Plan | keep | absorb | remove | dedup_count |
|------|-----:|-------:|-------:|------------:|
| silo | 15 | 3 | 0 | 15 |
| gta_game | 14 | 4 | 0 | 14 |
| sovereign_id | 11 | 7 | 0 | 11 |
| hk_game | 15 | 3 | 0 | 15 |
| parasomnia | 14 | 4 | 0 | 14 |
| **Total** | **69** | **21** | **0** | **69** |

**Iteration 49** (primary / secondary / remove)

| Plan | primary | secondary | remove | dedup_count |
|------|--------:|----------:|-------:|------------:|
| silo | 17 | 1 | 0 | 18 |
| gta_game | 13 | 5 | 0 | 18 |
| sovereign_id | 2 | 16 | 0 | 18 |
| hk_game | 7 | 4 | 7 | 11 |
| parasomnia | 13 | 5 | 0 | 18 |
| **Total** | **52** | **31** | **7** | **83** |

### gpt-oss-20b

**Iteration 48** (keep / absorb / remove)

| Plan | keep | absorb | remove | dedup_count |
|------|-----:|-------:|-------:|------------:|
| silo | 11 | 7 | 0 | 11 |
| gta_game | 18 | 0 | 0 | 18 |
| sovereign_id | 13 | 5 | 0 | 13 |
| hk_game | 13 | 5 | 0 | 13 |
| parasomnia | 12 | 6 | 0 | 12 |
| **Total** | **67** | **23** | **0** | **67** |

**Iteration 49** (primary / secondary / remove)

| Plan | primary | secondary | remove | dedup_count |
|------|--------:|----------:|-------:|------------:|
| silo | 14 | 2 | 2 | 16 |
| gta_game | 15 | 3 | 0 | 18 |
| sovereign_id | 12 | 1 | 5 | 13 |
| hk_game | 12 | 1 | 5 | 13 |
| parasomnia | 13 | 2 | 3 | 15 |
| **Total** | **66** | **9** | **15** | **75** |

### gpt-5-nano

**Iteration 48** (keep / absorb / remove)

| Plan | keep | absorb | remove | dedup_count |
|------|-----:|-------:|-------:|------------:|
| silo | 9 | 9 | 0 | 9 |
| gta_game | 10 | 8 | 0 | 10 |
| sovereign_id | 9 | 8 | 1 | 9 |
| hk_game | 9 | 9 | 0 | 9 |
| parasomnia | 9 | 9 | 0 | 9 |
| **Total** | **46** | **43** | **1** | **46** |

**Iteration 49** (primary / secondary / remove)

| Plan | primary | secondary | remove | dedup_count |
|------|--------:|----------:|-------:|------------:|
| silo | 14 | 0 | 4 | 14 |
| gta_game | 14 | 4 | 0 | 18 |
| sovereign_id | 6 | 8 | 4 | 14 |
| hk_game | 8 | 4 | 6 | 12 |
| parasomnia | 5 | 7 | 6 | 12 |
| **Total** | **47** | **23** | **20** | **70** |

### qwen3-30b-a3b

**Iteration 48** (keep / absorb / remove)

| Plan | keep | absorb | remove | dedup_count |
|------|-----:|-------:|-------:|------------:|
| silo | 16 | 2 | 0 | 16 |
| gta_game | 17 | 1 | 0 | 17 |
| sovereign_id | 12 | 6 | 0 | 12 |
| hk_game | 14 | 4 | 0 | 14 |
| parasomnia | 17 | 1 | 0 | 17 |
| **Total** | **76** | **14** | **0** | **76** |

**Iteration 49** (primary / secondary / remove)

| Plan | primary | secondary | remove | dedup_count |
|------|--------:|----------:|-------:|------------:|
| silo | 17 | 1 | 0 | 18 |
| gta_game | 15 | 3 | 0 | 18 |
| sovereign_id | 2 | 11 | 5 | 13 |
| hk_game | 11 | 2 | 5 | 13 |
| parasomnia | 6 | 10 | 2 | 16 |
| **Total** | **51** | **27** | **12** | **78** |

### gpt-4o-mini

**Iteration 48** (keep / absorb / remove)

| Plan | keep | absorb | remove | dedup_count |
|------|-----:|-------:|-------:|------------:|
| silo | 16 | 2 | 0 | 16 |
| gta_game | 18 | 0 | 0 | 18 |
| sovereign_id | 16 | 2 | 0 | 16 |
| hk_game | 14 | 4 | 0 | 14 |
| parasomnia | 17 | 1 | 0 | 17 |
| **Total** | **81** | **9** | **0** | **81** |

**Iteration 49** (primary / secondary / remove)

| Plan | primary | secondary | remove | dedup_count |
|------|--------:|----------:|-------:|------------:|
| silo | 17 | 1 | 0 | 18 |
| gta_game | 12 | 6 | 0 | 18 |
| sovereign_id | 9 | 9 | 0 | 18 |
| hk_game | 13 | 3 | 2 | 16 |
| parasomnia | 12 | 6 | 0 | 18 |
| **Total** | **63** | **25** | **2** | **88** |

### gemini-2.0-flash

**Iteration 48** (keep / absorb / remove)

| Plan | keep | absorb | remove | dedup_count |
|------|-----:|-------:|-------:|------------:|
| silo | 14 | 4 | 0 | 14 |
| gta_game | 18 | 0 | 0 | 18 |
| sovereign_id | 13 | 5 | 0 | 13 |
| hk_game | 14 | 4 | 0 | 14 |
| parasomnia | 16 | 2 | 0 | 16 |
| **Total** | **75** | **15** | **0** | **75** |

**Iteration 49** (primary / secondary / remove)

| Plan | primary | secondary | remove | dedup_count |
|------|--------:|----------:|-------:|------------:|
| silo | 12 | 3 | 3 | 15 |
| gta_game | 14 | 4 | 0 | 18 |
| sovereign_id | 7 | 7 | 4 | 14 |
| hk_game | 4 | 7 | 7 | 11 |
| parasomnia | 4 | 13 | 1 | 17 |
| **Total** | **41** | **34** | **15** | **75** |

### claude-haiku-4.5

**Iteration 48** (keep / absorb / remove)

| Plan | keep | absorb | remove | dedup_count |
|------|-----:|-------:|-------:|------------:|
| silo | 14 | 4 | 0 | 14 |
| gta_game | 17 | 1 | 0 | 17 |
| sovereign_id | 13 | 5 | 0 | 13 |
| hk_game | 11 | 6 | 1 | 11 |
| parasomnia | 16 | 2 | 0 | 16 |
| **Total** | **71** | **18** | **1** | **71** |

**Iteration 49** (primary / secondary / remove)

| Plan | primary | secondary | remove | dedup_count |
|------|--------:|----------:|-------:|------------:|
| silo | 11 | 1 | 6 | 12 |
| gta_game | 11 | 6 | 1 | 17 |
| sovereign_id | 10 | 2 | 6 | 12 |
| hk_game | 8 | 3 | 7 | 11 |
| parasomnia | 7 | 7 | 4 | 14 |
| **Total** | **47** | **19** | **24** | **66** |

---

## 3. Absorb-Info Preservation Check

In iter 49 (primary/secondary/remove taxonomy), `remove` justifications should ideally cite
the `lever_id` (UUID) of the lever that absorbs the removed one, preserving the absorb relationship.

For comparison, iter 48 `absorb` justifications cited UUIDs 90% of the time (129/143).

| Model | Total removes | Removes citing UUID | Citation rate |
|-------|-------------:|--------------------:|--------------:|
| llama3.1 | 7 | 7 | 100% |
| gpt-oss-20b | 15 | 15 | 100% |
| gpt-5-nano | 20 | 16 | 80% |
| qwen3-30b-a3b | 12 | 1 | 8% |
| gpt-4o-mini | 2 | 2 | 100% |
| gemini-2.0-flash | 15 | 15 | 100% |
| claude-haiku-4.5 | 24 | 17 | 71% |
| **ALL MODELS** | **95** | **73** | **77%** |

**Notes on non-UUID citations:**
- gpt-5-nano: 4 of its non-UUID removes still reference the absorbing lever by short-id prefix (e.g., `4745854b`, `3d0270f9`) rather than full UUID.
- qwen3-30b-a3b: Only 1/12 removes cites a full UUID. Most reference the absorbing lever by bracketed short-id (e.g., `[0a7d8031]`) instead of full UUID. The absorb relationship is expressed but not in the expected format.
- claude-haiku-4.5: 17/24 cite full UUIDs. The 7 without UUID still describe the absorbing relationship in prose.

---

## 4. Classification Distribution in Iteration 49

How many primary vs secondary vs remove across all models and plans.

### Per-model totals (across 5 plans, 90 input levers each)

| Model | primary | secondary | remove | primary % | secondary % | remove % |
|-------|--------:|----------:|-------:|----------:|------------:|---------:|
| llama3.1 | 52 | 31 | 7 | 58% | 34% | 8% |
| gpt-oss-20b | 66 | 9 | 15 | 73% | 10% | 17% |
| gpt-5-nano | 47 | 23 | 20 | 52% | 26% | 22% |
| qwen3-30b-a3b | 51 | 27 | 12 | 57% | 30% | 13% |
| gpt-4o-mini | 63 | 25 | 2 | 70% | 28% | 2% |
| gemini-2.0-flash | 41 | 34 | 15 | 46% | 38% | 17% |
| claude-haiku-4.5 | 47 | 19 | 24 | 52% | 21% | 27% |
| **ALL** | **367** | **168** | **95** | **58%** | **27%** | **15%** |

### Per-plan totals (across 7 models, 126 input levers each)

| Plan | primary | secondary | remove | primary % | secondary % | remove % |
|------|--------:|----------:|-------:|----------:|------------:|---------:|
| silo | 102 | 9 | 15 | 81% | 7% | 12% |
| gta_game | 94 | 31 | 1 | 75% | 25% | 1% |
| sovereign_id | 48 | 54 | 24 | 38% | 43% | 19% |
| hk_game | 63 | 24 | 39 | 50% | 19% | 31% |
| parasomnia | 60 | 50 | 16 | 48% | 40% | 13% |

---

## 5. Per-Plan Kept Counts (side-by-side)

| Model | silo 48 | silo 49 | gta 48 | gta 49 | sov_id 48 | sov_id 49 | hk 48 | hk 49 | para 48 | para 49 |
|-------|--------:|--------:|-------:|-------:|----------:|----------:|------:|------:|--------:|--------:|
| llama3.1 | 15 | 18 | 14 | 18 | 11 | 18 | 15 | 11 | 14 | 18 |
| gpt-oss-20b | 11 | 16 | 18 | 18 | 13 | 13 | 13 | 13 | 12 | 15 |
| gpt-5-nano | 9 | 14 | 10 | 18 | 9 | 14 | 9 | 12 | 9 | 12 |
| qwen3-30b-a3b | 16 | 18 | 17 | 18 | 12 | 13 | 14 | 13 | 17 | 16 |
| gpt-4o-mini | 16 | 18 | 18 | 18 | 16 | 18 | 14 | 16 | 17 | 18 |
| gemini-2.0-flash | 14 | 15 | 18 | 18 | 13 | 14 | 14 | 11 | 16 | 17 |
| claude-haiku-4.5 | 14 | 12 | 17 | 17 | 13 | 12 | 11 | 11 | 16 | 14 |

---

## 6. Key Observations

### Model-level changes (avg kept levers, iter48 -> iter49)

- **llama3.1**: 13.8 -> 16.6 (+2.8) -- REGRESSED (kept more, less dedup)
- **gpt-oss-20b**: 13.4 -> 15.0 (+1.6) -- REGRESSED (kept more, less dedup)
- **gpt-5-nano**: 9.2 -> 14.0 (+4.8) -- REGRESSED (kept more, less dedup)
- **qwen3-30b-a3b**: 15.2 -> 15.6 (+0.4) -- REGRESSED (kept more, less dedup)
- **gpt-4o-mini**: 16.2 -> 17.6 (+1.4) -- REGRESSED (kept more, less dedup)
- **gemini-2.0-flash**: 15.0 -> 15.0 (0.0) -- UNCHANGED
- **claude-haiku-4.5**: 14.2 -> 13.2 (-1.0) -- IMPROVED (kept fewer, more dedup)

### Overall

- **Grand average kept**: 13.9 (iter48) -> 15.3 (iter49), delta +1.4
- The primary/secondary/remove taxonomy **retains more levers** on average than keep/absorb/remove.
  This is because `secondary` levers are kept in `deduplicated_levers` (they survived), whereas
  `absorb` levers in iter48 were removed from the final list.

### Taxonomy shift analysis

- **Iter 48 classification totals** (630 lever decisions): keep=485, absorb=143, remove=2
- **Iter 49 classification totals** (630 lever decisions): primary=367, secondary=168, remove=95

- Iter 48 removed from dedup list (absorb+remove): **145** (23% of 630)
- Iter 49 removed from dedup list (remove only): **95** (15% of 630)
- Net change: -50 fewer removals (34% reduction in removals)

This confirms that the taxonomy change has a major structural effect: levers that were previously
`absorb` (removed from final list) are now split between `secondary` (kept) and `remove` (removed).
Of the 263 levers classified as secondary or remove in iter 49,
168 (64%) became secondary (kept) and 95 (36%) became remove (dropped).

### Absorb-info preservation verdict

- **76.8%** (73/95) of iter 49 `remove` justifications cite a full UUID of the absorbing lever.
- This compares to **90%** (129/143) UUID citation rate for `absorb` justifications in iter 48.
- The gap is primarily driven by **qwen3-30b-a3b** (8% UUID rate) which uses short-id bracket notation instead.
- Excluding qwen3-30b-a3b, the remaining 6 models achieve **86.7%** (72/83) UUID citation rate, close to iter 48's 90%.
- Absorb-info is largely preserved in the new taxonomy, but the prompt may benefit from stronger
  guidance to always include the full `lever_id` UUID in remove justifications.

### Model-specific notes

- **gpt-4o-mini**: Barely uses `remove` at all in iter 49 (only 2/90 levers). Nearly everything is primary or secondary. This model's dedup behavior is very conservative under both taxonomies.
- **llama3.1**: Zero removes in iter 48 (no absorb-to-remove at all). In iter 49, it only removes in one plan (hk_game: 7 removes). Highly plan-dependent.
- **gpt-5-nano**: Most aggressive deduplicator in both iterations. Iter 48 avg kept: 9.2. Iter 49 avg kept: 14.0. The taxonomy change significantly increased its kept count.
- **claude-haiku-4.5**: Most removes in iter 49 (24/90 = 27%). Also the most aggressive deduplicator in iter 49, keeping the fewest levers on average (13.2).
- **gemini-2.0-flash**: Strong UUID compliance (100%) but highly variable dedup across plans (11 to 18 kept).
- **qwen3-30b-a3b**: Uses short-id bracket notation instead of full UUIDs. May need prompt adjustment to enforce full UUID format.

### Verdict

The primary/secondary/remove taxonomy in iter 49 **preserves more levers** (avg 15.3 vs 13.9 kept).
This is the expected structural effect: `secondary` levers survive dedup, unlike `absorb` levers in iter 48.
Whether this is desirable depends on downstream step requirements. If more granular lever lists are preferred,
iter 49 delivers. If tighter dedup is the goal, the `remove` threshold may need tightening.

Absorb-info (which lever absorbs which) is mostly preserved via UUID citations in remove justifications,
at 77% overall (87% excluding the qwen3 outlier). This is a slight regression from iter 48's 90%,
addressable with minor prompt refinement.
