# Insight Claude

## Overview

This analysis evaluates **PR #453** ("Adaptive batch size, guarded retry, and max_tokens bump
for enrich step") against the baseline established in analysis 54 (PR #451, before) and analysis
55 (PR #452, before).

**Critical caveat — input data changed**: Analysis 56 uses `"input": "baseline/train"` (35
deduplicated levers across 5 plans, 5–8 per plan), while analyses 54 and 55 used
`"input": "snapshot/1_deduplicate_levers"` (78 levers, 14–18 per plan). This violates the
cross-experiment comparison prerequisite: the same input data must be used for valid comparison.
Per-lever field length averages remain comparable, but lever counts, batch counts, and total
throughput metrics are confounded. All comparisons involving lever counts must be treated as
approximate.

**Runs compared**:

| Model | "Before" (analysis 54) | "Before" (analysis 55) | "After" (analysis 56) |
|-------|------------------------|------------------------|----------------------|
| ollama-llama3.1 | `3/85` | `3/92` | `3/99` |
| openrouter-gpt-oss-20b | `3/86` | `3/93` | `4/00` |
| openai-gpt-5-nano | `3/87` | `3/94` | `4/01` |
| openrouter-qwen3-30b-a3b | `3/88` | `3/95` | `4/02` |
| openrouter-gpt-4o-mini | `3/89` | `3/97` | `4/03` |
| openrouter-gemini-2.0-flash-001 | `3/90` | `3/96` | `4/04` |
| anthropic-claude-haiku-4-5-pinned | `3/91` | `3/98` | `4/05` |

---

## Negative Things

### N1 — C1/C2 interaction bug: max_tokens bump disables adaptive batch for gpt-oss-20b

The PR's two most important changes for gpt-oss-20b conflict with each other:

- **C1** bumps `max_tokens` for gpt-oss-20b from 8192 → 128000 in `baseline.json`. This changes
  the LlamaIndex `num_output` metadata from 8192 to 128000.
- **C2** triggers `batch_size=2` when `num_output < SMALL_OUTPUT_THRESHOLD (16384)`. Since
  C1 raises `num_output` to 128000, the check `128000 < 16384` is `False` — C2 does **not**
  trigger for gpt-oss-20b.

The stated intent of C2 was to help gpt-oss-20b avoid output overflow with smaller batches.
But C1 silently disables C2 for exactly the model it was meant to help. The correct condition
would check `context_window` (which remains 3900 for gpt-oss-20b via OpenRouter metadata) rather
than `num_output` (which is the LlamaIndex max_tokens setting, inflated by C1).

Evidence: `history/4/00_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json`
metadata shows `"context_window": 3900, "num_output": 128000`. BATCH_SIZE=5 is used for all
gpt-oss-20b batches.

C2 code location: `enrich_potential_levers.py:175–185`.

### N2 — gpt-oss-20b still fails 3/5 plans (new failure mode: empty_response)

After PR #453, gpt-oss-20b still fails 3/5 plans. The failure mode changed:

- **Before (PR #452)**: Retry cascade → 3 plans × 600s timeout = 1800s wasted
- **After (PR #453)**: All batches return `empty_response` instantly → 3 plans × <2s = <6s

The 3 failing plans (sovereign_identity, hong_kong_game, parasomnia) consistently return
`empty_response` from every OpenRouter provider attempted. This happens in <1s per call —
much faster than the old timeout pattern. The guarded retry (B4) does run: sovereign_identity
shows 3 calls (1 original batch + 2 sub-batches from depth=1 split), hong_kong_game and
parasomnia show 6 calls each (2 original batches × (1+2 sub-batches)). All return empty_response.

The 2 succeeding plans (gta_game, silo) were routed by OpenRouter to providers that work
(Parasail, Amazon Bedrock, Nebius, Chutes) and produce correct output.

Evidence:
- `history/4/00_enrich_potential_levers/outputs/20260308_sovereign_identity/usage_metrics.jsonl`:
  3 calls, all `"error": "empty_response"`, sub-second each
- `history/4/00_enrich_potential_levers/outputs/20250321_silo/usage_metrics.jsonl`:
  2 successes — Nebius (1697→3173 output tokens, 29s) and Chutes (2280→5108 output tokens, 437s)

This failure is consistent with the `context_window=3900` limitation at certain OpenRouter
providers: when max_tokens=128000 >> context_window=3900, providers that enforce the actual
model limit may reject the request outright.

### N3 — UUID fix (C3) not implemented

PR #453 does not include the C3 fix (`f"- {lever.name}"` at line 190 instead of
`f"- {lever.lever_id}: {lever.name}"`). The code at line 190 still reads:

```python
full_lever_context_str = "\n".join([f"- {lever.lever_id}: {lever.name}" for lever in levers_to_characterize])
```

This causes llama3.1 to emit full UUIDs in 31/35 levers' synergy/conflict fields (89% rate).
Gemini shows moderate UUID contamination (12/35, 34%), though this rate is stochastic (analysis
54 run 90 showed 25/77 = 32%; analysis 55 run 96 showed 0/78 — wide variance).

Evidence: `history/3/99_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json`
— synergy_text for "Social Control Mechanism" contains
`"(5ac097c7-3b02-4b07-af35-c5d11d3b9029)"`.

### N4 — OPTIMIZE_INSTRUCTIONS updates already present in PR #452

The PR description claims to document "consequence-echoing and UUID format inconsistency as
known problems" in OPTIMIZE_INSTRUCTIONS. However, analysis 55 confirmed both entries were
already added by PR #452 (see `OPTIMIZE_INSTRUCTIONS` lines 82–92 in the current source).
The PR description appears to be repeating the D5 credit from PR #452, not documenting a
new contribution. This is harmless but misleading for audit purposes.

### N5 — Accurate batch counting was already fixed in PR #452

The PR description includes "Accurate batch counting: Report actual `batches_succeeded` instead
of hardcoded `1`" as D5. Analysis 55 confirmed this was fixed by PR #452 (runs 92–98 showed
`calls_succeeded: 3–5` reflecting actual batch counts). The current runs continue this
behaviour correctly.

---

## Positive Things

### P1 — Guarded retry eliminates 1800s of wasted runner time

The most impactful change: `MAX_RETRY_DEPTH=1, MAX_RETRY_BUDGET_SECONDS=300` in the retry
handler (lines 98–100, 262–266) prevents the unbounded retry cascade that caused 3×600s
timeouts in PR #452.

Observed timing improvement for gpt-oss-20b:
- PR #452 (analysis 55): 3 plans timeout at exactly 600s each → 1800s total wasted
- PR #453 (current): 3 plans fail in <2s each → <6s total wasted

Runner total time for gpt-oss-20b:
- PR #452: silo (195s) + gta_game (229s) + 3×600s = ~2224s
- PR #453: silo (466s) + gta_game (48.5s) + 3×<2s = ~520s

This is a 4.3× reduction in runner time for gpt-oss-20b, despite the same 2/5 functional
success rate. The silo plan took longer (466s vs 195s) due to the Chutes provider being slow,
but this is within the time budget and produces correct output.

Evidence: `history/4/00_enrich_potential_levers/events.jsonl` and
`history/3/93_enrich_potential_levers/outputs.jsonl`.

### P2 — max_tokens bump restores gpt-oss-20b content quality for 2 plans

For the 2 plans that succeed (gta_game and silo), the enriched content is now complete and
well-formed. Output tokens per batch:
- gta_game: 7924 tokens (Parasail) + 5957 tokens (Amazon Bedrock)
- silo: 5108 tokens (Nebius) + 3173 tokens (Chutes)

Before the max_tokens bump, output was truncated at exactly 8192 tokens per batch, producing
malformed JSON. Now the full structured JSON is generated even for verbose models. Field
lengths for gpt-oss-20b are in the 1.29–1.36× range — within acceptable bounds and
comparable to other capable models.

Evidence: `history/4/00_enrich_potential_levers/outputs/20250321_silo/usage_metrics.jsonl`
and `history/4/00_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json`
(7 well-formed levers with full description + synergy + conflict).

### P3 — C2 adaptive batch size works for other models (gemini, haiku, qwen3-30b, gpt-4o-mini)

For the 4 OpenRouter models with `num_output=8192 < 16384`, C2 correctly triggers
`batch_size=2`. With the small baseline/train input (5–8 levers per plan), this means 3–4
batches per plan instead of 1–2. All 4 models produce `calls_succeeded` of 3–4 per plan,
confirming complete enrichment. No truncation issues observed.

The smaller batches also produce more focused synergy/conflict text, which may reduce the
UUID contamination rate for qwen3-30b (2/35 = 6%) compared to run 95 (which showed higher
rates in some plans).

### P4 — llama3.1 description length continues improving (0.76×)

llama3.1's average description length improved from 0.65× (analysis 54) → 0.70× (analysis 55)
→ 0.76× baseline (current). The consequence-echoing pattern is less dominant than in analysis
54. Sample from `history/3/99_enrich_potential_levers/outputs/20250321_silo/`:
"Social Control Mechanism controls the order and structure of society within the silo,
balancing compliance with innovation and creativity." — this is grounded and non-template,
though still shorter than baseline (263 chars vs 504 chars baseline).

The trend is positive but llama3.1 remains below the ideal 1.0× target.

### P5 — No LLMChatError / Pydantic validation failures

None of the current runs show LLMChatError entries in events.jsonl. The schema validation
that previously discarded entire batches is not a problem here. The only failure mode is
`empty_response` from OpenRouter providers for gpt-oss-20b, which is a provider-level
rejection rather than a schema validation issue.

---

## Comparison

### Analysis 54 (PR #451) → Analysis 56 (PR #453)

Note: different input data (snapshot vs baseline/train); per-lever averages are comparable.

| Model | Success rate | Avg desc length | vs baseline | UUID rate |
|-------|-------------|-----------------|-------------|-----------|
| llama3.1 (run 85) | 5/5 | 316 | 0.65× | 75/78 (96%) |
| llama3.1 (run 99) | 5/5 | 370 | **0.76×** | 31/35 (89%) |
| gpt-oss-20b (run 86) | 0/5 errors | 540 | 1.11× | 5/14 (36%) |
| gpt-oss-20b (run 4/00) | 2/5 enriched | 660 | **1.36×** | 8/15 (53%) |
| gpt-5-nano (run 87) | 5/5 | 658 | 1.36× | 3/78 (4%) |
| gpt-5-nano (run 4/01) | 5/5 | 682 | **1.41×** | 0/34 (0%) |
| qwen3-30b (run 88) | 5/5 | 372 | 0.77× | 23/78 (29%) |
| qwen3-30b (run 4/02) | 5/5 | 466 | **0.96×** | 2/35 (6%) |
| gpt-4o-mini (run 89) | 5/5 | 482 | 1.00× | 0/78 (0%) |
| gpt-4o-mini (run 4/03) | 5/5 | 549 | **1.13×** | 0/35 (0%) |
| gemini (run 90) | 5/5 | 456 | 0.94× | 25/77 (32%) |
| gemini (run 4/04) | 5/5 | 540 | **1.12×** | 12/35 (34%) |
| haiku (run 91) | 5/5 | 568 | 1.17× | 5/78 (6%) |
| haiku (run 4/05) | 5/5 | 604 | **1.25×** | 1/35 (3%) |

### Analysis 55 (PR #452) → Analysis 56 (PR #453)

| Metric | PR #452 (runs 92–98) | PR #453 (runs 99, 4/00–4/05) | Change |
|--------|---------------------|------------------------------|--------|
| gpt-oss-20b success | 2/5 (3×600s timeout) | 2/5 (3×<2s fast-fail) | **IMPROVED: timeout → fast-fail** |
| Other models success | 30/30 (100%) | 30/30 (100%) | UNCHANGED |
| gpt-oss-20b runner time | ~2224s | ~520s | **IMPROVED (4.3×)** |
| llama3.1 desc length | 339 (0.70×) | 370 (0.76×) | IMPROVED |
| qwen3-30b desc length | 375 (0.78×) | 466 (0.96×) | IMPROVED (confounded by input change) |
| gemini desc length | 456 (0.94×) | 540 (1.12×) | IMPROVED (confounded by input change) |
| UUID rate (llama3.1) | ~75/78 (96%) | 31/35 (89%) | MARGINAL IMPROVEMENT (noise) |
| Fabricated % claims | 0 | 36/209 (17%) | APPARENT INCREASE (echoed from consequences) |
| LLMChatError count | 0 | 0 | UNCHANGED |

**Note on fabricated % claims**: The 36 percentage claims in descriptions are echoes of
numbers in the input `consequences` field (e.g., "30% reduction" from the lever's own
consequences text), not newly fabricated values. They appear in the `description` field,
which echoes consequence data — a form of consequence echoing documented in
OPTIMIZE_INSTRUCTIONS.

---

## Quantitative Metrics

### Success Rates

| Model | PR #452 (status) | PR #453 (status) | PR #453 (functional) |
|-------|-----------------|-----------------|----------------------|
| llama3.1 | 5/5 ok | 5/5 ok | 5/5 (35 levers) |
| gpt-oss-20b | 2/5 ok, 3/5 timeout | 5/5 ok | 2/5 enriched (15 levers) |
| gpt-5-nano | 5/5 ok | 5/5 ok | 5/5 (34 levers) |
| qwen3-30b | 5/5 ok | 5/5 ok | 5/5 (35 levers) |
| gpt-4o-mini | 5/5 ok | 5/5 ok | 5/5 (35 levers) |
| gemini | 5/5 ok | 5/5 ok | 5/5 (35 levers) |
| haiku | 5/5 ok | 5/5 ok | 5/5 (35 levers) |
| **Total** | **32/35 (91.4%)** | **35/35 (100% status)** | **32/35 (91.4% functional)** |

Note: gpt-5-nano shows 34 levers (5 plans × ~6.8 levers each) because sovereign_identity
has only 5 levers and 1 batch returns all 5; other plans have 7–8 levers and 2 batches.

### Field Length Table (current runs, all plans)

Baseline averages: desc=483.9 chars, syn=285.7 chars, con=298.3 chars

| Model | Avg desc | Ratio | Avg syn | Ratio | Avg con | Ratio |
|-------|---------|-------|---------|-------|---------|-------|
| llama3.1 | 370 | 0.76× | 353 | 1.24× | 380 | 1.27× |
| gpt-oss-20b | 660 | 1.36× | 382 | 1.34× | 385 | 1.29× |
| gpt-5-nano | 682 | 1.41× | 358 | 1.25× | 369 | 1.24× |
| qwen3-30b | 466 | 0.96× | 232 | 0.81× | 253 | 0.85× |
| gpt-4o-mini | 549 | 1.13× | 315 | 1.10× | 349 | 1.17× |
| gemini | 540 | 1.12× | 309 | 1.08× | 320 | 1.07× |
| haiku | 604 | 1.25× | 475 | 1.66× | 510 | 1.71× |

All models are within 0.76×–1.71× of baseline. No model exceeds the 2× warning threshold
for verbosity. Haiku's synergy/conflict length (1.66–1.71×) is elevated but consistent with
prior analysis.

### UUID Contamination

| Model | UUID count / total | Rate | Trend vs analysis 54 |
|-------|-------------------|------|----------------------|
| llama3.1 | 31/35 | 89% | ~UNCHANGED (C3 not implemented) |
| gpt-oss-20b | 8/15 | 53% | ~UNCHANGED (limited data) |
| gpt-5-nano | 0/34 | 0% | IMPROVED (was 4%) |
| qwen3-30b | 2/35 | 6% | IMPROVED (was 29%) |
| gpt-4o-mini | 0/35 | 0% | UNCHANGED |
| gemini | 12/35 | 34% | ~UNCHANGED (was 32%) |
| haiku | 1/35 | 3% | IMPROVED (was 6%) |

UUID source: `enrich_potential_levers.py:190` — `f"- {lever.lever_id}: {lever.name}"`.
The C3 fix (changing to `f"- {lever.name}"`) was not included in PR #453.

### Option Count Violations

| Model | Violations (< 3 options) / total |
|-------|----------------------------------|
| All models | 0/209 |

No violations observed. The `check_option_count` validator (which accepts ≥3) is not a
blocking issue in the current runs.

### Adaptive Batch Sizes (C2 trigger status)

| Model | num_output | C2 triggered? | Effective batch_size |
|-------|-----------|---------------|---------------------|
| llama3.1 | 256 | YES | 2 |
| gpt-oss-20b | 128000 (C1 bumped) | **NO (C1 conflict)** | **5** |
| gpt-5-nano | 128000 | NO | 5 |
| qwen3-30b | 8192 | YES | 2 |
| gpt-4o-mini | 8192 | YES | 2 |
| gemini | 8192 | YES | 2 |
| haiku | 8192 | YES | 2 |

Note: `SMALL_OUTPUT_THRESHOLD = 16384`. Models with `num_output < 16384` get `batch_size=2`.
Llama3.1 has `num_output=256` (Ollama reports its max new tokens per step), so it also gets
batch_size=2.

---

## Evidence Notes

- gpt-oss-20b metadata post-C1: `history/4/00_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json` — `"context_window": 3900, "num_output": 128000`
- gpt-oss-20b empty_response: `history/4/00_enrich_potential_levers/outputs/20260308_sovereign_identity/usage_metrics.jsonl` — all 3 calls `"error": "empty_response"` in <0.7s
- gpt-oss-20b success (silo): `history/4/00_enrich_potential_levers/outputs/20250321_silo/usage_metrics.jsonl` — Nebius provider: 1697 input, 3173 output, 29s; Chutes: 2280 input, 5108 output, 437s
- Analysis 55 timeout evidence: `history/3/93_enrich_potential_levers/outputs.jsonl` — 3 plans × `"error": "plan timeout after 600s"`
- llama3.1 UUID contamination: `history/3/99_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json` synergy_text for "Ethical Oversight Framework" includes `(ccd48764-fc2c-4926-82a0-fb54ff5f00dc)`
- C2 code: `enrich_potential_levers.py:175–185` (SMALL_OUTPUT_THRESHOLD = 16384, SMALL_OUTPUT_BATCH_SIZE = 2)
- C3 missing: `enrich_potential_levers.py:190` still reads `f"- {lever.lever_id}: {lever.name}"`
- OPTIMIZE_INSTRUCTIONS: lines 28–93 in `enrich_potential_levers.py` — entries for consequence echoing (lines 82–87) and UUID format inconsistency (lines 88–92) confirmed present from PR #452

---

## PR Impact

### What PR #453 Was Supposed to Fix

1. **C1**: max_tokens bump for gpt-oss-20b (8192 → 128000) — fix output truncation
2. **C2**: Adaptive batch size (batch_size=2 when num_output < 16384) — reduce batch overflow
3. **B4**: Guarded retry (depth=1, 300s budget) — prevent unbounded retry cascade
4. **D5**: Accurate batch counting (claims to fix, already fixed by PR #452)
5. **OPTIMIZE_INSTRUCTIONS**: Documentation updates (claims to add, already added by PR #452)

### Before vs After Comparison Table

| Metric | Before (PR #452, runs 85–91) | Before (PR #452, runs 92–98) | After (PR #453, runs 99/4/00–4/05) | Change |
|--------|------------------------------|------------------------------|-------------------------------------|--------|
| **Overall success rate** | 30/35 (85.7%) | 32/35 (91.4%) | 35/35 (100% status) / 32/35 (91.4% functional) | IMPROVED status, UNCHANGED functional |
| **gpt-oss-20b success** | 0/5 errors | 2/5 (3×600s timeout) | 2/5 (3×<2s empty_response) | IMPROVED (no timeouts) |
| **gpt-oss-20b runner time** | ~1862s (fast fails) | ~2224s (timeouts) | ~520s | **IMPROVED 4.3×** |
| **Other models success** | 30/30 | 30/30 | 30/30 | UNCHANGED |
| **Bracket placeholder leakage** | 0 | 0 | 0 | UNCHANGED |
| **Option count violations** | 0 | 0 | 0 | UNCHANGED |
| **Template leakage** | Eliminated by PR #451 | None | None | UNCHANGED |
| **LLMChatError count** | 0 | 0 | 0 | UNCHANGED |
| **llama3.1 desc (ratio)** | 0.65× | 0.70× | **0.76×** | IMPROVED |
| **qwen3-30b desc (ratio)** | 0.77× | 0.78× | **0.96×** | IMPROVED (confounded by input change) |
| **gemini desc (ratio)** | 0.94× | 0.94× | **1.12×** | IMPROVED (confounded by input change) |
| **haiku desc (ratio)** | 1.17× | 1.20× | **1.25×** | UNCHANGED (within noise) |
| **gpt-5-nano desc (ratio)** | 1.36× | 1.34× | **1.41×** | UNCHANGED (within noise) |
| **gpt-4o-mini desc (ratio)** | 1.00× | 1.02× | **1.13×** | Slight increase, within range |
| **UUID rate (llama3.1)** | 96% | ~96% | 89% | Marginal (C3 not fixed) |
| **UUID rate (qwen3-30b)** | 29% | ~20% | 6% | IMPROVED (smaller batches help) |
| **UUID rate (gemini)** | 32% | 0% | 34% | STOCHASTIC (no trend) |
| **C2 logic flaw** | N/A | N/A | C1 disables C2 for gpt-oss-20b | **NEW BUG** |
| **Retry depth limit** | Absent | Absent | Depth=1 + 300s budget | **FIXED** |
| **max_tokens gpt-oss-20b** | 8192 | 8192 | 128000 | CHANGED (C1) |

### Did the PR Fix the Targeted Issues?

**B4 (Guarded retry) — YES**: The 3×600s timeout pattern is fully eliminated. gpt-oss-20b's
failing plans now fail in <2s each. The implementation at lines 262–266 correctly checks
`depth < MAX_RETRY_DEPTH` and `elapsed < MAX_RETRY_BUDGET_SECONDS` before retrying.

**C1 (max_tokens bump) — PARTIALLY YES**: For gta_game and silo, the bump removed the
truncation barrier — output of 3173–7924 tokens per batch is now possible without being
cut off. However, 3 plans still fail via empty_response from OpenRouter, which may be a
side-effect of setting max_tokens=128000 >> context_window=3900 (some providers reject the
request).

**C2 (Adaptive batch size) — UNINTENDED MISDIRECTION**: C2 does not help gpt-oss-20b because
C1 inflated its num_output to 128000, preventing the threshold check from triggering. C2
does correctly trigger for gemini, haiku, qwen3-30b, gpt-4o-mini (all have num_output=8192).

### Regressions

1. **C1/C2 conflict**: By bumping max_tokens to 128000, C1 disables C2's protection for
   gpt-oss-20b. The model now uses BATCH_SIZE=5 with a 128000 max_tokens, which makes some
   OpenRouter providers return empty_response (possibly because they enforce the actual model
   context_window of 3900 and reject requests specifying max_tokens >> context_window).

2. **Input data change**: The runner was switched from `snapshot/1_deduplicate_levers` to
   `baseline/train`, breaking the comparison chain with analyses 54 and 55. This is not a
   PR-caused regression, but it makes it impossible to cleanly attribute quality improvements
   to PR #453 vs the simpler input data.

### Verdict

**CONDITIONAL**

The PR delivers its stated primary goal: the guarded retry eliminates the 3×600s timeouts
from PR #452, reducing gpt-oss-20b runner time from ~2224s to ~520s. This is a significant
infrastructure improvement. The max_tokens bump works for 2/5 gpt-oss-20b plans and produces
correct, complete output.

However, C1 and C2 conflict: the max_tokens bump disables the adaptive batch-size check for
gpt-oss-20b, leaving the root cause unaddressed. The model still fails 3/5 plans, now via
empty_response instead of timeout. A follow-up is needed:

1. **C2 fix**: Change the adaptive batch size condition from `num_output < SMALL_OUTPUT_THRESHOLD`
   to `context_window < SMALL_CONTEXT_THRESHOLD` (e.g., context_window < 8000), so gpt-oss-20b
   with context_window=3900 gets batch_size=2. This should decouple C2 from the C1 max_tokens change.
2. **C3**: Strip UUIDs from `full_lever_context_str` at line 190 (`f"- {lever.name}"`) — the
   one-line fix that analysis 55 documented as a priority.

---

## Questions For Later Synthesis

1. **C2 threshold criterion**: Should C2 use `context_window` instead of `num_output`? A model
   with context_window=3900 gets batch_size=5 after C1 (because num_output=128000). A model
   with context_window=200000 (haiku) gets batch_size=2 (because num_output=8192). The
   relationship between context_window and num_output is not consistent across providers.

2. **max_tokens=128000 rejects from providers**: Is the empty_response for gpt-oss-20b's
   3 failing plans caused by setting max_tokens >> context_window? If so, C1 overcorrected:
   a more conservative bump (e.g., max_tokens=32000 or 65536) might avoid provider rejections
   while still clearing the 8192 truncation limit.

3. **qwen3-30b UUID improvement**: The UUID contamination rate for qwen3-30b dropped from
   ~29% (run 88) to 6% (run 4/02). Is this due to batch_size=2 (shorter context per batch
   reduces UUID copying probability), or due to the smaller input (baseline/train levers are
   simpler and don't need cross-batch references), or stochastic variation?

4. **gemini UUID stochasticity**: Gemini shows 32% UUID rate in run 90, 0% in run 96, 34%
   in run 4/04. The rate is consistent with the two non-96 runs. Was run 96 an anomaly
   (perhaps due to a different OpenRouter routing on that day)?

5. **Haiku synergy/conflict length (1.66–1.71×)**: Haiku consistently produces longer-than-baseline
   synergy/conflict fields. With batch_size=2 now active for haiku, does the smaller batch
   context make outputs more focused, or does it allow more verbose cross-references?

---

## Reflect

The PR correctly targets the right issues (timeout, output truncation, retry cascade) but the
C1/C2 interaction is a design oversight: `num_output` is LlamaIndex's max_tokens setting, not
the model's actual context window capacity. C1 changed max_tokens (inflating num_output), and
C2 used num_output as a proxy for output capacity. The two changes are logically coupled in a
way that wasn't anticipated. The correct metric for batch sizing is `context_window`, which is
what determines how much text the model can process per call, not the output token limit.

Content quality is slightly better (llama3.1, qwen3-30b improving toward baseline), but the
input data change confounds these measurements. The improvements may be due to simpler input
levers (baseline/train) requiring shorter, more focused descriptions — not due to PR #453's
prompt or code changes.

---

## Potential Code Changes

**C4 (new, high priority)**: Fix C2 threshold to use `context_window` instead of `num_output`.

Change `enrich_potential_levers.py:181`:
```python
# Before:
if num_output < SMALL_OUTPUT_THRESHOLD:
# After:
if num_output < SMALL_OUTPUT_THRESHOLD or context_window < SMALL_CONTEXT_THRESHOLD:
```
Add `SMALL_CONTEXT_THRESHOLD = 8000` near line 104. This would trigger batch_size=2 for
gpt-oss-20b (context_window=3900 < 8000) regardless of the max_tokens bump.

Also consider: if context_window < 5000, set batch_size=1 to minimize per-batch token count.

**C3 (carry forward, high priority)**: Fix UUID in `full_lever_context_str` at line 190:
```python
# Before:
full_lever_context_str = "\n".join([f"- {lever.lever_id}: {lever.name}" for lever in levers_to_characterize])
# After:
full_lever_context_str = "\n".join([f"- {lever.name}" for lever in levers_to_characterize])
```

**H1 (carry forward, medium priority)**: Anti-echoing instruction in
`ENRICH_LEVERS_SYSTEM_PROMPT` for `description` field. llama3.1 at 0.76× baseline is
improving but still below 1.0×. Proposed addition:
"The `description` must add new context beyond what `consequences` states — do not
summarize or rephrase the consequences field."

---

## OPTIMIZE_INSTRUCTIONS Alignment

The current OPTIMIZE_INSTRUCTIONS correctly documents:
- Consequence echoing without elaboration (lines 82–87)
- UUID cross-reference format inconsistency (lines 88–92)
- Batch boundary blindness (lines 79–81)

**Proposed new entry**: The C1/C2 interaction problem reveals a new infrastructure-level
known problem that self-improve agents should watch for:

> "max_tokens vs context_window confusion. The adaptive batch size check (C2) uses
> `num_output` as a proxy for output capacity. `num_output` reflects the LlamaIndex
> `max_tokens` setting, not the model's true context window. When max_tokens is bumped
> (e.g., from 8192 to 128000), `num_output` inflates and the adaptive batch check no
> longer triggers. Always check `context_window` for batch-size decisions, not
> `max_tokens`/`num_output`."

---

## Summary

PR #453 successfully eliminates the 3×600s timeout pattern from PR #452 by adding a guarded
retry (depth=1, 300s budget). gpt-oss-20b runner time drops from ~2224s to ~520s per run.
The max_tokens bump restores correct output for 2/5 gpt-oss-20b plans.

However, C1 (max_tokens bump) and C2 (adaptive batch size) conflict: bumping max_tokens to
128000 inflates `num_output`, which prevents the `num_output < 16384` check from triggering
for gpt-oss-20b. The model still uses BATCH_SIZE=5 and still fails 3/5 plans — now via fast
empty_response rather than 600s timeouts. The fix is to check `context_window` instead of
`num_output` in C2's threshold logic.

Content quality is stable or slightly improved (no model exceeds 2× baseline; llama3.1 and
qwen3-30b moved closer to 1×), but these improvements are confounded by the input data
change from `snapshot/1_deduplicate_levers` to `baseline/train`. The UUID contamination
problem (C3) remains unaddressed.

**Verdict: CONDITIONAL** — Keep PR #453 for the guarded retry (clear win). Schedule C4 (C2
threshold fix) and C3 (UUID fix) as immediate follow-ups before the next analysis iteration.
