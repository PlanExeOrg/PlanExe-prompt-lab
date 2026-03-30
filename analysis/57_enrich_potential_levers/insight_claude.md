# Insight Claude

## Overview

This analysis evaluates **PR #454** ("Adaptive batch size, guarded retry, and max_tokens
bump for enrich step") against runs 3/85–3/91 (post-PR #451, pre-PR #454).

**Run-to-model mapping:**

| Before PR | After PR | Model |
|-----------|----------|-------|
| `3/85` | `4/06` | ollama-llama3.1 |
| `3/86` | `4/07` | openrouter-openai-gpt-oss-20b |
| `3/87` | `4/08` | openai-gpt-5-nano |
| `3/88` | `4/09` | openrouter-qwen3-30b-a3b |
| `3/89` | `4/10` | openrouter-openai-gpt-4o-mini |
| `3/90` | `4/11` | openrouter-gemini-2.0-flash-001 |
| `3/91` | `4/12` | anthropic-claude-haiku-4-5-pinned |

**Important confound**: The input baseline was regenerated between runs 3/91 and 4/06.
Before-PR runs enriched 14–18 levers per plan (from 002-10, full potential levers set).
After-PR runs enrich 5–8 levers per plan (from the correctly deduped set, matching
baseline 002-12). This makes direct quality comparisons between before and after runs
unreliable — only the operational reliability metrics (success rate, error types,
durations) can be cleanly attributed to PR #454.

---

## Negative Things

### N1 — gpt-oss-20b still fails 3 of 5 plans (new overflow failure mode)

After the PR, gpt-oss-20b (run 4/07) shows `status: "ok"` for all 5 plans in
`outputs.jsonl`, but produces zero `characterized_levers` for sovereign_identity,
hong_kong_game, and parasomnia_research_unit.

Root cause: the max_tokens bump (8192 → 128000) combined with the model's
actual context window of 131072 leaves only 131072 − 128000 = **3072 tokens** for
input text. The system prompt + full lever context already consumes more than 3072 tokens
for these three plans, so every batch — including single-lever batches (depth=1) — fails
with a `BadRequestError`:

```
"you requested about 131909 tokens (3909 of text input, 128000 in the output).
 Please reduce the length of either one..."
```

Evidence: `history/4/07_enrich_potential_levers/outputs/20260308_sovereign_identity/
002-12-enriched_levers_raw.json` contains 12 error entries (3 `batch_retry`, 3×2
`batch_skipped`, 5 `incomplete`) and 0 `characterized_levers`. The input token counts
for individual levers (3675–3909) all exceed the 3072-token input budget.

The two plans that do succeed (silo: 7 levers, gta: 8 levers) have shorter context
(≤3072 input tokens per batch), so the 4 batches of 2 levers each complete without overflow.

**This is a silent failure**: the plan-level `status` in `outputs.jsonl` is `"ok"` and
`calls_succeeded: 0`. Downstream steps will receive an empty lever list.

### N2 — llama3.1 consequence echoing and UUID leakage persist (unchanged)

Both issues documented in the previous assessment are unchanged by PR #454:

- **Consequence echoing**: llama3.1 descriptions show 28–45% word overlap with the
  input `consequences` field and average 358 chars (0.74× baseline avg of 484 chars).
  Source: `history/4/06_enrich_potential_levers/outputs/20250321_silo/
  002-12-enriched_levers_raw.json`, e.g., "Ethical Oversight Framework: This lever
  controls the decision-making process within the silo, ensuring that ethical
  considerations are made..." — echoes consequences rather than elaborating on purpose
  and scope.

- **UUID leakage (B2)**: llama3.1 injects 7–16 full UUIDs per plan in `synergy_text`
  and `conflict_text` (e.g., "Information Control Strategy (b35d92a2-c2a2-42e9-9836-
  eee6bae98898)"). Source: `history/4/06_enrich_potential_levers/outputs/20250321_silo/
  002-12-enriched_levers_raw.json`. Root cause is unchanged at source line 198:
  `full_lever_context_str = "\n".join([f"- {lever.lever_id}: {lever.name}" ...])`.

### N3 — llama3.1 unknown_lever_id hallucination (new)

Run 4/06, gta_game: 1 error of type `unknown_lever_id` for lever `056fa843-...`. llama3.1
returned a characterization for a lever ID that does not exist in the input set. That lever
is logged as `incomplete` and excluded from the output. The final gta_game output has 7
characterized levers instead of 8.

Source: `history/4/06_enrich_potential_levers/outputs/20250329_gta_game/
002-12-enriched_levers_raw.json` — `errors` array: `[{"type": "unknown_lever_id", ...},
{"type": "incomplete", ...}]`.

The UUID leakage (B2) is likely a contributing factor: when `full_lever_context_str`
includes UUIDs, llama3.1 may construct a plausible-looking but incorrect UUID from memory
fragments.

---

## Positive Things

### P1 — Guarded retry prevents 600-second timeouts for gpt-oss-20b

Before the PR, gpt-oss-20b ran for the full 600-second plan timeout before failing
(3/5 plans timed out; 2/5 failed quickly with "LLM batch interaction failed").
After the PR, failures are detected within 2 seconds via `BadRequestError` and the
guarded retry logic immediately skips to the next lever. Total run time for a failing
plan: ≤2 seconds vs 600 seconds before.

Evidence: `history/3/86_enrich_potential_levers/events.jsonl` shows three
`"plan timeout after 600s"` entries. `history/4/07_enrich_potential_levers/events.jsonl`
shows `run_single_plan_complete` at 0.98s, 1.09s, and 1.73s for the three failing plans.

### P2 — gpt-oss-20b achieves partial success for 2 of 5 plans (was 0/5)

Silo and gta_game (the two plans with shortest input context) are now fully enriched:
7 and 8 `characterized_levers` respectively, with no errors. Before the PR, gpt-oss-20b
produced zero characterized levers for all 5 plans.

Source: `history/4/07_enrich_potential_levers/outputs/20250321_silo/
002-12-enriched_levers_raw.json` — 7 levers with complete `description`, `synergy_text`,
and `conflict_text`. `activity_overview.json` shows 4 successful calls across 3 providers
(Chutes, DeepInfra, Parasail) totaling 18,906 tokens.

### P3 — Accurate batch counting now implemented

Before the PR, `calls_succeeded` was hardcoded to 1 in `runner.py:184` regardless of
how many batches actually succeeded. After the PR, the actual batch count is reported.

Evidence: `history/4/07_enrich_potential_levers/outputs.jsonl` shows
`calls_succeeded: 4` for silo and gta_game (4 batches of 2 levers each for 7–8 levers
at batch_size=2), and `calls_succeeded: 0` for the three failing plans. Before the PR,
`history/3/86_enrich_potential_levers/outputs.jsonl` showed `calls_succeeded: null`
for all failures (the hardcoded path was never reached on error).

### P4 — No LLMChatError / schema validation failures in any after-PR run

None of the 7 after-PR runs (35 plan executions) generated `LLMChatError` entries in
their `events.jsonl` files. The Pydantic schema for `BatchCharacterizationResult` is
passing cleanly across all models. The only errors are `unknown_lever_id` (llama3.1,
1 occurrence) and `BadRequestError` overflows (gpt-oss-20b, 3 plans).

### P5 — Content quality holds within acceptable range for all successful models

After-PR field lengths vs baseline across all 5 plans:

| Model | Desc | Desc/base | Syn | Syn/base | Conf | Conf/base |
|-------|------|-----------|-----|----------|------|-----------|
| **baseline avg** | **484** | **1.0×** | **287** | **1.0×** | **300** | **1.0×** |
| llama3.1 | 358 | 0.74× | 337 | 1.17× | 336 | 1.12× |
| gpt-oss-20b† | 626 | 1.29× | 371 | 1.29× | 384 | 1.28× |
| gpt-5-nano | 679 | 1.40× | 354 | 1.23× | 361 | 1.20× |
| qwen3-30b | 470 | 0.97× | 236 | 0.82× | 253 | 0.84× |
| gpt-4o-mini | 545 | 1.13× | 315 | 1.10× | 355 | 1.18× |
| gemini-flash | 543 | 1.12× | 322 | 1.12× | 332 | 1.11× |
| haiku | 638 | 1.32× | 464 | 1.62× | 467 | 1.56× |

†gpt-oss-20b metrics from 2 plans only (silo + gta). No model exceeds the 2× warning threshold.
The `consequences` and `review` fields are unchanged by the enrich step (passthrough from input),
confirming that only `description`, `synergy_text`, and `conflict_text` are generated.

---

## Comparison

### Per-Plan Lever Counts and Errors

**After PR (4/06–4/12):**

| Run | silo | gta | sovereign | hkg | parasomnia |
|-----|------|-----|-----------|-----|------------|
| 4/06 llama3.1 | 7(0err) | 7(2err) | 5(0err) | 7(0err) | 8(0err) |
| 4/07 gpt-oss-20b | 7(0err) | 8(0err) | 0(12err) | 0(17err) | 0(20err) |
| 4/08 gpt-5-nano | 7(0err) | 8(0err) | 5(0err) | 7(0err) | 8(0err) |
| 4/09 qwen3-30b | 7(0err) | 8(0err) | 5(0err) | 7(0err) | 8(0err) |
| 4/10 gpt-4o-mini | 7(0err) | 8(0err) | 5(0err) | 7(0err) | 8(0err) |
| 4/11 gemini-flash | 7(0err) | 8(0err) | 5(0err) | 7(0err) | 8(0err) |
| 4/12 haiku | 7(0err) | 8(0err) | 5(0err) | 7(0err) | 8(0err) |

**Before PR (3/85–3/91):**

| Run | silo | gta | sovereign | hkg | parasomnia |
|-----|------|-----|-----------|-----|------------|
| 3/85 llama3.1 | 15(0err) | 16(0err) | 14(0err) | 15(0err) | 18(0err) |
| 3/86 gpt-oss-20b | FAIL | FAIL | FAIL | FAIL | FAIL |
| 3/87 gpt-5-nano | 15(0err) | 16(0err) | 14(0err) | 15(0err) | 18(0err) |
| 3/88 qwen3-30b | 15(0err) | 16(0err) | 14(0err) | 15(0err) | 18(0err) |
| 3/89 gpt-4o-mini | 15(0err) | 16(0err) | 14(0err) | 15(0err) | 18(0err) |
| 3/90 gemini-flash | 15(0err) | 16(0err) | 13(0err) | 15(0err) | 18(0err) |
| 3/91 haiku | 15(0err) | 16(0err) | 14(0err) | 15(0err) | 18(0err) |

Note: The lever count change (14–18 → 5–8) is due to baseline regeneration between
runs 3/91 and 4/06, not to PR #454. Before-PR runs enriched all potential levers from
002-10; after-PR runs enrich only the deduplicated ("keep") set whose IDs match the
baseline 002-12. Whether this change was intentional or a side-effect of the baseline
regeneration requires investigation.

### Duration (seconds per plan, wallclock)

**gpt-oss-20b:**

| Run | silo | gta | sovereign | hkg | parasomnia |
|-----|------|-----|-----------|-----|------------|
| Before (3/86) | TIMEOUT 600s | TIMEOUT 600s | FAIL 600s | FAIL 27s | FAIL 31s |
| After (4/07) | 140s | 276s | **0.98s** | **1.09s** | **1.73s** |

The failing plans are now rejected in <2s vs 600s, a **300× improvement in fail-fast
behavior**.

---

## Quantitative Metrics

### Success Rate

| Metric | Before (3/85–3/91) | After (4/06–4/12) | Change |
|--------|-------------------|------------------|--------|
| Plans with status=ok | 30/35 (85.7%) | 35/35 (100%) | +14.3 pp |
| Plans with all levers enriched | 30/35 (85.7%) | 32/35 (91.4%) | +5.7 pp |
| gpt-oss-20b plans with levers | 0/5 (0%) | 2/5 (40%) | +40 pp |
| gpt-oss-20b plans fully enriched | 0/5 (0%) | 2/5 (40%) | +40 pp |
| gpt-oss-20b plans zero levers | 5/5 (100%) | 3/5 (60%) | −40 pp |
| All other models total | 30/30 (100%) | 30/30 (100%) | 0 |

### Fabricated Percentages and Template Leakage

Fabricated `%` claims (from the model-generated fields `description`, `synergy_text`,
`conflict_text`) across after-PR runs:

| Run | Plan | Desc % | Syn % | Conf % |
|-----|------|--------|-------|--------|
| 4/06 llama3.1 | silo | 3 | 0 | 0 |
| 4/06 llama3.1 | gta | 0 | 0 | 0 |
| 4/06 llama3.1 | hkg | 0 | 0 | 0 |
| 4/08 gpt-5-nano | silo–hkg | 2–4 | 0 | 0 |
| 4/09 qwen3-30b | hkg | 2 | 0 | 0 |
| 4/12 haiku | silo | 11 | 0 | 1 |

Note: Most `%` occurrences in `description` are echoed from the `consequences` input field
(which already contains fabricated percentages like "30% reduction in innovative output"
from the baseline). These are an upstream issue from the `identify_potential_levers` or
`enrich_potential_levers` prompt, not new fabrication by PR #454.

### UUID Leakage Count (synergy + conflict fields, llama3.1)

| Plan | Synergy UUIDs | Conflict UUIDs |
|------|--------------|----------------|
| silo | 9 | 9 |
| gta | 7 | 9 |
| hkg | 7 | 7 |
| parasomnia | 16 | 8 |

This is B2 (unchanged from analysis 54). Source line 198: `full_lever_context_str` still
emits `"- {lever.lever_id}: {lever.name}"`.

---

## Evidence Notes

- `history/4/07_enrich_potential_levers/outputs/20260308_sovereign_identity/002-12-enriched_levers_raw.json`:
  12 errors, 0 characterized_levers, all `BadRequestError` with "131909 tokens requested
  (3909 text input, 128000 output)"
- `history/4/07_enrich_potential_levers/outputs/20250321_silo/activity_overview.json`:
  calls to 3 providers (Chutes, DeepInfra, Parasail), 4 calls total, 18,906 tokens
- `history/4/07_enrich_potential_levers/outputs.jsonl`:
  `calls_succeeded: 4` for silo/gta, `calls_succeeded: 0` for sovereign/hkg/parasomnia
- `history/3/86_enrich_potential_levers/events.jsonl`:
  3× `"plan timeout after 600s"`, 2× `"LLM batch interaction failed"`
- `enrich_potential_levers.py` lines 95–107: `BATCH_SIZE=5`, `SMALL_CONTEXT_THRESHOLD=6000`,
  `SMALL_CONTEXT_BATCH_SIZE=2`
- `enrich_potential_levers.py` lines 186–193: adaptive batch size probes `context_window`
  from model metadata. For gpt-oss-20b, reported `context_window=3900 < 6000` → `batch_size=2`
- `enrich_potential_levers.py` line 198: UUID leakage B2 is still present
- `baseline/train/20250321_silo/002-12-enriched_levers_raw.json`: baseline was generated
  by `google/gemini-2.0-flash-001`, shows `context_window: 3900, num_output: 8192`

---

## PR Impact

### What the PR Was Supposed to Fix

1. **Adaptive batch size**: Use `batch_size=2` for gpt-oss-20b (context_window=3900 < 6000)
   to avoid overfilling small-context models.
2. **max_tokens bump**: 8192 → 128000 to avoid truncating structured JSON output.
3. **Guarded retry**: Split failing batches once (depth=1) within a 300s budget; skip on
   continued failure. Prevents 600s timeout cascades.
4. **Accurate batch counting**: Report real `batches_succeeded` instead of hardcoded 1.

### Before vs After Comparison

| Metric | Before (3/85–3/91) | After (4/06–4/12) | Change |
|--------|-------------------|------------------|--------|
| Overall success (status=ok) | 30/35 (85.7%) | 35/35 (100%) | **+14.3 pp** |
| Overall levers enriched (all plans) | 30/35 (85.7%) | 32/35 (91.4%) | **+5.7 pp** |
| gpt-oss-20b: plans with levers | 0/5 (0%) | 2/5 (40%) | **+40 pp** |
| gpt-oss-20b: new overflow failures | N/A | 3/5 (60%) | **New regression** |
| gpt-oss-20b: timeout per failing plan | 600s | <2s | **300× faster fail** |
| Accurate batch count | Hardcoded 1 | Actual count | **Fixed** |
| calls_succeeded=4 (gpt-oss, silo) | — | 4 batches × 2 levers | **Confirmed** |
| B2 UUID leakage (llama3.1) | Present | Present | **Unchanged** |
| N2 consequence echoing (llama3.1) | Present | Present (desc 0.74×) | **Unchanged** |
| N3 unknown_lever_id (llama3.1) | Not observed | 1 occurrence (gta) | **New** |
| Field lengths vs baseline | N/A (different input) | 0.74×–1.62× | **Acceptable** |
| LLMChatError count | 0 | 0 | **Unchanged** |

### Did the PR Fix the Targeted Issue?

**Partially.** The adaptive batch size, guarded retry, and accurate batch counting all
work correctly. gpt-oss-20b now produces valid output for 2/5 plans (vs 0/5 before) and
fails fast (<2s) on the other 3 plans (vs 600s before). This is a real operational improvement.

**However**, a new failure mode was introduced: setting max_tokens=128000 for a model
with context_window=131072 leaves only 3072 tokens for input text. For plans with
longer lever descriptions (sovereign_identity, hong_kong_game, parasomnia), even a
single-lever batch (batch_size=1, depth=1) exceeds this budget. All levers are silently
skipped and the plan-level status remains "ok" — the failure is invisible in
`outputs.jsonl`.

The fix: reduce max_tokens for gpt-oss-20b to ≤65536 (half the context window), giving
adequate headroom for the system prompt + context + batch content.

### Regressions

1. **C1 (max_tokens overflow)**: 3/5 gpt-oss-20b plans produce zero levers due to
   max_tokens=128000 consuming nearly all of the 131072-token context window. This
   affects plans with longer lever context (sovereign_identity: 5 levers, hkg: 7 levers,
   parasomnia: 8 levers).
2. **N3 (unknown_lever_id)**: llama3.1 gta_game produces one hallucinated lever_id;
   the lever is silently dropped. This may be exacerbated by B2 (UUIDs in context).

### Verdict: **CONDITIONAL**

The PR delivers three correctly implemented improvements (guarded retry, adaptive batch
size logic, accurate batch counting) and partially fixes gpt-oss-20b (2/5 plans now work
vs 0/5 before). The blocking issue is the max_tokens=128000 value for gpt-oss-20b, which
makes 3/5 plans fail silently. The fix is a targeted change: cap max_tokens at a
fraction of the model's actual context window (e.g., `context_window // 2`) in
`baseline.json` or in the adaptive sizing code. Until that fix lands, gpt-oss-20b remains
unreliable for longer plans.

---

## Questions For Later Synthesis

1. **Input confound**: Before-PR runs enriched 14–18 levers (from 002-10), after-PR runs
   enrich 5–8 levers (matching 002-12 baseline). Was the baseline intentionally regenerated
   between the two run batches? Which input set is correct for the enrich step?

2. **Max-tokens cap**: Should the adaptive batch size code also compute a safe
   `max_tokens = min(configured_max_tokens, context_window // 2)` for the LLM call, or
   should this be addressed only in `baseline.json` per-model configuration?

3. **Silent zero-lever failure**: Plans that skip all levers due to overflow still report
   `status: "ok"`. Should the runner report `status: "error"` when `characterized_levers`
   is empty? This could prevent downstream steps from silently receiving an empty lever set.

4. **N3 hallucination frequency**: Is llama3.1's `unknown_lever_id` error a one-off or
   systematic? If B2 (UUIDs in context) is fixed, does it disappear?

5. **Haiku syn/conf at 1.56–1.62×**: This is higher than before. Is haiku producing
   genuinely more informative synergy/conflict text, or is it padding? A qualitative
   review of 2–3 examples would clarify.

---

## Reflect

The PR correctly identified three real problems and implemented technically sound fixes
for all three. The max_tokens=128000 choice was motivated by the need to prevent JSON
truncation, but was applied without checking whether it left adequate input headroom for
gpt-oss-20b's 131072-token context window. The result is a new failure mode that is
worse in some ways than the original: instead of a timeout + clear error, the plan
silently produces zero levers with `status: "ok"`.

The fail-fast improvement (600s → <2s for failures) is genuinely valuable — it converts
silent resource waste into visible, quickly-detected failures. But the root problem
(gpt-oss-20b can't process most plans) persists.

The input-lever count discrepancy (14–18 before, 5–8 after) is a significant confound
that makes content quality comparison between before and after unreliable. This needs to
be resolved before drawing conclusions about whether the enrich step is improving lever
quality over time.

---

## Potential Code Changes

**C1 — Cap max_tokens relative to context_window in adaptive sizing code**

At `enrich_potential_levers.py:186–193`, after probing `context_window`, also compute
a safe max_tokens cap:

```python
# Pseudocode
if context_window < SOME_THRESHOLD:
    # leave at least half the context window for input
    effective_max_tokens = min(configured_max_tokens, context_window // 2)
    # pass effective_max_tokens to LLM creation
```

Or alternatively: update `baseline.json` to set gpt-oss-20b's `max_tokens` to 32000
or 65536 rather than 128000. Either approach prevents the overflow.

**C2 — Strip UUIDs from full_lever_context_str (B2 — unchanged from analysis 54)**

At `enrich_potential_levers.py:198`, change:
```python
full_lever_context_str = "\n".join([f"- {lever.lever_id}: {lever.name}" for lever in levers_to_characterize])
```
to:
```python
full_lever_context_str = "\n".join([f"- {lever.name}" for lever in levers_to_characterize])
```

This removes the UUID format signal that causes llama3.1 to inject full UUIDs into
synergy/conflict text (N2/B2). It may also reduce llama3.1's `unknown_lever_id`
hallucinations (N3).

**H1 — Add explicit output-size guard in system prompt for small-context models**

For models where context_window is close to max_tokens + system_overhead, add a note
to the system prompt instructing the model to produce concise responses. This is a
last-resort measure if the max_tokens cap (C1) is insufficient.

---

## OPTIMIZE_INSTRUCTIONS Alignment

The current `OPTIMIZE_INSTRUCTIONS` in `enrich_potential_levers.py` (lines 28–93)
already documents:
- "Consequence echoing without elaboration" (added after PR #451)
- "UUID cross-reference format inconsistency" (added after PR #451)

Both problems are still occurring (N2, B2). No new categories are introduced by PR #454.

**Proposed new entry** for `OPTIMIZE_INSTRUCTIONS`:

```
- max_tokens overflow for small-context models. If max_tokens is set close to the
  model's context_window, the available input token budget drops to near zero, causing
  all batches to fail with BadRequestError even at batch_size=1. The fix is to cap
  max_tokens at (context_window // 2) or set a model-specific max_tokens in
  baseline.json. Failure mode is silent: plan-level status remains "ok" but
  characterized_levers is empty.
```

---

## Summary

PR #454 makes three clean improvements: guarded retry (eliminates 600s timeouts),
adaptive batch size (correct logic), and accurate batch counting. gpt-oss-20b went from
0/5 to 2/5 plans fully enriched, with the 3 failures now detected in under 2 seconds
instead of 600 seconds.

The blocking issue is max_tokens=128000 for gpt-oss-20b: this leaves only 3072 input
tokens in the 131072-token context window. Plans with longer lever descriptions
(sovereign_identity, hong_kong_game, parasomnia) silently produce zero characterized
levers. The fix is a targeted reduction of max_tokens for gpt-oss-20b to ≤65536.

Content quality for the 6 other models is stable (0.74×–1.62× baseline on all fields).
Known issues B2 (UUID leakage) and N2 (consequence echoing in llama3.1) are unchanged
by this PR.

**Verdict: CONDITIONAL** — keep the guarded retry, adaptive batch size, and batch
counting improvements; fix the max_tokens=128000 value for gpt-oss-20b before
considering this model reliable.
