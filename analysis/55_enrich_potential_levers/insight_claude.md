# Insight Claude

## Overview

This analysis evaluates **PR #452** ("Add per-batch retry for enrich step, update OPTIMIZE_INSTRUCTIONS")
against the baseline established in analysis 54. The PR makes three changes:

- **B1**: Per-batch retry — failed batches are split in half and retried; single-lever failures are
  skipped rather than aborting the plan.
- **B4**: `runner.py` now reports the actual `batches_succeeded` count instead of hardcoding `1`.
- **D5**: Two new known-problem entries added to `OPTIMIZE_INSTRUCTIONS` (consequence echoing without
  elaboration, UUID cross-reference format inconsistency). Documentation only — no runtime effect.

**Input**: `snapshot/1_deduplicate_levers` (same as analyses 53 and 54 — valid for comparison)

**Runs compared**:

| Before (analysis 54) | After (analysis 55) | Model |
|----------------------|---------------------|-------|
| `3/85_enrich_potential_levers` | `3/92_enrich_potential_levers` | ollama-llama3.1 |
| `3/86_enrich_potential_levers` | `3/93_enrich_potential_levers` | openrouter-gpt-oss-20b |
| `3/87_enrich_potential_levers` | `3/94_enrich_potential_levers` | openai-gpt-5-nano |
| `3/88_enrich_potential_levers` | `3/95_enrich_potential_levers` | openrouter-qwen3-30b-a3b |
| `3/89_enrich_potential_levers` | `3/96_enrich_potential_levers` | openrouter-gpt-4o-mini |
| `3/90_enrich_potential_levers` | `3/97_enrich_potential_levers` | openrouter-gemini-2.0-flash-001 |
| `3/91_enrich_potential_levers` | `3/98_enrich_potential_levers` | anthropic-claude-haiku-4-5-pinned |

---

## Negative Things

### N1 — gpt-oss-20b still fails 3/5 plans (now via timeout instead of fast failure)

After the retry mechanism, gpt-oss-20b improved from 0/5 to 2/5, but three plans
(sovereign_identity, hong_kong_game, parasomnia_research_unit) now timeout after 600s instead of
failing immediately.

Run 93 events.jsonl:
```
run_single_plan_error: sovereign_identity  — plan timeout after 600s
run_single_plan_error: parasomnia          — plan timeout after 600s
run_single_plan_error: hong_kong_game      — plan timeout after 600s
```

The retry mechanism itself causes this: each failed batch consumes its full duration before the
split is attempted. With gpt-oss-20b routinely producing 8192 output tokens (at the model limit),
multi-batch plans accumulate enough retry overhead to exceed the 600s plan timeout.

Evidence: `history/3/93_enrich_potential_levers/events.jsonl`

### N2 — gpt-oss-20b context window (3900 tokens) makes batch failures systematic

The `metadata` field in run 93 silo output records:
```json
{"context_window": 3900, "num_output": 8192, "model_name": "openai/gpt-oss-20b"}
```
With BATCH_SIZE=5 levers and detailed consequences+options+review per lever in the prompt, gpt-oss-20b
consistently produces output at or near the 8192-token hard limit. The usage_metrics.jsonl for run 93
silo confirms this pattern: one batch produced exactly 8192 output tokens (DeepInfra provider) and was
returned as invalid JSON.

```
DeepInfra: input_tokens=2548, output_tokens=8192  → invalid_json (triggers split)
Amazon Bedrock (half-1): input_tokens=1968, output_tokens=3201 (success)
Amazon Bedrock (half-2): input_tokens=2139, output_tokens=7504 (success)
```

Evidence: `history/3/93_enrich_potential_levers/outputs/20250321_silo/usage_metrics.jsonl`

The root issue is not fixed: BATCH_SIZE=5 produces output that overflows gpt-oss-20b's output token
limit on nearly every batch. The retry mechanism compensates but the compensation is expensive.

### N3 — Timeout now uses runner time budget wastefully for gpt-oss-20b

Before PR #452, gpt-oss-20b failures were fast: run 86 showed hong_kong_game failing in 27s and
gta_game in 31s with "LLM batch interaction failed." After the retry mechanism, the same plans now
use the entire 600s budget before failing.

For gpt-oss-20b runs:
- Before: 0/5 succeeded, failures were 27–31s (fast) or 600s (slow timeout)
- After: 2/5 succeeded (195s, 229s), 3 timed out at 600s each = 1800s consumed

This means PR #452 changed gpt-oss-20b's failure mode from "mostly fast failure" to "always slow
timeout," which consumes significantly more runner wall-clock time per run.

### N4 — UUID cross-reference still present in `full_lever_context_str`

`enrich_potential_levers.py` line 168 still reads:
```python
full_lever_context_str = "\n".join([f"- {lever.lever_id}: {lever.name}" for lever in levers_to_characterize])
```
D5 documented UUID cross-reference format inconsistency as a known problem, but the underlying code
change was not included in this PR. The full_lever_context_str continues to expose raw UUIDs to the
LLM, which remain visible in outputs from UUID-sensitive models (llama3.1, run 92):

> "Information Control Protocols conflicts with Knowledge Preservation Strategy
> (9bc93565-67b1-49fc-afb9-4d310510f698)"

Evidence: `history/3/92_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json`,
lever "Information Control Protocols" conflict_text.

### N5 — D5 OPTIMIZE_INSTRUCTIONS update has no runtime effect

The two new known-problem entries added to OPTIMIZE_INSTRUCTIONS ("Consequence echoing without
elaboration" and "UUID cross-reference format inconsistency") are self-improve documentation only
and are not injected into the runtime system prompt. Content quality for all 6 working models is
unchanged — variations are within stochastic noise (see Quantitative Metrics).

---

## Positive Things

### P1 — B1 retry mechanism works: gpt-oss-20b improved from 0/5 to 2/5

The two successful plans (silo and gta_game) demonstrate that the retry mechanism functions
correctly. Usage metrics for silo show one batch failure (8192 output tokens, invalid JSON) followed
by two successful sub-batch completions:

```
Clarifai  — success (2574 in, 5397 out)
DeepInfra — success on retry pass 1 (2548 in, 8192 out) but invalid_json
Amazon Bedrock (sub-batch 1) — success (1968 in, 3201 out)
Amazon Bedrock (sub-batch 2) — success (2139 in, 7504 out)
DeepInfra — success (2570 in, 6151 out)
```

Final calls_succeeded for silo: 4 (3 original batches + 1 retry sub-batch pair = 4 successes, 1 failure).
Evidence: `history/3/93_enrich_potential_levers/outputs/20250321_silo/usage_metrics.jsonl`

### P2 — B4 fix confirmed: calls_succeeded now reports actual batch counts

Before (runs 85–91): all plans reported `calls_succeeded: 1` regardless of the actual number of
LLM calls made (silo has 3 batches for 15 levers, gta_game has 4 for 20 levers with BATCH_SIZE=5).

After (runs 92–98): actual counts are reported:
- llama3.1 (run 92): silo=3, gta_game=4, sovereign_identity=3, hong_kong_game=3, parasomnia=4
- haiku (run 98): silo=3, gta_game=4, sovereign_identity=3, hong_kong_game=3, parasomnia=4

This confirms the B4 fix is working. Evidence: `history/3/92_enrich_potential_levers/outputs.jsonl`
vs `history/3/85_enrich_potential_levers/outputs.jsonl`.

### P3 — No LLMChatError entries for the 6 working models

Events.jsonl for all 6 non-gpt-oss-20b runs (92, 94, 95, 96, 97, 98) contain no error events.
Schema validation continues to work correctly.

### P4 — qwen3-30b CJK character leak did not recur in run 95

Analysis 54 noted one CJK character ("封锁") in qwen3-30b run 88 silo plan. A CJK scan of all
5 plans in run 95 (qwen3-30b after) found no occurrences. The single occurrence appears to have
been stochastic rather than systematic.

Evidence: CJK scan of all 25 output files for runs 88 and 95 (`characterized_levers[*].conflict_text`,
`synergy_text`, `description`). Only match was run 88, silo, lever "External Engagement Policy" conflict_text.

### P5 — Content quality for 6 working models is stable (no regression)

All non-gpt-oss-20b models show field length changes within ±7% of their run 85–91 baselines,
which is within normal stochastic variation for non-deterministic LLM outputs. No template
artifacts, no fabricated percentage claims, no CJK leaks. The quality preserved from PR #451
has not regressed.

---

## Comparison

### Comparison vs Baseline Training Data

Baseline (from `baseline/train/`, all plans): desc=484 chars, syn=286 chars, conf=298 chars.

| Model | Desc (after) | Desc ratio | Syn (after) | Syn ratio | Conf (after) | Conf ratio |
|-------|-------------|------------|-------------|-----------|--------------|------------|
| llama3.1 | 339 | 0.70× | 360 | 1.26× | 368 | 1.23× |
| gpt-oss-20b | 650* | 1.34×* | 382* | 1.34×* | 369* | 1.24×* |
| gpt-5-nano | 647 | 1.34× | 339 | 1.19× | 349 | 1.17× |
| qwen3-30b | 375 | 0.78× | 202 | 0.71× | 220 | 0.74× |
| gpt-4o-mini | 492 | 1.02× | 269 | 0.94× | 297 | 1.00× |
| gemini | 456 | 0.94× | 284 | 0.99× | 292 | 0.98× |
| haiku | 581 | 1.20× | 464 | 1.62× | 477 | 1.60× |

\* gpt-oss-20b after values include 3 partial outputs from timed-out plans; only 2/5 plans truly
succeeded. These averages are not directly comparable.

No model exceeds 2× on any field after this PR (haiku syn/conf at 1.6× is the same as before).
No fabricated percentage claims observed. No marketing-copy language detected.

### Comparison vs Prior Runs (before this PR)

The only material change is gpt-oss-20b success rate (0/5 → 2/5). All other models are stable:

| Model | Desc before | Desc after | Change | Syn before | Syn after | Change |
|-------|-------------|------------|--------|------------|-----------|--------|
| llama3.1 | 316 | 339 | +7.3% | 372 | 360 | −3.2% |
| gpt-5-nano | 658 | 647 | −1.7% | 332 | 339 | +2.1% |
| qwen3-30b | 372 | 375 | +0.8% | 213 | 202 | −5.2% |
| gpt-4o-mini | 482 | 492 | +2.1% | 279 | 269 | −3.6% |
| gemini | 456 | 456 | 0.0% | 275 | 284 | +3.3% |
| haiku | 568 | 581 | +2.3% | 453 | 464 | +2.4% |

All changes are within the ±7% range expected from non-deterministic model outputs with no prompt
changes. None of these changes are attributable to PR #452.

### Silo Plan Field Lengths (consistent per-plan reference)

| Model | Run | Desc | Syn | Conf |
|-------|-----|------|-----|------|
| Baseline | — | 504 | 312 | 331 |
| llama3.1 | 85 (before) | 329 | 386 | 420 |
| llama3.1 | 92 (after) | 430 | 357 | 384 |
| gpt-5-nano | 87 (before) | 687 | 339 | 355 |
| gpt-5-nano | 94 (after) | 656 | 363 | 373 |
| qwen3-30b | 88 (before) | 331 | 163 | 173 |
| qwen3-30b | 95 (after) | 355 | 170 | 190 |
| gpt-4o-mini | 89 (before) | 477 | 287 | 316 |
| gpt-4o-mini | 96 (after) | 499 | 266 | 310 |
| gemini | 90 (before) | 441 | 291 | 299 |
| gemini | 97 (after) | 436 | 321 | 323 |
| haiku | 91 (before) | 543 | 452 | 478 |
| haiku | 98 (after) | 563 | 429 | 446 |
| gpt-oss-20b | 93 (after) | 652 | 395 | 366 |

### Model Ranking (quality + reliability, after PR)

1. **haiku-4-5** — Richest descriptions (1.20× baseline), grounded synergy/conflict. 100% success.
2. **gpt-5-nano** — Good description length (1.34×), natural prose (template eliminated by PR #451). 100%.
3. **gpt-4o-mini** — Near-baseline lengths. Clean, compact, consistent. 100%.
4. **gemini-2.0-flash** — Near-baseline lengths. Stable, no regression. 100%.
5. **llama3.1** — Below-baseline descriptions (0.70×), still showing objectives/key-metrics structure.
   100% but content remains shallower than baseline.
6. **qwen3-30b** — Terse synergy/conflict (0.74× baseline). No CJK this run. 100%.
7. **gpt-oss-20b** — 2/5 success (up from 0/5). 3 plans timeout. Output consistently at 8192-token
   limit due to small context_window (3900 tokens) and verbose enrichment format.

---

## Quantitative Metrics

### Success Rate

| Run pair | Model | Before | After | Change |
|----------|-------|--------|-------|--------|
| 85→92 | llama3.1 | 5/5 | 5/5 | same |
| 86→93 | gpt-oss-20b | 0/5 | 2/5 | **+2** (3 timeout) |
| 87→94 | gpt-5-nano | 5/5 | 5/5 | same |
| 88→95 | qwen3-30b | 5/5 | 5/5 | same |
| 89→96 | gpt-4o-mini | 5/5 | 5/5 | same |
| 90→97 | gemini | 5/5 | 5/5 | same |
| 91→98 | haiku | 5/5 | 5/5 | same |
| **Total** | | **30/35 (85.7%)** | **32/35 (91.4%)** | **+2** |

### calls_succeeded Reporting (B4 fix)

| Model | Before (example plan) | After (example plan) | Notes |
|-------|----------------------|---------------------|-------|
| llama3.1 | `"calls_succeeded": 1` | `"calls_succeeded": 3` | silo has 15 levers, 3 batches of 5 |
| gpt-5-nano | `"calls_succeeded": 1` | `"calls_succeeded": 3` | silo |
| qwen3-30b | `"calls_succeeded": 1` | `"calls_succeeded": 3` | silo |
| haiku | `"calls_succeeded": 1` | `"calls_succeeded": 3` | silo |
| gpt-oss-20b | `"calls_succeeded": null` | `"calls_succeeded": 4` | silo (3 orig + 1 retry) |

### Template Leakage and Constraint Violations

| Violation Type | Before (85–91) | After (92–98) |
|----------------|----------------|---------------|
| Missing description | 0 | 0 |
| Missing synergy_text | 0 | 0 |
| Missing conflict_text | 0 | 0 |
| Plan timeouts | 3 (run 86) | 3 (run 93) |
| Fabricated % claims | 0 | 0 |
| CJK characters | 1 (run 88, qwen3-30b, silo) | 0 |
| UUID refs in text (llama3.1) | Present | Present (unchanged) |

### LLM Call Volume Increase for gpt-oss-20b

With the retry mechanism, the total LLM calls for gpt-oss-20b increase significantly on retry plans:

| Plan | Before calls | After calls | Notes |
|------|-------------|-------------|-------|
| silo | 0 (failed immediately) | 5 (4 success, 1 failure) | retry triggered once |
| gta_game | 0 (failed immediately) | 6 (5 success, 1 failure) | retry triggered once |
| sovereign_identity | ~3 (timeout) | ~? (timeout at 600s) | partial output: 14 levers |

---

## PR Impact

### What the PR Was Supposed to Fix

From the PR description:
- **B1**: Enrich step retries failed batches by splitting in half. Fixes gpt-oss-20b's 0/5 failure
  caused by output token limits on large batches.
- **B4**: `runner.py` reports actual `batches_succeeded` count (was hardcoded `1`).
- **D5**: Documents two new known problems in `OPTIMIZE_INSTRUCTIONS`.

### Before vs After Comparison Table

| Metric | Before (runs 86, 85–91) | After (runs 93, 92–98) | Change |
|--------|-------------------------|------------------------|--------|
| gpt-oss-20b success rate | 0/5 | 2/5 | **+2 plans** |
| gpt-oss-20b timeout plans | 3/5 (silo, sovereign, parasomnia) | 3/5 (sovereign, hong_kong, parasomnia) | same count, different plans |
| All other models success | 30/30 | 30/30 | none |
| Overall success rate | 30/35 (85.7%) | 32/35 (91.4%) | +5.7% |
| calls_succeeded (hardcoded 1) | Yes (all runs 85–91) | No (correct counts) | **Fixed** |
| Retry events in usage_metrics | N/A (no retry) | 2 retries (silo, gta_game) | **Working** |
| gpt-oss-20b wall-clock per run | ~1800s (3×600s) + 2×fast-fail | ~2200s (3×600s + 195s + 229s) | slightly worse |
| Content quality (working models) | baseline | unchanged (±7%) | none |
| CJK leak (qwen3-30b) | 1 instance | 0 instances | resolved (stochastic) |
| UUID refs in full_lever_context | Present | Present (unchanged) | not fixed |

### Did the PR Fix the Targeted Issue?

**B1 — Partially yes.** The retry mechanism works and recovered 2 plans for gpt-oss-20b. The
silo plan's usage metrics directly confirm the split-batch recovery. However, the root cause
(BATCH_SIZE=5 producing output that exceeds 8192 tokens for gpt-oss-20b's verbose format) is not
addressed. The retry adds cost and latency without eliminating the failure mode.

The 3 remaining timeouts are a new failure pattern: previously, gpt-oss-20b plans failed quickly
with "LLM batch interaction failed"; now they consume the full 600s budget via chained retries
that cannot complete in time. This is a trade-off: 2 plans recovered, 3 plans now fail more slowly.

**B4 — Yes.** Confirmed: all after-PR runs report actual calls_succeeded counts.

**D5 — No runtime impact.** OPTIMIZE_INSTRUCTIONS is documentation only; no content quality
changes are expected or observed.

### Regressions

1. **gpt-oss-20b timeout behavior** (N1, N3): Three plans now always timeout (600s each) instead
   of failing fast. Total runner time for gpt-oss-20b increased from ~1800s+62s to ~2200s per run.
   This is a regression in runner efficiency.
2. **UUID format fix not included** (N4): D5 documented the UUID issue but did not fix line 168.

### Verdict: **CONDITIONAL**

B1 partially works (2 plans recovered), B4 is cleanly fixed. However, the retry mechanism introduces
a systematic timeout pattern for larger gpt-oss-20b plans that adds ~1800s of wasted runner time
per test run. The PR should be kept for the B4 fix and the 2-plan improvement, but the retry
strategy needs a follow-up to prevent excessive timeout consumption:

- **Required follow-up**: Reduce BATCH_SIZE for models with small context windows (gpt-oss-20b
  has context_window=3900), or add a maximum retry depth (1 level only), or use a per-batch
  timeout budget to skip retries when insufficient time remains.

---

## Evidence Notes

Files consulted:

- `history/3/92–98_enrich_potential_levers/outputs.jsonl` — success/failure counts, calls_succeeded
- `history/3/85–91_enrich_potential_levers/outputs.jsonl` — before-PR success counts (all calls_succeeded=1)
- `history/3/93_enrich_potential_levers/events.jsonl` — 3 timeout events
- `history/3/86_enrich_potential_levers/events.jsonl` — 5 failure events (fast + timeout)
- `history/3/93_enrich_potential_levers/outputs/20250321_silo/usage_metrics.jsonl` — retry evidence
- `history/3/93_enrich_potential_levers/outputs/20250329_gta_game/usage_metrics.jsonl` — retry evidence
- `history/3/92–98_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json` — content quality
- `history/3/85_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json` — before llama3.1
- `history/3/93_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json` — gpt-oss-20b content
- `history/3/98_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json` — haiku content
- `baseline/train/*/002-12-enriched_levers_raw.json` — baseline field lengths
- `PlanExe/worker_plan/worker_plan_internal/lever/enrich_potential_levers.py` lines 27–92, 155–266

---

## OPTIMIZE_INSTRUCTIONS Alignment

The current OPTIMIZE_INSTRUCTIONS (lines 27–92 in `enrich_potential_levers.py`) now lists:
boilerplate descriptions, self-referential synergy/conflict, phantom lever references, symmetric
parroting, word-count padding, missing conflict_text, batch boundary blindness, consequence echoing
without elaboration (new in D5), UUID cross-reference format inconsistency (new in D5).

**Alignment check for after-PR runs**:

| Problem | Observed? | Notes |
|---------|-----------|-------|
| Boilerplate descriptions | Minimal | No model shows identical templates across all levers |
| Self-referential synergy/conflict | Not observed | Spot checks clean |
| Phantom lever references | Not systematically checked | Spot checks show valid lever names |
| Symmetric parroting | Present (llama3.1) | "Strong synergy exists with X... Additionally, X has a positive interaction with Y" |
| Word-count padding | Reduced vs pre-#451 | No "It is important to note that..." patterns visible |
| Missing conflict_text | Not observed | All levers have conflict_text |
| Batch boundary blindness | Not tested | Would require cross-batch reference audit |
| Consequence echoing (new D5) | Partially present (llama3.1) | Run 92 shows "Its objectives are / Key success metrics include" which is better than pure echoing in run 85 |
| UUID cross-reference (new D5) | Present (llama3.1, run 92) | "conflicts with Knowledge Preservation Strategy (9bc93565-67b1-49fc-afb9-4d310510f698)" |

**New observation not yet in OPTIMIZE_INSTRUCTIONS**:
- **Small-context-window models need adaptive BATCH_SIZE**: gpt-oss-20b's context_window=3900 means
  that even though BATCH_SIZE=5 fits within the input context, the output for 5 enriched levers
  consistently exceeds 8192 output tokens. The OPTIMIZE_INSTRUCTIONS could document this as a known
  infrastructure problem: "Models with context_window < 8000 tokens or strict output limits
  will consistently produce truncated JSON at BATCH_SIZE=5. Use per-model BATCH_SIZE configuration."

---

## Questions For Later Synthesis

1. **Should BATCH_SIZE be model-adaptive?** gpt-oss-20b's context_window=3900 is visible at
   runtime. Could the runner reduce BATCH_SIZE to 2 for models where `context_window < 8000`?
   This would prevent the 8192-token output overflow and eliminate the root cause for gpt-oss-20b.

2. **Should the retry have a depth limit?** The current implementation retries indefinitely until
   the plan timeout is hit. A maximum depth of 1 (split once, never split sub-batches) plus a
   remaining-time check before retrying would prevent the timeout exhaustion observed in run 93.

3. **Is UUID fix (B2) still the next priority?** D5 documented UUID cross-reference format
   inconsistency in OPTIMIZE_INSTRUCTIONS, but line 168 still includes `lever.lever_id` in
   `full_lever_context_str`. After analysis 54's concern about qwen3-30b UUID nondeterminism,
   should this be a dedicated PR to fix line 168?

4. **Is llama3.1's consequence echoing sufficiently improved?** Run 92 shows "Its objectives are /
   Key success metrics include" structure (avg desc 339 chars vs 316 before), which is richer than
   run 85's pure echoing but still below baseline (0.70×). Is this acceptable, or should the
   system prompt add an explicit elaboration instruction?

5. **What is the priority ordering?** From most to least impactful remaining issues:
   - C1: Adaptive BATCH_SIZE for small-context models (fixes gpt-oss-20b root cause)
   - C2: Fix UUID in `full_lever_context_str` (line 168, name-only format)
   - C3: Retry depth limit + time budget guard (prevents slow timeout pattern)
   - H1: System prompt elaboration guidance for llama3.1 (content quality improvement)

---

## Reflect

PR #452 made two concrete improvements: B1 (retry) recovered gpt-oss-20b from 0/5 to 2/5, and
B4 fixed the misleading `calls_succeeded=1` reporting. The D5 documentation update is housekeeping
that costs nothing at runtime.

The limitation is that B1 treats symptoms rather than the root cause. gpt-oss-20b's context_window
is 3900 tokens and its output cap is 8192 tokens. With 5 levers per batch and detailed
consequences/review in the prompt, every batch for this model is near its output limit. The split-
and-retry strategy rescues 2 of 5 plans, but the 3 remaining failures are simply too large for the
model to complete within the 600s plan budget even with splitting.

The ideal fix is adaptive: detect that gpt-oss-20b has a small context window and set BATCH_SIZE=2
or BATCH_SIZE=3 for it. This would prevent output overflow in the first place, eliminate the retry
overhead, and likely recover all 5 plans.

The quality improvements from PR #451 (gpt-5-nano template elimination, grounded conflict texts)
have been successfully preserved through this PR. None of the 6 working models regressed.

---

## Potential Code Changes

**C1 (critical)** — Add per-model BATCH_SIZE based on context window.
`enrich_potential_levers.py` currently hardcodes `BATCH_SIZE = 5` (line 95). gpt-oss-20b with
context_window=3900 and num_output=8192 needs BATCH_SIZE=2 or 3 to prevent output token overflow.
The runner has access to `llm.metadata["context_window"]` — use it to select a smaller batch size
when context_window < 8000.
Expected effect: gpt-oss-20b recovers all 5 plans without triggering retries.
Evidence: `history/3/93_enrich_potential_levers/outputs/20250321_silo/usage_metrics.jsonl` —
consistent 8192-token output overflow pattern across all gpt-oss-20b batches.

**C2 (improvement)** — Fix `full_lever_context_str` to name-only format.
Line 168: `f"- {lever.lever_id}: {lever.name}"` → `f"- {lever.name}"`.
Expected effect: eliminates UUID references from synergy/conflict texts for UUID-sensitive models
(llama3.1, and potentially qwen3-30b's inconsistent format).
Evidence: `history/3/92_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json`
— conflict_text contains full 36-char UUID `(9bc93565-67b1-49fc-afb9-4d310510f698)`.

**C3 (improvement)** — Add retry depth limit and remaining-time guard.
In the retry exception handler (lines 239–250), before inserting sub-batches into pending_batches,
check: if the sub-batch size would be 1 or smaller, or if remaining wall-clock time is < 60s, skip
the retry and log the skip. This prevents the 3×600s timeout pattern seen in run 93.
Expected effect: gpt-oss-20b's 3 failing plans fail at ~60–120s instead of 600s, reducing runner
time waste from ~1800s to ~300s.

**H1 (prompt)** — Add explicit elaboration guidance to system prompt for descriptions.
Current description guidance: "(80-100 words) Clearly explain the lever's purpose, what it controls,
its objectives, and key success metrics." llama3.1 produces 0.70× baseline despite this.
Adding: "Do not simply restate the lever's consequences. Use the consequences as grounding context,
but elaborate on purpose, scope, and decision-relevant implications." may help llama3.1 recover.
Expected effect: llama3.1 description length returns toward 0.80–0.90× baseline.
Risk: may inflate content for strong models that already produce adequate elaboration.

---

## Summary

PR #452 ("Add per-batch retry for enrich step, update OPTIMIZE_INSTRUCTIONS") produced a
**partial, conditional improvement**:

**What worked:**
- gpt-oss-20b recovered from 0/5 to 2/5 success (B1 retry confirmed working via usage metrics)
- `calls_succeeded` now reports actual batch counts instead of hardcoded `1` (B4 cleanly fixed)
- D5 documentation added two accurately identified known problems to OPTIMIZE_INSTRUCTIONS

**What remains:**
- 3/5 gpt-oss-20b plans still fail — now via 600s timeout rather than fast failure
- The retry adds overhead (~1800s extra wall-clock time) without fixing the root cause
- UUID cross-reference format (line 168) unchanged
- llama3.1 still below baseline description length (0.70×)

**Root cause not yet addressed:** gpt-oss-20b's context_window=3900 means BATCH_SIZE=5 reliably
overflows its output token limit. Adaptive BATCH_SIZE (C1) would likely recover all 5 plans
without any retry overhead.

**Verdict: CONDITIONAL.** Keep for B4 (clean fix). Keep B1 as a safety net, but add C1 (adaptive
BATCH_SIZE) and C3 (retry depth limit) as immediate follow-ups to prevent systematic timeout
exhaustion for gpt-oss-20b on larger plans.
