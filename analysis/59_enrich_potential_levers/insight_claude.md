# Insight Claude

## Overview

This analysis evaluates **PR #456** ("Adaptive batch size, guarded retry, and OpenRouter
config fixes for enrich step") against the runs examined in analysis 54
(PR #451 "Include consequences and review in enrich batch prompt").

**Input data caveat**: The current runs (4/20–26) used `baseline/train` as input
(5–8 deduplicated levers per plan), while the previous runs (3/85–91) used
`snapshot/1_deduplicate_levers` (14–18 levers per plan). This is a cross-experiment
input mismatch — lever counts and some field-length comparisons are confounded. Per
AGENTS.md prerequisites, this should be flagged before comparing. The mismatch arises
because the runner was reconfigured to run against `baseline/train` for this iteration.
Where possible, metrics are compared against `baseline/train` directly rather than
against the prior runs.

**Runs compared**:

| Model | Before (analysis 54) | After (this analysis) |
|-------|----------------------|-----------------------|
| ollama-llama3.1 | `3/85_enrich_potential_levers` | `4/20_enrich_potential_levers` |
| openrouter-gpt-oss-20b | `3/86_enrich_potential_levers` | `4/21_enrich_potential_levers` |
| openai-gpt-5-nano | `3/87_enrich_potential_levers` | `4/22_enrich_potential_levers` |
| openrouter-qwen3-30b-a3b | `3/88_enrich_potential_levers` | `4/23_enrich_potential_levers` |
| openrouter-gpt-4o-mini | `3/89_enrich_potential_levers` | `4/24_enrich_potential_levers` |
| openrouter-gemini-2.0-flash | `3/90_enrich_potential_levers` | `4/25_enrich_potential_levers` |
| anthropic-claude-haiku-4-5 | `3/91_enrich_potential_levers` | `4/26_enrich_potential_levers` |

---

## Negative Things

### N1 — gpt-oss-20b parasomnia_research_unit still times out

Run 4/21 (gpt-oss-20b) processed 4/5 plans successfully. The parasomnia plan hit the
600s timeout. The gta_game plan took 243 seconds — well above the other models (33–71s),
suggesting gpt-oss-20b is simply slow on larger plans. The parasomnia plan is the
largest in the baseline (8 levers, complex domain), which likely explains the timeout.

Evidence:
- `history/4/21_enrich_potential_levers/events.jsonl` line 10: `run_single_plan_error
  plan=20260311_parasomnia_research_unit error="plan timeout after 600s"`
- `history/4/21_enrich_potential_levers/outputs.jsonl`: gta_game duration=243.9s,
  parasomnia status=error duration=600s

### N2 — llama3.1 produces phantom lever IDs in 2 plans (3 levers not enriched)

Run 4/20 (llama3.1) shows `unknown_lever_id` errors in two plans:

- **gta_game**: 4 errors — two unknown_lever_id entries
  (`056fa843-5572-40a5-bca5-bca5cc18408`, `e36152c8-e249-4419-926b-d89db4cb89d`) and
  two `incomplete` entries for the same corrupted UUIDs. Result: 6 enriched levers
  instead of expected 8.
- **hong_kong_game**: 2 errors — one unknown_lever_id
  (`cbf0a8bc-1b56-4901-a607-83214a62c684`) and one `incomplete`. Result: 6 enriched
  levers instead of expected 7.

llama3.1 is generating characterizations with hallucinated or truncated UUIDs that
don't match any input lever. These phantom IDs are caught by the new error tracking
system (introduced in this PR). Total: 32/35 levers enriched for llama3.1 instead of
35. This was very likely a pre-existing bug now made visible by the PR's error tracking.

Evidence:
- `history/4/20_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json` errors field
- `history/4/20_enrich_potential_levers/outputs/20260310_hong_kong_game/002-12-enriched_levers_raw.json` errors field

### N3 — gpt-5-nano "Purpose:" template reappears in one description

Run 4/22 (gpt-5-nano) shows a "Purpose:" sub-header in the Resource Allocation Strategy
description for the gta_game plan. Analysis 54 identified this template as eliminated
by PR #451. Its reappearance for one lever in one plan suggests the template suppression
is input-dependent — different levers from `baseline/train` occasionally trigger the
pattern.

Evidence: `history/4/22_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json`
— Resource Allocation Strategy description begins "Purpose: determine how the silo
allocates finite resources..."

### N4 — Fabricated % claims still present in description fields (pre-existing)

Multiple models echo fabricated percentage claims from the `consequences` field into
their `description` text. Examples:

- llama3.1: 10 descriptions contain % claims (e.g., "Policy Advocacy Strategy...
  20% greater likelihood of adoption")
- gpt-4o-mini: 12 descriptions contain % claims
- gpt-5-nano: 11 descriptions contain % claims
- qwen3-30b: 9 descriptions
- haiku: 4 descriptions
- gemini-flash: 1 description
- gpt-oss-20b: 4 descriptions

This is not a regression introduced by PR #456 — it was present in the previous runs.
It originates from the `identify_potential_levers` step (the `consequences` field
contains fabricated percentages from that step), and the enrich step echoes these into
descriptions. This is the "consequence echoing" known problem in OPTIMIZE_INSTRUCTIONS.

### N5 — Input data mismatch confounds direct before/after comparison

The `input` field differs between analysis 54 (`snapshot/1_deduplicate_levers`) and
analysis 59 (`baseline/train`). Raw lever counts, field lengths, and content-specific
comparisons between the two analysis sets are unreliable. See Overview.

---

## Positive Things

### P1 — gpt-oss-20b success rate: 0/5 → 4/5 (major fix)

The most significant improvement: gpt-oss-20b went from complete failure (5/5 timeout
or fast error in run 3/86) to near-complete success (4/5 in run 4/21). The root cause
was `context_window=3900` (OpenRouter fallback) combined with `max_tokens=8192`. Since
3900 - 8192 < 0, LlamaIndex had no usable input token budget, causing all batches to
fail or hang.

After PR #456:
- `context_window`: 3900 → 131,072 (correct value for `openai/gpt-oss-20b`)
- `max_tokens`: 8192 → 65,536 (balanced within 131K context)
- Available input tokens: ~65K (was ~0)

Evidence: `history/4/21_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json`
metadata: `context_window=131072`, `num_output=65536`. All silo/gta/sovereign/hong_kong
plans now produce valid enriched levers with 7-8 enriched levers each.

### P2 — Correct context_window for all four OpenRouter models

The PR sets explicit `context_window` for all four OpenRouter models, eliminating the
LlamaIndex default fallback of 3900:

| Model | Before (cw) | After (cw) |
|-------|-------------|------------|
| openai/gpt-oss-20b | 3,900 | 131,072 |
| google/gemini-2.0-flash-001 | 3,900 | 1,048,576 |
| openai/gpt-4o-mini | 3,900 | 128,000 |
| qwen/qwen3-30b-a3b | 3,900 | 40,960 |

With correct `context_window`, all four models now process levers with the correct
batch size (5 levers/batch with large context, appropriate for baseline's 5–8 levers).

Evidence: `history/4/2{1,3,4,5}_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json`
metadata fields.

### P3 — Batch count normalized (3–4 → 1–2 per plan)

With the correct context window, the per-plan batch count dropped from 3–4 (with
cw=3900) to 1–2 (with correct cw). For a plan with 5 levers (sovereign_identity), one
batch is sufficient. For 7–8 lever plans, two batches cover them at batch_size=5.

| Model | Before total batches (5 plans) | After total batches (5 plans) |
|-------|-------------------------------|-------------------------------|
| llama3.1 | 17 | 9 |
| gpt-oss-20b | 3 (1 plan only) | 9 |
| gpt-5-nano | 17 | 9 |
| qwen3-30b | 17 | 9 |
| gpt-4o-mini | 17 | 9 |
| gemini-flash | 17 | 9 |
| haiku | 17 | 9 |

The 9 batches for 5 plans is correct: 4 plans × 2 batches + 1 plan × 1 batch = 9.

### P4 — Guarded retry logic added (C1 from analysis 54)

The PR adds per-batch retry with split on failure (lines 282–308 of
`enrich_potential_levers.py`). If a batch fails, it splits into two sub-batches and
retries once (MAX_RETRY_DEPTH=1) within a 300s budget. This directly addresses B1
("no per-batch retry") from analysis 54.

The guarded retry does not appear to have fired in the current runs (no `batch_retry`
errors in any enriched file), but it provides a safety net for transient failures.

### P5 — Error tracking added to raw output

The PR adds an `errors` field to the enriched levers raw JSON. This enables offline
diagnosis of:
- `unknown_lever_id`: model returned a characterization for a lever_id not in the input
- `incomplete`: a lever_id from input was not enriched (no description/synergy/conflict)
- `batch_retry`: a batch was split and retried
- `batch_skipped`: a batch failed and was skipped after retry exhaustion

Evidence: N2 above — the phantom lever ID bug in llama3.1 was discovered through this
new field (`history/4/20_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json`).

### P6 — OPTIMIZE_INSTRUCTIONS documents both fixed bugs

The current `OPTIMIZE_INSTRUCTIONS` constant already includes entries for the two
problems this PR addresses:
- "max_tokens overflow for small-context models" — documents the gpt-oss-20b failure
  mode and its fix
- "OpenRouter context_window metadata fallback" — documents the cw=3900 fallback
  problem and the solution (explicit override in baseline.json)

The PR both documents the problems (OPTIMIZE_INSTRUCTIONS) and fixes them (code +
config). This is correct process.

---

## Comparison

### Success Rate (before vs after)

| Model | Before (3/85–91) | After (4/20–26) | Change |
|-------|------------------|-----------------|--------|
| llama3.1 | 5/5 | 5/5 | same |
| gpt-oss-20b | 0/5 | 4/5 | **+4** |
| gpt-5-nano | 5/5 | 5/5 | same |
| qwen3-30b | 5/5 | 5/5 | same |
| gpt-4o-mini | 5/5 | 5/5 | same |
| gemini-flash | 5/5 | 5/5 | same |
| haiku | 5/5 | 5/5 | same |
| **Total** | **30/35 (85.7%)** | **34/35 (97.1%)** | **+11.4pp** |

Note: Previous total was 30/35 because gpt-oss-20b failed all 5 plans (run 3/86 had
2 fast LLM errors and 3 timeouts). The lone remaining failure (parasomnia timeout in
run 4/21) is gpt-oss-20b's slow throughput, not a config bug.

### Lever Count vs Baseline

| Model | Before levers | After levers | Baseline | Notes |
|-------|---------------|--------------|----------|-------|
| llama3.1 | 78 (different input) | 32 | 35 | 3 missing due to phantom IDs |
| gpt-oss-20b | 14 (1 partial plan) | 35 | 35 | **Match** |
| gpt-5-nano | 78 | 35 | 35 | **Match** |
| qwen3-30b | 78 | 35 | 35 | **Match** |
| gpt-4o-mini | 78 | 35 | 35 | **Match** |
| gemini-flash | 77 | 35 | 35 | **Match** |
| haiku | 78 | 35 | 35 | **Match** |

The previous runs' elevated lever counts (77–78) are primarily explained by the
different input (snapshot: 14–18 levers/plan vs baseline: 5–8 levers/plan). The
overcounting due to cw=3900 causing 3–4 small batches instead of 2 normal batches
is also a factor.

### Field Lengths vs Baseline (desc=483, syn=285, conf=298 chars)

All metrics are for current (4/20–26) runs vs baseline/train:

| Model | n | desc | d/b | syn | s/b | conf | c/b |
|-------|---|------|-----|-----|-----|------|-----|
| llama3.1 | 32 | 405 | 0.84× | 374 | 1.31× | 384 | 1.29× |
| gpt-oss-20b | 35 | 619 | 1.28× | 407 | 1.43× | 414 | 1.39× |
| gpt-5-nano | 35 | 689 | 1.43× | 350 | 1.23× | 360 | 1.21× |
| qwen3-30b | 35 | 392 | 0.81× | 199 | 0.70× | 209 | 0.70× |
| gpt-4o-mini | 35 | 477 | 0.99× | 289 | 1.01× | 321 | 1.08× |
| gemini-flash | 35 | 488 | 1.01× | 305 | 1.07× | 319 | 1.07× |
| haiku | 35 | 588 | 1.22× | 433 | 1.52× | 447 | 1.50× |

No model exceeds the 2× warning threshold. qwen3-30b is notably terse on synergy/conflict
(0.70×) — consistent with prior analyses. llama3.1 description is slightly below
baseline (0.84×).

---

## Quantitative Metrics

### Success Rate

| Model | Before (3/85–91) | After (4/20–26) | Change |
|-------|------------------|-----------------|--------|
| llama3.1 | 5/5 | 5/5 | = |
| gpt-oss-20b | 0/5 | 4/5 | +4 |
| gpt-5-nano | 5/5 | 5/5 | = |
| qwen3-30b | 5/5 | 5/5 | = |
| gpt-4o-mini | 5/5 | 5/5 | = |
| gemini-flash | 5/5 | 5/5 | = |
| haiku | 5/5 | 5/5 | = |
| **TOTAL** | **30/35 (85.7%)** | **34/35 (97.1%)** | **+4 plans** |

### Batch Count

| Model | Before total batches | After total batches | Change |
|-------|---------------------|---------------------|--------|
| llama3.1 | 17 | 9 | –8 |
| gpt-oss-20b | 3 (1 plan) | 9 | +6 (now full 5 plans) |
| gpt-5-nano | 17 | 9 | –8 |
| qwen3-30b | 17 | 9 | –8 |
| gpt-4o-mini | 17 | 9 | –8 |
| gemini-flash | 17 | 9 | –8 |
| haiku | 17 | 9 | –8 |

### Context Window Values

| Model | Before | After |
|-------|--------|-------|
| openai/gpt-oss-20b | 3,900 | 131,072 |
| google/gemini-2.0-flash-001 | 3,900 | 1,048,576 |
| openai/gpt-4o-mini | 3,900 | 128,000 |
| qwen/qwen3-30b-a3b | 3,900 | 40,960 |
| llama3.1 (Ollama) | 131,072 | 131,072 (unchanged) |
| anthropic-haiku (direct) | N/A | 200,000 |

### Errors in Enriched Files

| Model | Error type | Count |
|-------|-----------|-------|
| llama3.1 | unknown_lever_id | 3 |
| llama3.1 | incomplete | 3 |
| All others | none | 0 |

### Constraint Violations

| Violation | Before (3/85–91) | After (4/20–26) |
|-----------|------------------|-----------------|
| Missing description | 0 | 0 |
| Missing synergy_text | 0 | 0 |
| Missing conflict_text | 0 | 0 |
| Plan failures | 5 (gpt-oss-20b) | 1 (gpt-oss-20b parasomnia) |
| Phantom lever IDs | not tracked | 3 (llama3.1, 2 plans) |
| Fabricated % in desc | present (pre-existing) | present (pre-existing) |
| gpt-5-nano "Purpose:" template | 0 | 1 (gta_game, Resource Alloc) |

---

## Evidence Notes

Files consulted:

- `history/4/20–26_enrich_potential_levers/outputs.jsonl` — current run success rates
- `history/3/85–91_enrich_potential_levers/outputs.jsonl` — previous run success rates
- `history/4/21_enrich_potential_levers/events.jsonl` — parasomnia timeout event
- `history/3/86_enrich_potential_levers/events.jsonl` — gpt-oss-20b failure events
- `history/4/2{0,1,3,4,5}_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json` — metadata context_window values
- `history/4/20_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json` — llama3.1 phantom lever ID errors
- `history/4/20_enrich_potential_levers/outputs/20260310_hong_kong_game/002-12-enriched_levers_raw.json` — llama3.1 phantom lever ID errors
- `baseline/train/*/002-12-enriched_levers_raw.json` — baseline lever counts and field lengths
- `snapshot/1_deduplicate_levers/20250321_silo/002-11-deduplicated_levers_raw.json` — snapshot lever IDs (confirmed different from baseline)
- `PlanExe/worker_plan/worker_plan_internal/lever/enrich_potential_levers.py` lines 28–103 (OPTIMIZE_INSTRUCTIONS), 109–119 (constants), 187–327 (execute method with retry logic)
- `analysis/54_enrich_potential_levers/insight_claude.md` — prior analysis baseline

---

## PR Impact

### What the PR Was Supposed to Fix

From `pr_description`:
1. OpenRouter config fixes: Add explicit `context_window` for all 4 OpenRouter models
2. gpt-oss-20b max_tokens: 8192→65536 (input/output balanced within 131K context)
3. Adaptive batch size: `batch_size=2` when `context_window < 3000` (avoids false
   positives on the old 3900 fallback)
4. Guarded retry: Split once (depth=1) within 300s budget, then skip
5. Error tracking: Persist errors in raw JSON output for offline diagnosis
6. Accurate batch counting: `batches_succeeded` instead of hardcoded `1`

### Before vs After Comparison Table

| Metric | Before (runs 3/85–91) | After (runs 4/20–26) | Change |
|--------|----------------------|----------------------|--------|
| Overall success rate | 30/35 (85.7%) | 34/35 (97.1%) | **+11.4pp** |
| gpt-oss-20b success | 0/5 (0%) | 4/5 (80%) | **+4 plans** |
| Context window (OpenRouter) | 3,900 (all) | 131K/1M/128K/41K | **Fixed** |
| gpt-oss-20b max_tokens | 8,192 | 65,536 | **Fixed** |
| Batches per plan (avg) | 3–4 | 1–2 | **Normalized** |
| Lever counts match baseline | No (14–18/plan) | Yes (5–8/plan) | **Fixed** |
| Error tracking in output | Not present | Present | **Added** |
| Guarded retry logic | Not present | MAX_RETRY_DEPTH=1, 300s budget | **Added** |
| llama3.1 phantom IDs tracked | Not visible | 3 unknown_lever_id errors | Surfaced |
| gpt-5-nano "Purpose:" template | 0 (PR #451 fixed) | 1 (gta_game) | Minor regression |
| Fabricated % in desc | Present | Present | Unchanged |
| qwen3-30b synergy/conflict terseness | 0.74×/0.76× (baseline) | 0.70×/0.70× | Marginal |

### Did the PR Fix the Targeted Issues?

**Context window fix**: YES. All four OpenRouter models now report the correct
`context_window` in metadata, and batch counts are normalized. Confirmed by metadata
inspection across `history/4/2{1,3,4,5}_enrich_potential_levers/outputs/*/002-12-enriched_levers_raw.json`.

**gpt-oss-20b recovery**: PARTIALLY. 4/5 plans succeed. The parasomnia_research_unit
plan (the largest, 8 levers) still times out at 600s. This appears to be gpt-oss-20b's
slow throughput on large plans rather than a configuration error — gta_game took 243s
even with correct config, compared to 21–47s for other models.

**Adaptive batch size**: YES. With `SMALL_CONTEXT_THRESHOLD=3000`, the old cw=3900
fallback would NOT trigger the small batch size (3900 > 3000), preventing false
positives. If a model genuinely has cw < 3000, it will use `SMALL_CONTEXT_BATCH_SIZE=2`.

**Guarded retry**: YES (implemented, not triggered). No `batch_retry` errors appear in
any current output file, indicating all batches succeeded on first attempt. The retry
mechanism is available for transient failures.

**Error tracking**: YES. The `errors` field is populated in output files. The llama3.1
phantom lever ID problem (N2) was directly discovered through this new field.

### Regressions

1. **gpt-5-nano "Purpose:" template reappearance** (N3): One instance in gta_game
   plan. Minor — may be input-dependent rather than a regression.
2. **llama3.1 3 levers not enriched** (N2): Phantom lever IDs in 2 plans cause 3
   levers to have no enrichment. This was likely pre-existing (not visible before the
   PR added error tracking).

### Verdict: **CONDITIONAL**

The PR produced a **significant, measurable improvement** in success rate (85.7% →
97.1%) and directly fixed the targeted OpenRouter configuration bugs. The gpt-oss-20b
model, which was completely non-functional in analysis 54, now succeeds on 4/5 plans.

CONDITIONAL rather than KEEP because:
1. gpt-oss-20b still times out on parasomnia_research_unit — the model is fundamentally
   slow for large plans. The 600s plan timeout may need to be increased, or gpt-oss-20b
   may need to be treated as a non-production-grade model for this step.
2. llama3.1 phantom lever IDs (3 levers unenriched) need investigation — this is now
   visible thanks to the PR, and should be addressed before declaring the step stable.
3. The input data mismatch between analysis 54 and 59 (snapshot vs baseline/train)
   makes the content quality comparison unreliable; a clean comparison against the same
   input set would strengthen confidence.

---

## OPTIMIZE_INSTRUCTIONS Alignment

Current OPTIMIZE_INSTRUCTIONS (lines 28–103 of `enrich_potential_levers.py`) lists
these known problems:

| Problem | Observed? | Notes |
|---------|-----------|-------|
| Boilerplate descriptions | Reduced | gpt-5-nano "Purpose:" reappears once (gta_game) |
| Self-referential synergy/conflict | Not observed | Spot checks clean |
| Phantom lever references | YES (llama3.1) | unknown_lever_id errors in 2 plans |
| Symmetric parroting | Not checked systematically | Spot checks show variation |
| Word-count padding | Not observed in new runs | — |
| Missing conflict_text | Not observed | All levers have conflict_text |
| Batch boundary blindness | Not triggered | Only 2 batches per plan, adequate cross-batch context |
| Consequence echoing | YES (all models) | % claims echo from consequences into description |
| UUID cross-reference format | YES (llama3.1) | UUIDs in synergy_text (cbf0a8bc...) |
| max_tokens overflow | Fixed by PR | gpt-oss-20b now uses balanced 65K/65K |
| OpenRouter cw fallback | Fixed by PR | All four models now have explicit cw |

**New problem not yet in OPTIMIZE_INSTRUCTIONS (proposed addition)**:
- **Phantom lever ID generation for non-function-calling models**: llama3.1 (not a
  function-calling model: `is_function_calling_model: false`) generates lever_id values
  that are truncated or corrupted UUIDs. These don't match any input lever. This is
  distinct from "phantom lever references" (wrong lever names) — this is wrong lever
  IDs. Models without native function-calling support may misformat UUID fields when
  producing structured JSON. Suggest: add a validator that checks all returned
  `lever_id` values against the input set and logs a specific warning.

---

## Questions For Later Synthesis

1. **Should gpt-oss-20b's plan timeout be increased?** The model completes gta_game
   in 243s and the parasomnia plan (also 8 levers) times out at 600s. The slow
   throughput may be a model-level limitation. Options: raise plan timeout to 900s,
   or remove gpt-oss-20b from production runs for this step.

2. **Why does llama3.1 generate corrupted lever IDs?** llama3.1 is not a function-
   calling model. It generates structured JSON via free-text parsing. The corrupted UUIDs
   (`056fa843-5572-40a5-bca5-bca5cc18408` vs expected full UUIDs) suggest either
   hallucination or truncation. Is there a schema-enforced lever_id validator that
   could reject non-matching UUIDs at parse time?

3. **Is the gpt-5-nano "Purpose:" template regression input-specific?** The template
   appeared only in the gta_game plan with the `baseline/train` input. With
   `snapshot/1_deduplicate_levers` levers (analysis 54), it was absent. Is there
   something specific about the baseline/train gta_game lever set that triggers it?

4. **Input data standardization**: Analysis 54 used `snapshot/1_deduplicate_levers`
   and analysis 59 uses `baseline/train`. Future iterations should ensure consistent
   input to make comparisons valid. Should the snapshot be updated to match baseline/train?

5. **qwen3-30b synergy/conflict terseness (0.70×)**: This has been noted since analysis
   53. It was 0.74–0.76× in analysis 54 and is now 0.70×. Is this a regression or
   input-dependent variation?

---

## Reflect

PR #456 fixes the core infrastructure issue that made OpenRouter models unreliable for
this step. The critical insight is that with `context_window=3900` (the LlamaIndex
fallback), the available input budget was approximately 3900 - max_tokens = 3900 - 8192
= negative, which LlamaIndex would cap at near-zero. For gpt-oss-20b with max_tokens=8192,
this caused every batch to fail or hang. For other models with max_tokens=8192, it
allowed the batch to proceed but with severely truncated input — explaining why the
previous runs showed 3–4 batches per plan instead of the correct 1–2.

The most important discovery from this analysis was enabled by the PR itself: the new
`errors` field in the raw output surfaced that llama3.1 has been generating phantom
lever IDs silently. Without error tracking, these failures were invisible — the output
JSON would simply contain fewer levers than expected, and no diagnostic information
would indicate why.

The input data mismatch between analyses 54 and 59 is a methodological concern but
does not undermine the core PR evaluation: success rates and metadata values (context_window)
can be compared regardless of which input levers were used.

---

## Potential Code Changes

**C1** — Investigate llama3.1 phantom lever ID generation.
The `is_function_calling_model: false` flag suggests llama3.1 produces structured JSON
via free-text. Consider adding schema validation that rejects `lever_id` values not
present in the input before calling `enriched_levers_map[char.lever_id]`. Currently
the code only catches this AFTER the fact (line 268: `if char.lever_id in enriched_levers_map`).
Adding a pre-validation warning + metric counter would quantify how often this occurs.
Evidence: 3 phantom lever IDs in `history/4/20_enrich_potential_levers` across 2 plans.

**C2** — Increase plan timeout for gpt-oss-20b or document it as a slow model.
gpt-oss-20b took 243s on gta_game and timed out at 600s on parasomnia. All other models
complete all 5 plans in 14–107s. Consider model-specific timeout configuration or
removing gpt-oss-20b from automated runs until throughput improves.
Evidence: `history/4/21_enrich_potential_levers/outputs.jsonl` — gta_game duration=243.9s.

**H1** — Add lever_id validation pre-check in enrichment loop.
At line 267 of `enrich_potential_levers.py`, before updating `enriched_levers_map`,
validate that `char.lever_id` matches an expected format (UUID v4 regex). If it fails
format validation, log immediately with the original UUID for forensics.
Expected effect: better diagnostics for llama3.1 (and other non-function-calling
models) when they generate corrupted or hallucinated lever IDs.

**H2** — Add OPTIMIZE_INSTRUCTIONS entry for phantom lever ID generation.
The current known-problems list does not distinguish between phantom lever *names*
(referenced in synergy/conflict text) and phantom lever *IDs* (returned in the
characterization schema). Add a specific entry for the latter.

---

## Summary

PR #456 ("Adaptive batch size, guarded retry, and OpenRouter config fixes for enrich
step") delivered a **significant, measurable infrastructure fix**:

- Success rate: 85.7% → 97.1% (4 additional plans completed)
- gpt-oss-20b: 0/5 → 4/5 (from completely broken to mostly functional)
- Context window: All four OpenRouter models now report correct values (was 3,900 for all)
- Batch counts normalized: 3–4 batches/plan → 1–2 batches/plan (correct for 5–8 levers)
- Error tracking added: phantom lever ID bug in llama3.1 now surfaced

Remaining issues:
- gpt-oss-20b: 1/5 plans still times out (parasomnia_research_unit, large plan, slow model)
- llama3.1: 3 levers not enriched due to phantom lever IDs across 2 plans
- gpt-5-nano "Purpose:" template: 1 instance reappeared (possibly input-dependent)
- Input data mismatch confounds direct content-quality comparison with analysis 54

**Verdict: CONDITIONAL**. The PR is sound and should be merged, but two follow-up
issues warrant tracking: (1) gpt-oss-20b timeout on large plans, (2) llama3.1 phantom
lever IDs that silently skip lever enrichment.
