# Insight Claude

## Overview

This analysis evaluates **PR #455** ("Adaptive batch size, guarded retry, and gpt-oss-20b config fix
for enrich step") against the baseline established in analysis 54 (PR #451).

**PR #455 changes:**
1. gpt-oss-20b config fix: `max_tokens` 8192→65536, added `context_window=131072`
2. Adaptive batch size: `batch_size=2` when `context_window < 6000` (SMALL_CONTEXT_THRESHOLD)
3. Guarded retry: split once (depth=1) on batch failure within 300s budget
4. Error tracking: persist errors in raw JSON output (`errors` field)
5. Accurate batch counting: `batches_succeeded` (was hardcoded `1`)
6. OPTIMIZE_INSTRUCTIONS: document consequence-echoing, UUID format inconsistency, max_tokens overflow

**Input data warning**: Before runs (3/85-91, from PR #451 experiments) used
`snapshot/1_deduplicate_levers` (15-18 levers per plan). After runs (4/13-19) use
`baseline/train` (7-8 levers per plan). This violates the cross-experiment comparison
prerequisites from AGENTS.md — any field-length comparisons between before and after
are confounded by this input difference and must be interpreted with caution.

**Runs compared:**

| Before (analysis 54 runs) | After (analysis 58 runs) | Model |
|---------------------------|--------------------------|-------|
| `3/85_enrich_potential_levers` | `4/13_enrich_potential_levers` | ollama-llama3.1 |
| `3/86_enrich_potential_levers` | `4/14_enrich_potential_levers` | openrouter-openai-gpt-oss-20b |
| `3/87_enrich_potential_levers` | `4/15_enrich_potential_levers` | openai-gpt-5-nano |
| `3/88_enrich_potential_levers` | `4/16_enrich_potential_levers` | openrouter-qwen3-30b-a3b |
| `3/89_enrich_potential_levers` | `4/17_enrich_potential_levers` | openrouter-openai-gpt-4o-mini |
| `3/90_enrich_potential_levers` | `4/18_enrich_potential_levers` | openrouter-gemini-2.0-flash-001 |
| `3/91_enrich_potential_levers` | `4/19_enrich_potential_levers` | anthropic-claude-haiku-4-5-pinned |

---

## Negative Things

### N1 — gpt-oss-20b: 3/5 plans still timeout after PR

The "LLM batch interaction failed." errors from run 86 are gone (see Positive P1), but
three plans timeout at 600s in run 14: `20260310_hong_kong_game`, `20250321_silo`,
`20260308_sovereign_identity`.

Root cause: the guarded retry + multi-provider failover is making 6-9 API calls per plan
for gpt-oss-20b. Each failed provider attempt eats into the 300s MAX_RETRY_BUDGET_SECONDS
while simultaneously pushing total plan wall-clock time past 600s. The output files ARE
written (all 5 plans have valid enriched levers), but the orchestrator marks them as
`status=error` because the plan timeout fires.

Evidence:
- `history/4/14_enrich_potential_levers/outputs/20260310_hong_kong_game/activity_overview.json`:
  6 calls across DeepInfra, Fireworks, Together; total 34465 output tokens, 17327 input tokens
- `history/4/14_enrich_potential_levers/outputs/20250321_silo/activity_overview.json`:
  8 calls across Amazon Bedrock, DeepInfra, Fireworks, Nebius, Together; total 45354 output tokens
- `history/4/14_enrich_potential_levers/events.jsonl`: silo timeout at 13:58:03 (600s after
  13:41:40 start), log.txt shows "killed after 600s" at 15:51:40 local

### N2 — Adaptive batch_size=2 unintentionally triggers for 3 OpenRouter models

The adaptive batch size code at line 195 (`enrich_potential_levers.py`) checks:
`if context_window < SMALL_CONTEXT_THRESHOLD (6000): batch_size = SMALL_CONTEXT_BATCH_SIZE (2)`

llama_index's `OpenRouter_LLM` returns `context_window=3900` for ALL OpenRouter-proxied
models (confirmed from output metadata), which is below the 6000 threshold. This causes
batch_size=2 for three models that do NOT need it:

| Model (via OpenRouter) | Reported context_window | Actual context_window | batch_size triggered |
|------------------------|-------------------------|-----------------------|---------------------|
| qwen3-30b-a3b | 3900 | ~32768+ | 2 (unintended) |
| gpt-4o-mini | 3900 | 128000 | 2 (unintended) |
| gemini-2.0-flash | 3900 | 1000000 | 2 (unintended) |

Evidence: `history/4/17_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json`
metadata[0] shows `context_window: 3900, llm_classname: OpenRouter_LLM`.

Compared to before: run 89 (gpt-4o-mini, before PR) had `calls_succeeded: 1` per plan;
run 17 (after PR) has `calls_succeeded: 3-4`. The adaptive batch size creates 3-4 small
batches where before there was 1 large batch, increasing total API calls significantly.

For gpt-4o-mini run 17 silo: **15 total API calls** vs 13 in run 89. For the after run,
those 15 calls processed 7 levers (4 successful batches × 2 levers each + retries),
while the before run's 13 calls processed 15 levers (1 successful batch + retries for a
much larger input). The extra calls are retry overhead from batch splitting.

Evidence: `history/4/17_enrich_potential_levers/outputs/20250321_silo/activity_overview.json`
vs `history/3/89_enrich_potential_levers/outputs/20250321_silo/activity_overview.json`.

### N3 — Input data discrepancy invalidates field-length comparison

Before runs (3/85-91) enriched 15-18 levers per plan (from `snapshot/1_deduplicate_levers`).
After runs (4/13-19) enrich 7-8 levers per plan (from `baseline/train`, deduplicated set).

Verified:
- `snapshot/1_deduplicate_levers/20250321_silo`: 15 levers
- `baseline/train/20250321_silo/002-11-deduplicated_levers_raw.json`: 7 deduplicated levers
- Run 89 silo enriched 15 levers; run 17 silo enriched 7 levers

The `meta.json` for analysis 58 lists `"input": "baseline/train"` while analysis 54's
`meta.json` listed `"input": "snapshot/1_deduplicate_levers"`. **The cross-experiment
comparison prerequisites from AGENTS.md are violated.** Field-length metrics and
percent-claim counts between before and after are unreliable.

### N4 — Percent claims appeared in gpt-4o-mini and haiku outputs

After runs show fabricated percentage claims in descriptions that were absent before:
- Run 17 (gpt-4o-mini): **16 percent claims** across 5 plans (0 in run 89)
- Run 19 (haiku): **16 percent claims** across 5 plans (0 in run 91)

Examples from run 17 silo:
- `Information Control Strategy.description`: "30% reduction in innovative output" and "15%"
- `Resource Management Philosophy.description`: "20%" and "10%"
- `Societal Structure Paradigm.description`: "15%" and "5%"

The baseline/train input `002-10-potential_levers.json` contains these percentages in the
`consequences` field (e.g., "Immediate: Resource hoarding → Systemic: 15% increase in
black market activity"). The after runs are echoing those numbers into the enrichment output.

However, this finding is confounded: (a) the before runs used a different input snapshot
whose `consequences` text may not have contained these numbers, and (b) the adaptive
batch_size=2 creates smaller prompt contexts that may increase per-lever focus and
consequence-echoing. The causal mechanism is unclear without isolating variables.

Evidence: `history/4/17_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json`
vs `history/3/89_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json`.

### N5 — llama3.1 UUID mutations produce silent lever-skip errors

Run 13 (llama3.1) shows 4 errors across 2 plans — two plans each have one `unknown_lever_id`
and one `incomplete` error:

```json
{"type": "unknown_lever_id", "lever_id": "056fa843-5572-40a5-bca5-bca5cc7c18408"}
{"type": "incomplete", "lever_id": "056fa843-5572-40a5-bca5-cc7c7cc18408"}
```

The UUID `bca5` appears twice in the first variant (too long). The LLM mutated the actual
lever UUID, then the lookup in `enriched_levers_map` failed, causing the lever to be
marked `incomplete`. The error tracking (new in PR #455) makes this visible; before the
PR, such lever mutations would silently drop enrichment without any record.

Evidence: `history/4/13_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json`
and `history/4/13_enrich_potential_levers/outputs/20260310_hong_kong_game/002-12-enriched_levers_raw.json`.

---

## Positive Things

### P1 — gpt-oss-20b "LLM batch interaction failed." error eliminated

Run 86 (before PR): all 5 plans failed. hong_kong_game and gta_game returned
"LLM batch interaction failed." in under 30 seconds; silo, sovereign_identity, and
parasomnia timed out after 600 seconds spending 25-37K input tokens without output.

Run 14 (after PR): the fast failure mode is gone. All 5 plans now produce valid
`002-12-enriched_levers_raw.json` with the expected lever counts and zero `errors` entries.
gta_game and parasomnia_research_unit complete with `status=ok` at 136-146s. This confirms
the max_tokens 8192→65536 fix addresses the BadRequestError root cause.

Evidence:
- `history/3/86_enrich_potential_levers/outputs.jsonl`: all 5 plans `status=error`
- `history/4/14_enrich_potential_levers/outputs.jsonl`: 2 ok, 3 timeout
- `history/4/14_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json`:
  8 levers, 0 errors, metadata shows `context_window: 131072, num_output: 65536`

### P2 — gpt-oss-20b output quality is grounded and project-specific

For the 2 plans that succeed in run 14, the enriched levers reference actual project details:

- `hong_kong_game`, "Production Efficiency Optimization" description: "maximizing value within
  the HK$470 million budget by streamlining every phase of filmmaking"
- `hong_kong_game`, "Audience Engagement Strategy" description: "theatrical and premium VOD windows"

This demonstrates the max_tokens fix enables the model to produce complete, contextual
responses rather than the truncated/errored output from run 86.

Evidence: `history/4/14_enrich_potential_levers/outputs/20260310_hong_kong_game/002-12-enriched_levers_raw.json`
lever descriptions.

### P3 — Error tracking is operational and catches real issues

The new `errors` field in the JSON output (line 327 in `enrich_potential_levers.py`) now
persists failure records. Run 13 shows the feature working correctly: `unknown_lever_id`
errors for malformed UUIDs, paired with `incomplete` errors when the lookup fails. Before
this PR, such failures were logged but not saved to disk.

This is a measurable improvement to diagnostic capability. The `analysis/run_insight.py`
pipeline (and future code review agents) can now programmatically audit error rates without
re-running the pipeline.

### P4 — OPTIMIZE_INSTRUCTIONS updated with three new known problems

PR #455 adds three new entries to the known-problems list (lines 82-98):
1. "Consequence echoing without elaboration" — weak models summarize consequences verbatim
2. "UUID cross-reference format inconsistency" — models copy UUIDs in varying formats
3. "max_tokens overflow for small-context models" — cap at `context_window // 2`

Entry 3 documents the exact root cause that was fixed by this PR, providing the rationale
for the fix. Entry 1 was proposed in analysis 54 (H2) and is now formalized.

### P5 — 5/5 plans produce valid output for gpt-oss-20b (status notwithstanding)

Even though 3 of 5 gpt-oss-20b plans have `status=error` (plan timeout) in outputs.jsonl,
all 5 output files contain complete enriched lever sets with 0 errors. The orchestrator's
600s timeout fires AFTER the enrichment writes its output, meaning the enriched lever data
is usable even for the "failed" plans. This is a practical improvement — before the PR,
those 3 plans had NO output at all.

Evidence: `history/4/14_enrich_potential_levers/outputs/20260308_sovereign_identity/002-12-enriched_levers_raw.json`:
5 levers, 0 errors. `outputs.jsonl` for same plan: `status=error, error="plan timeout after 600s"`.

---

## Comparison

### Success Rate

| Run pair | Model | Before (status=ok) | After (status=ok) | Change |
|----------|-------|--------------------|-------------------|--------|
| 85→13 | ollama-llama3.1 | 5/5 | 5/5 | same |
| 86→14 | openrouter-gpt-oss-20b | 0/5 | 2/5 | **+2** |
| 87→15 | openai-gpt-5-nano | 5/5 | 5/5 | same |
| 88→16 | openrouter-qwen3-30b | 5/5 | 5/5 | same |
| 89→17 | openrouter-gpt-4o-mini | 5/5 | 5/5 | same |
| 90→18 | openrouter-gemini-flash | 5/5 | 5/5 | same |
| 91→19 | anthropic-haiku | 5/5 | 5/5 | same |
| **Total** | | **30/35 (85.7%)** | **32/35 (91.4%)** | **+2** |

Note: gpt-oss-20b's 5/5 output files all contain valid enriched levers; only 2/5 plans
completed within the 600s orchestrator timeout.

### Field Lengths (caveat: different input data — comparisons are NOT reliable)

Before runs used snapshot input (15-18 levers/plan); after runs use baseline/train (7-8
levers/plan). Average field lengths reflect this structural difference:

| Model | Before desc | After desc | Before syn | After syn | Before conf | After conf |
|-------|-------------|------------|------------|-----------|-------------|------------|
| llama3.1 | 316 | 409 | 373 | 353 | 393 | 354 |
| gpt-oss-20b | 540 (1/5 plans) | 668 | 390 | 387 | 382 | 388 |
| gpt-5-nano | 658 | 678 | 333 | 347 | 338 | 358 |
| qwen3-30b | 371 | 470 | 212 | 235 | 225 | 253 |
| gpt-4o-mini | 482 | 553 | 278 | 322 | 305 | 353 |
| gemini-flash | 457 | 529 | 276 | 312 | 298 | 331 |
| haiku | 569 | 575 | 453 | 454 | 488 | 483 |

**Baseline (baseline/train avg):** desc=484, syn=287, conf=300.

The "increase" in after-run lengths is expected because: (a) fewer levers per plan means
each lever gets more focused attention, and (b) different input data. These numbers cannot
be used to claim quality improvement or regression.

### Adaptive Batch Size Effect on Calls Per Plan

The three OpenRouter models now use batch_size=2 (triggered by context_window=3900). This
is confirmed by `calls_succeeded` values in outputs.jsonl matching `ceil(n_levers / 2)`:

| Model | n_levers (silo) | Before calls_succ | After calls_succ | Expected (batch=2) |
|-------|-----------------|-------------------|------------------|--------------------|
| qwen3-30b | 7 | 1 | 4 | 4 ✓ |
| gpt-4o-mini | 7 | 1 | 4 | 4 ✓ |
| gemini-flash | 7 | 1 | 4 | 4 ✓ |
| llama3.1 | 7 | 1 | 2 | 2 (normal batch, ≤5) |
| gpt-5-nano | 7 | 1 | 2 | 2 (normal batch, ≤5) |
| haiku | 7 | 1 | 2 | 2 (normal batch, ≤5) |

---

## Quantitative Metrics

### Success Rate

| Before total | After total | Change |
|---|---|---|
| 30/35 (85.7%) | 32/35 (91.4%) | +2 plans (all from gpt-oss-20b) |

### Percent Claims (fabricated numbers in enrichment fields)

| Model | Before | After | Change |
|-------|--------|-------|--------|
| ollama-llama3.1 | 0 | 2 | +2 |
| gpt-oss-20b | 0 | 0 | same |
| gpt-5-nano | 0 | 6 | +6 |
| qwen3-30b | 0 | 2 | +2 |
| gpt-4o-mini | 0 | 16 | **+16** |
| gemini-flash | 0 | 3 | +3 |
| haiku | 0 | 16 | **+16** |

**Caveat**: This increase is confounded by input data difference (baseline/train
consequences fields contain percent claims; snapshot consequences may not). The causal
direction (PR #455 vs input data) cannot be isolated without a controlled comparison.

### Error Tracking

| Run | Model | Error types | Plans affected |
|-----|-------|-------------|----------------|
| 13 (after) | llama3.1 | unknown_lever_id, incomplete | 2/5 |
| 14–19 (after) | all others | (none) | 0 |

### API Calls Per Plan (gpt-4o-mini, silo example)

| Run | Total calls | Successful batches | Input tokens | Output tokens |
|-----|------------|-------------------|--------------|---------------|
| 89 (before) | 13 | 1 (15 levers) | 40,306 | 13,331 |
| 17 (after) | 15 | 4 (7 levers) | 32,941 | 6,769 |

The after run makes more batches but fewer tokens overall (due to fewer levers processed).

### Constraint Violations

| Violation type | Before (runs 85-91) | After (runs 13-19) |
|----------------|---------------------|--------------------|
| Missing fields (description, synergy, conflict) | 0 | 0 |
| Status=error plans | 5 (run 86) | 3 (run 14) |
| Errors in JSON output | 0 (no field) | 4 (run 13, llama3.1) |
| Fabricated % claims | 0 | 45 total |

---

## Evidence Notes

Files consulted:

- `history/3/85–91_enrich_potential_levers/outputs.jsonl` — before run status and calls_succeeded
- `history/4/13–19_enrich_potential_levers/outputs.jsonl` — after run status and calls_succeeded
- `history/3/86_enrich_potential_levers/events.jsonl` — gpt-oss-20b "LLM batch interaction failed." errors
- `history/4/14_enrich_potential_levers/events.jsonl` — gpt-oss-20b plan timeouts
- `history/4/14_enrich_potential_levers/outputs/20250329_gta_game/activity_overview.json` — 2 calls, success
- `history/4/14_enrich_potential_levers/outputs/20260310_hong_kong_game/activity_overview.json` — 6 calls, timeout
- `history/4/14_enrich_potential_levers/outputs/20260310_hong_kong_game/log.txt` — "killed after 600s"
- `history/4/17_enrich_potential_levers/outputs/20250321_silo/activity_overview.json` — 15 calls, gpt-4o-mini
- `history/3/89_enrich_potential_levers/outputs/20250321_silo/activity_overview.json` — 13 calls before
- `history/4/17_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json` — metadata context_window=3900
- `history/4/13_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json` — llama3.1 UUID mutation errors
- `baseline/train/20250321_silo/002-10-potential_levers.json` — silo consequences with "30% reduction in innovative output"
- `snapshot/1_deduplicate_levers/20250321_silo/002-11-deduplicated_levers_raw.json` — 15 levers (before run input)
- `baseline/train/20250321_silo/002-11-deduplicated_levers_raw.json` — 7 levers (after run input)
- `PlanExe/worker_plan/worker_plan_internal/lever/enrich_potential_levers.py` lines 28-99 (OPTIMIZE_INSTRUCTIONS), 101-113 (thresholds), 186-200 (adaptive batch), 215-303 (retry logic)
- `analysis/54_enrich_potential_levers/insight_claude.md` — prior analysis baseline

---

## PR Impact

### What the PR Was Supposed to Fix

From the PR description:
1. gpt-oss-20b was failing with BadRequestError because `max_tokens=8192` left only ~3K
   input headroom, and no explicit `context_window` caused llama_index to assume a small
   default. The fix: `max_tokens=65536`, `context_window=131072`.
2. Adaptive batch size for small-context models: `batch_size=2` when `context_window < 6000`.
3. Guarded retry: split on batch failure, skip if budget exceeded.
4. Error tracking: persist errors in raw JSON output.
5. OPTIMIZE_INSTRUCTIONS: document three new known problems.

### Before vs After Comparison

| Metric | Before (runs 85-91) | After (runs 13-19) | Change |
|--------|---------------------|--------------------|--------|
| Overall success rate | 30/35 (85.7%) | 32/35 (91.4%) | **+5.7%** |
| gpt-oss-20b status=ok | 0/5 | 2/5 | **+2** |
| gpt-oss-20b valid output files | 1/5 (partial) | 5/5 | **+4** |
| "LLM batch interaction failed." errors | 2 (run 86) | 0 | **Fixed** |
| All non-oss models status=ok | 30/30 | 30/30 | same |
| Error tracking in JSON | Not present | Working | **New** |
| OpenRouter models batch_size | 1 (full batch) | 2 (adaptive) | Changed |
| % claims in gpt-4o-mini | 0 | 16 | Confounded |
| % claims in haiku | 0 | 16 | Confounded |
| OPTIMIZE_INSTRUCTIONS entries | 6 | 9 | **+3 new** |

### Did the PR Fix the Targeted Issue?

**gpt-oss-20b config fix (max_tokens + context_window): YES.**
The "LLM batch interaction failed." errors are gone. All 5 plans produce valid enriched
lever output. 2/5 plans complete within the orchestrator's 600s timeout; 3/5 time out due
to excessive cross-provider retry overhead (see N1). The core fix works — the BadRequestError
that blocked all progress is eliminated.

**Adaptive batch size: PARTIAL with unintended side effects (N2).**
The intent was to protect small-context models (gpt-oss-20b before the config fix) from
overflow. After the fix, gpt-oss-20b correctly reports `context_window=131072` and is NOT
in the small-batch path. However, three unrelated OpenRouter models (qwen3-30b, gpt-4o-mini,
gemini-flash) trigger the small-batch path because llama_index's `OpenRouter_LLM` reports
`context_window=3900` for all models. These models do not benefit from batch_size=2 and
incur additional API calls.

**Guarded retry: PARTIAL with new timeout issue (N1).**
The retry logic prevents hard failures from propagating, but its aggressive multi-provider
fallover for gpt-oss-20b (6-9 cross-provider calls per plan) causes 3 plans to exceed the
orchestrator's 600s timeout. The output is written; only the status is affected. But a
`status=error` plan is not used by downstream steps, so effectively 3 of 5 plans are
still failing from the orchestrator's perspective.

**Error tracking: YES (P3).**
The `errors` field is populated and catches real issues (llama3.1 UUID mutations, N5).

**OPTIMIZE_INSTRUCTIONS: YES (P4).**
Three new known problems documented; these align with findings from analysis 54.

### Regressions

1. **OpenRouter batch_size=2 side effect (N2)**: qwen3-30b, gpt-4o-mini, gemini-flash are
   now processed in smaller batches due to a metadata reporting bug in llama_index's
   OpenRouter integration. This increases API calls (3-4× more batches) and may affect
   cross-lever reference quality (levers in different batches may not reference each other
   well, as OPTIMIZE_INSTRUCTIONS warns about "Batch boundary blindness").
2. **gpt-oss-20b still at 2/5 status=ok (N1)**: The timeout is a new failure mode that
   replaced the fast failure. Different symptom, different root cause, similar net result
   for the orchestrator.
3. **Percent claims increased (N4)**: Confounded by input difference; cannot attribute
   causally to PR #455 with confidence.

### Verdict: **CONDITIONAL**

The PR fixes the most critical gpt-oss-20b failure (BadRequestError → silent skip) and adds
useful diagnostic infrastructure (error tracking, OPTIMIZE_INSTRUCTIONS updates). But:

- gpt-oss-20b still fails 3/5 plans at the orchestrator level (timeout, not error, but
  effectively the same for the pipeline).
- The adaptive batch size is triggering for unintended models due to OpenRouter's llama_index
  metadata bug (`context_window=3900` universal fallback).
- The guarded retry's multi-provider fallover consumes too much time for gpt-oss-20b.

Follow-up needed:
1. Fix the adaptive batch_size trigger condition — check `num_output < 6000` instead of
   `context_window < 6000`, or use a model-name allowlist, or increase the threshold.
2. Increase the plan timeout for gpt-oss-20b (or reduce the number of provider fallover
   attempts).

---

## OPTIMIZE_INSTRUCTIONS Alignment

The current `OPTIMIZE_INSTRUCTIONS` (lines 28-99) now includes all problems from analysis 54
plus three new entries from PR #455. Alignment check for after runs:

| Problem | Observed in after runs? | Notes |
|---------|------------------------|-------|
| Boilerplate descriptions | Not observed | Descriptions are plan-specific |
| Self-referential synergy/conflict | Not checked systematically | No flagrant examples in spot checks |
| Phantom lever references | Not checked systematically | Small batch_size=2 may worsen cross-batch references |
| Symmetric parroting | Not checked | Not measured |
| Word-count padding | Occasional | Some descriptions are verbose |
| Missing conflict_text | Not observed | All levers have conflict_text |
| Batch boundary blindness | Potential concern | batch_size=2 means 3-4 batches; cross-batch references untested |
| Consequence echoing | 2 errors in run 13 (llama3.1) | UUID mutations caused by consequence text echoing partial UUID |
| UUID format inconsistency | 4 errors in run 13 | "unknown_lever_id" mutations documented |
| max_tokens overflow | Fixed by this PR | No more BadRequestError for gpt-oss-20b |

**New problem to propose adding to OPTIMIZE_INSTRUCTIONS**:
The adaptive batch_size=2 for OpenRouter models (context_window=3900 metadata) may worsen
"Batch boundary blindness" — with only 2 levers per batch context, the LLM has less
visibility of the full lever space when generating synergy/conflict text. The OPTIMIZE_INSTRUCTIONS
should mention: "Small batch sizes (2 levers per call) may reduce inter-lever reference
quality. Ensure the full_lever_context_str is visible and prominent in the prompt, and
consider whether adaptive batch_size=2 is necessary for models with adequate actual context
windows."

---

## Questions For Later Synthesis

1. **What should replace the `context_window < 6000` check?** The `num_output` field (which
   reflects configured max_tokens, not actual capacity) was explicitly avoided per the PR
   description: "context_window is the correct metric — num_output reflects the configured
   max_tokens cap." But context_window=3900 for OpenRouter is wrong. Options: (a) use a
   model-name allowlist/blocklist, (b) use `num_output < 6000` as a fallback signal,
   (c) raise the threshold to something that OpenRouter's 3900 still clears (e.g., 3000
   rather than 6000), (d) disable adaptive batch_size entirely since gpt-oss-20b is now
   correctly configured.

2. **Is batch_size=2 actually harmful for qwen3-30b/gpt-4o-mini/gemini-flash?** All three
   models produce status=ok at 5/5 with batch_size=2. The concern is batch boundary blindness
   (can cross-batch lever references be verified?). Spot-checking synergy/conflict text
   for cross-batch references would answer this.

3. **Why does gpt-oss-20b still take 300-600s for 5-lever plans?** The sovereign_identity
   plan has only 5 levers; with batch_size=5 (normal, since gpt-oss-20b context_window=131072
   is not in the small-batch path), there should be 1 batch. But activity_overview shows
   9 calls. Does gpt-oss-20b always need multiple provider attempts, or is there a structured
   LLM retry happening? Examining the retry budget and depth logic for this model would clarify.

4. **Is the plan timeout (600s) appropriate for gpt-oss-20b?** The multi-provider fallover
   is a feature, not a bug — it makes gpt-oss-20b more reliable. If the enrichment completes
   within 600s but the orchestrator kills it at 600s, the fix is to increase the timeout
   for this step, not to reduce the retry count.

5. **Should the `errors` list include all batch_retry events?** Currently, the `errors`
   field records `batch_retry` events. For run 14 (gpt-oss-20b), the output files show
   no errors in the `errors` list (outputs are complete). Either the retries all succeeded
   without triggering the error recording path, or the errors are only recorded for
   genuinely failed batches. Confirming which events reach the `errors` field would clarify
   the feature's completeness.

---

## Reflect

PR #455 makes a targeted fix (gpt-oss-20b config) that is confirmed to work by the absence
of "LLM batch interaction failed." errors. The remaining gpt-oss-20b failures are a different
problem (orchestrator timeout, not BadRequestError), and importantly the output IS being
written correctly.

The adaptive batch size feature, while well-intentioned, has an unintended reach due to
llama_index's OpenRouter_LLM returning context_window=3900 universally. This is a metadata
integration issue rather than a logic error — the threshold check is sound in principle but
the input value is incorrect. Three production models are now processing at batch_size=2
unnecessarily.

The error tracking (P3) is the PR's most durable contribution: it makes previously-silent
failure modes visible and diagnosable. This will compound in value as the optimization loop
runs more iterations.

The input data discrepancy between before/after runs (snapshot vs baseline/train) is the
biggest confound in this analysis. Synthesis should note that the "improvement" in field
lengths and "increase" in percent claims may both be artifacts of the input change rather
than genuine effects of the PR.

---

## Potential Code Changes

**C1 — Fix adaptive batch_size trigger for OpenRouter models.**
The condition `if context_window < SMALL_CONTEXT_THRESHOLD` fires for all OpenRouter
models (context_window=3900 universal fallback). Options:
- Raise threshold to 3000 to exclude these (since actual models are much larger)
- Use `num_output < 6000` as alternative signal (acknowledging it reflects max_tokens)
- Use a model-name allowlist
- Remove the adaptive feature entirely, since the original target (gpt-oss-20b) is now
  correctly configured with context_window=131072
Evidence: `enrich_potential_levers.py:194-196`

**C2 — Increase plan timeout or per-step timeout for gpt-oss-20b.**
gpt-oss-20b with multi-provider fallover regularly takes 300-600s per plan. The orchestrator's
600s plan timeout is too tight. Either increase the timeout for this step or add a model-specific
timeout override.
Evidence: `history/4/14_enrich_potential_levers/outputs/20250321_silo/activity_overview.json`,
`history/4/14_enrich_potential_levers/events.jsonl`

**H1 — Validate cross-batch lever references for small-batch models.**
With batch_size=2, qwen3-30b, gpt-4o-mini, and gemini-flash process 2 levers per call
while seeing the full lever list in context. Verify empirically whether synergy_text and
conflict_text reference levers from other batches at the same rate as single-batch processing.
If reference quality drops, either revert batch_size=2 for these models or strengthen the
prompt instruction ("You MUST reference levers from the FULL LIST, not only levers in
the current batch").

**H2 — Separate the experiment inputs (snapshot vs baseline/train).**
The before/after comparison in this analysis is confounded by different input datasets.
Future iterations should ensure both before and after runs use the same input. Either
migrate to baseline/train for all experiments, or re-run the before baseline on baseline/train.

---

## Summary

PR #455 provides a confirmed fix for gpt-oss-20b's primary failure mode (BadRequestError
from max_tokens=8192 overflow), increasing the valid-output rate for that model from 0/5
to 5/5 plans (even if only 2/5 complete within the orchestrator's 600s timeout). Error
tracking is a valuable new diagnostic feature. OPTIMIZE_INSTRUCTIONS gained three new
entries that document real problems.

The two significant concerns are:
1. The adaptive batch_size=2 is unintentionally triggering for three OpenRouter models
   (qwen3-30b, gpt-4o-mini, gemini-flash) because llama_index's OpenRouter integration
   reports context_window=3900 universally — a metadata bug, not a model capability.
2. gpt-oss-20b still has 3/5 plans at status=error (timeout) because the guarded retry's
   cross-provider fallover consumes 300-600s per plan, exceeding the orchestrator limit.

Field length and percent-claim comparisons are confounded by a change in input data
(snapshot/1_deduplicate_levers [15-18 levers] vs baseline/train [7-8 levers]) between the
before and after experiments.

**Verdict: CONDITIONAL.** Keep the max_tokens/context_window fix and error tracking. Follow
up on the adaptive batch_size trigger condition and the gpt-oss-20b plan timeout.
