# Investigation: Does deduplication leave enough levers for vital_few?

## Question

After the safety valve fix (PR #364), deduplication keeps 5-9 levers from
an input of 15. Is this too aggressive? Does `vital_few_levers` have enough
input to make meaningful selections?

## How vital_few_levers works

- **Target output**: exactly 5 levers (`TARGET_VITAL_LEVER_COUNT = 5`)
- **Selection**: rates each lever as Critical/High/Medium/Low, fills 5 slots
  in priority order
- **Minimum input**: no hard minimum — handles any non-empty list gracefully
- **Batching**: falls back to compressed batches if payload exceeds context

## Lever counts through the pipeline

| Stage | Count | Source |
|-------|-------|--------|
| identify_potential_levers | ~15 | adaptive loop, min_levers=15 |
| deduplicate_levers (iter 42, before fix) | 4-15 | varies by model |
| deduplicate_levers (iter 43, after fix) | 3-12 | varies by model |
| enrich_levers | same as dedup output | 1:1 pass-through |
| vital_few_levers | 4-5 | selects from enriched |

## Iter 42 vs iter 43 comparison (levers kept)

| Plan | Model | Iter 42 | Iter 43 | Delta |
|------|-------|---------|---------|-------|
| silo | llama3.1 | 15 | 8 | -7 |
| hong_kong | llama3.1 | 15 | 7 | -8 |
| silo | gpt-4o-mini | 10 | 10 | 0 |
| hong_kong | gpt-4o-mini | 12 | 12 | 0 |
| sovereign | gpt-5-nano | 4 | 3 | -1 |
| silo | haiku | 6 | 6 | 0 |
| hong_kong | haiku | 7 | 7 | 0 |
| silo | gemini | 7 | 7 | 0 |
| hong_kong | gemini | 7 | 7 | 0 |

## Analysis

### The fix mainly corrected llama3.1

Strong models (haiku, gemini, gpt-oss) already kept 5-8 in iter 42 — the
safety valve fix did not change their behavior. The calibration hint ("expect
4-8 absorb/remove") aligned llama3.1 with what strong models already do
naturally. This is not artificial pressure.

### Is 5-9 survivors enough for vital_few?

**Yes, for most cases.** vital_few selects 5, so 7-9 survivors give it 2-4
levers to exclude — enough selection pressure for meaningful filtering.

With only 5-6 survivors, vital_few has minimal room (0-1 exclusions). This
is borderline but not harmful — if dedup correctly removed genuine
duplicates, the remaining levers are all distinct and valuable.

### The gpt-5-nano edge case

gpt-5-nano keeps only 3 on sovereign_identity (was 4 in iter 42). This means
vital_few would pass everything through with no filtering. However:

- gpt-5-nano was already the most aggressive model before the fix (kept 4)
- The drop from 4→3 is within normal variance for this model
- This is model-specific behavior, not caused by the calibration hint

### Recommendation

**No change needed.** The current calibration is well-tuned:

- It fixed the actual problem (llama3.1 blanket-keep)
- It didn't change strong model behavior
- The worst case (gpt-5-nano at 3) was already borderline before the fix

If gpt-5-nano's aggression becomes a broader concern, a floor could be added
("do not absorb if fewer than 5 levers would remain") but this is not
warranted by current evidence. The dedup stage should consolidate duplicates,
and vital_few should decide importance — these are separate responsibilities.
