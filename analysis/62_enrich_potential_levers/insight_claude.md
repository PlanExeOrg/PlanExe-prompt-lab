# Insight Claude

Analysis of PR #460: "Use 6-char lever ID prefix, positive framing, and exact-count instruction"
Evaluated against baseline `analysis/60_enrich_potential_levers` (PR #457, registered best).

History runs examined: `4/41` through `4/47` (after PR #460) vs `4/27` through `4/33` (after PR #457).

---

## Rankings

Models by post-PR quality (best to worst):

1. **gpt-5-nano** (run 43) — 0 errors, 0 contamination, clean output
2. **gpt-oss-20b** (run 42) — 0 errors, 0 contamination, clean output
3. **qwen3-30b** (run 44) — 0 errors, 0 contamination, clean output
4. **gpt-4o-mini** (run 45) — 0 errors, 0 contamination, clean output
5. **gemini-2.0-flash** (run 46) — 0 errors, 0 contamination, clean output
6. **llama3.1** (run 41) — 2 errors (new minor regression), 0 contamination (fully fixed)
7. **haiku** (run 47) — 43 errors (major regression), 0 contamination

---

## Negative Things

### N1: Haiku unknown_lever_id errors increased 6x (from 7 → 43)

Before PR #460 (runs 27–33), claude-haiku-4-5-pinned produced **7** `unknown_lever_id` errors across all plans. After PR #460 (runs 41–47), haiku produces **43** errors — distributed across four plans:

| Plan | Haiku errors before (run 33) | Haiku errors after (run 47) |
|------|------------------------------|------------------------------|
| silo | 0 | 24 |
| gta_game | 5 | 10 |
| sovereign_identity | 0 | 0 |
| hong_kong_game | 1 | 1 |
| parasomnia | 1 | 8 |
| **Total** | **7** | **43** |

Evidence: `history/4/47_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json` — 24 `unknown_lever_id` errors with fabricated IDs: `d9e2f1`, `e8f4g2`, `f2h5i3`, … through `b3c6d4`.

**Root cause**: These IDs follow a sequential alphabetical pattern (d→e→f→g→h→j→k→l→m→n→o→p→q→r→s→t→u→v→w→x→y→z→a→b as the first character), not hexadecimal. They do not resemble any real lever UUID prefix (real prefixes: `278aac`, `3059cf`, `b35d92`, `ccd487`, `5ac097`, `364f20`, `5e26e4`). Haiku interprets the `lever_id` field description ("The 6-character identifier of the lever") as license to generate a sequential 6-char string rather than returning the actual prefix from the prompt.

Despite the fabricated IDs, all **7 real levers** in each plan ARE correctly matched and enriched — haiku produces correct characterizations alongside extra fabricated ones. The fabricated entries are silently discarded. This is a noise and reliability issue, not a correctness failure.

**Critical context**: In PR #458 (runs 34–40), the exact-count instruction was introduced and reduced haiku to **2 errors**. PR #460 re-introduces 43 errors, meaning the 6-char prefix is the direct cause of the regression.

### N2: llama3.1 introduced 2 new minor errors

Run 41 (llama3.1, hong_kong_game) now has 2 errors (`unknown_lever_id`: 1, `incomplete`: 1), where run 27 had 0.
Evidence: `history/4/41_enrich_potential_levers/outputs/20260310_hong_kong_game/002-12-enriched_levers_raw.json`.

This is minor — 34/35 levers still successfully enriched — but represents a small regression in llama3.1 that was previously clean.

### N3: Haiku descriptions inflating (1.39× baseline)

Haiku's average description length grew from 568 to 673 chars between PR #457 and PR #460 runs (a +18.5% increase). Against the baseline of 484 chars, haiku descriptions are now 1.39× baseline length. While still below the 2× warning threshold, the increase is model-specific and upward-trending.

Evidence: Run 47 silo / `Social Control Mechanism` description = 523 chars vs baseline = comparable lever descriptions at ~400–500 chars.

---

## Positive Things

### P1: UUID/placeholder contamination fully eliminated for llama3.1

PR #460 reduced UUID/placeholder contamination from **32 instances** (20 full UUIDs + 12 `(lever ID: XXXX)` placeholders) to **0** for llama3.1.

Before (run 27, llama3.1):
- `Technological Adaptation Strategy` synergy_text: `"...with the Resource Management Philosophy (lever ID: XXXX), as both prioritize efficient use..."` — from `history/4/27_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json`
- `External Relations Protocol` conflict_text: `"...with the Information Control Strategy (lever ID: WWW), as increased contact..."` — same file

After (run 41, llama3.1):
- `Technological Adaptation Strategy` synergy_text: `"The Technological Adaptation Strategy has strong synergy with the Resource Management Philosophy lever..."` — clean name references throughout

### P2: UUID contamination eliminated for all models

Running totals across all 7 models and all 5 plans:

| Metric | Before (runs 27–33) | After (runs 41–47) |
|--------|--------------------|--------------------|
| Full UUID refs in synergy/conflict | 20 | 0 |
| `(lever ID: XXXX)` placeholders | 12 | 0 |
| **Total contamination** | **32** | **0** |

### P3: All models complete all 5 plans (no timeouts/LLMChatErrors)

Events.jsonl for all 7 runs (41–47) show only `run_single_plan_start` / `run_single_plan_complete` events — no `LLMChatError`, no `PipelineStopRequested`, no timeouts. All 5 plans complete per model per run.

### P4: OPTIMIZE_INSTRUCTIONS updated with correct lessons

The source file `enrich_potential_levers.py:88–94` documents:
- The prohibition approach backfired on small models (PR #458 lesson)
- Positive framing is correct approach
- 6-char prefix as the current fix

This documentation is accurate and current.

---

## Comparison

Comparing analysis 62 (PR #460, runs 41–47) against analysis 60 (PR #457, runs 27–33, registered best):

| Metric | Before PR #460 | After PR #460 | Change |
|--------|---------------|---------------|--------|
| UUID contamination (synergy/conflict) | 32 | 0 | ✅ -100% |
| Total `errors` entries | 7 | 45 | ❌ +543% |
| haiku `unknown_lever_id` errors | 7 | 43 | ❌ +514% |
| llama3.1 errors | 0 | 2 | ❌ new |
| LLMChatError (events.jsonl) | 0 | 0 | ✅ unchanged |
| Characterized levers total | 245 | 244 | ≈ unchanged |
| Avg description length | 518 chars | 523 chars | ≈ +1% |
| Avg synergy_text length | 325 chars | 325 chars | unchanged |
| Avg conflict_text length | 327 chars | 340 chars | ≈ +4% |
| Plans completed | 5×7=35 | 5×7=35 | ✅ unchanged |

---

## Quantitative Metrics

### 1. UUID Contamination by Model

| Model | Run | UUIDs in text | Placeholders | Total |
|-------|-----|---------------|-------------|-------|
| llama3.1 | 27 (before) | 20 | 12 | **32** |
| gpt-oss-20b | 28 (before) | 0 | 0 | 0 |
| gpt-5-nano | 29 (before) | 0 | 0 | 0 |
| qwen3-30b | 30 (before) | 0 | 0 | 0 |
| gpt-4o-mini | 31 (before) | 0 | 0 | 0 |
| gemini-2.0-flash | 32 (before) | 0 | 0 | 0 |
| haiku | 33 (before) | 0 | 0 | 0 |
| **llama3.1** | **41 (after)** | **0** | **0** | **0** ✅ |
| gpt-oss-20b | 42 (after) | 0 | 0 | 0 |
| gpt-5-nano | 43 (after) | 0 | 0 | 0 |
| qwen3-30b | 44 (after) | 0 | 0 | 0 |
| gpt-4o-mini | 45 (after) | 0 | 0 | 0 |
| gemini-2.0-flash | 46 (after) | 0 | 0 | 0 |
| haiku | 47 (after) | 0 | 0 | 0 |

### 2. Error Count by Model

| Model | Before errors | After errors | Change |
|-------|-------------|-------------|--------|
| llama3.1 | 0 | 2 | ❌ new |
| gpt-oss-20b | 0 | 0 | — |
| gpt-5-nano | 0 | 0 | — |
| qwen3-30b | 0 | 0 | — |
| gpt-4o-mini | 0 | 0 | — |
| gemini-2.0-flash | 0 | 0 | — |
| haiku | 7 | 43 | ❌ +514% |
| **Total** | **7** | **45** | **❌ +543%** |

### 3. Field Length vs. Baseline (After PR #460)

| Field | Baseline avg | After PR avg | Ratio | Warning? |
|-------|-------------|-------------|-------|---------|
| description | 484 chars | 523 chars | 1.08× | No |
| synergy_text | 286 chars | 325 chars | 1.14× | No |
| conflict_text | 298 chars | 340 chars | 1.14× | No |
| consequences (pass-through) | 279 chars | 279 chars | 1.00× | No |
| review (pass-through) | 155 chars | 155 chars | 1.00× | No |

All ratios are at or below 1.14× — no verbosity regression. Baseline: 35 levers across 5 plans.

### 4. Per-model Field Lengths (After PR #460)

| Model | Run | Avg description | Avg synergy | Avg conflict |
|-------|-----|----------------|------------|-------------|
| llama3.1 | 41 | 377 | 323 | 331 |
| gpt-oss-20b | 42 | 566 | 353 | 343 |
| gpt-5-nano | 43 | 444 | 288 | 308 |
| qwen3-30b | 44 | 514 | 340 | 371 |
| gpt-4o-mini | 45 | 473 | 294 | 333 |
| gemini | 46 | 468 | 273 | 298 |
| haiku | 47 | 673 | 494 | 520 |

Haiku produces descriptions 1.39× baseline (673/484). Other models fall between 0.78× and 1.17×.

### 5. Haiku Fabricated ID Pattern (silo plan)

From `history/4/47_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json`:

| Fabricated ID | Real prefix pattern | Match? |
|--------------|---------------------|--------|
| d9e2f1 | 278aac | ❌ |
| e8f4g2 | 3059cf | ❌ |
| f2h5i3 | b35d92 | ❌ |
| … (24 total) | … | ❌ all |

The 24 fabricated IDs follow an alphabetical increment (d→e→f→g→h→j→k…) and contain non-hex characters (g, h, j, k, l, m, n, o, p, q, r, s, t, u, v, w, x, y, z), while real UUID prefixes are pure hex.

---

## Evidence Notes

- `history/4/27_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json`: 5 levers with full UUIDs in synergy/conflict (Technological Integration Strategy, Narrative Complexity Strategy, World Design Strategy, Monetization Strategy, Risk Mitigation Strategy each contain 3 UUID references in their text).

- `history/4/41_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json`: Same plan, 0 UUID references. Cross-references now use lever names only.

- `history/4/33_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json`: haiku before PR — 5 `unknown_lever_id` errors (full UUIDs that didn't match).

- `history/4/47_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json`: haiku after PR — 24 `unknown_lever_id` errors with sequential alphanumeric IDs.

- `enrich_potential_levers.py:239–247` (PR #460 change): `prefix_to_full = {lever.lever_id[:6]: lever.lever_id for lever in batch}` and `lever_details_for_prompt` uses `Lever {lever.lever_id[:6]}` instead of `Lever {lever.lever_id}`.

- `enrich_potential_levers.py:254–256`: "Return exactly {len(batch)} characterizations — one per lever, no more, no fewer."

- `enrich_potential_levers.py:134–136`: `LeverCharacterization.lever_id` field description = "The 6-character identifier of the lever" — this open-ended description allows haiku to generate any 6-char string.

---

## PR Impact

### What PR #460 was supposed to fix

1. **6-char prefix**: Eliminate full-UUID contamination in synergy/conflict text from `lever_details_for_prompt`. PR #457 stripped UUIDs from the full-list context; PR #460 now also strips them from the per-batch details.
2. **Positive framing**: Replace the negative UUID prohibition from PR #458 (which backfired on llama3.1) with a positive "refer to levers by name" instruction.
3. **Exact-count instruction**: "Return exactly N characterizations" — targeted at haiku's fabricated extra entries, which had been reduced to 2 by PR #458.

### Before vs. After comparison

| Metric | Before (runs 27–33, PR #457) | After (runs 41–47, PR #460) | Change |
|--------|-----------------------------|-----------------------------|--------|
| UUID refs in synergy/conflict | 20 | 0 | ✅ Eliminated |
| Placeholder `(lever ID: XXXX)` refs | 12 | 0 | ✅ Eliminated |
| Total contamination | 32 | 0 | ✅ **-100%** |
| haiku unknown_lever_id errors | 7 | 43 | ❌ **+514%** |
| llama3.1 errors | 0 | 2 | ❌ new |
| LLMChatError entries (all runs) | 0 | 0 | ✅ none |
| Total characterized levers | 245 | 244 | ≈ unchanged |
| Avg description length | 518 | 523 | ≈ +1% |
| Plans fully completed per model | 5/5 | 5/5 | ✅ unchanged |

**Note on context**: PR #458 (runs 34–40) had already added the exact-count instruction. At that point haiku had 2 errors. PR #460 re-ran haiku with the same exact-count instruction PLUS the 6-char prefix change. Haiku errors went from 2 (PR #458) to 43 (PR #460), confirming the 6-char prefix — not the exact-count instruction — is causing the regression.

### Did the PR fix the targeted issue?

**Yes, for UUID contamination**: The 6-char prefix + positive framing fully eliminated llama3.1's 32 UUID/placeholder contamination instances. This is a clean, verified fix with zero false positives. The fix also works correctly for all other models (gpt-oss-20b, gpt-5-nano, qwen3-30b, gpt-4o-mini, gemini).

**No, for haiku's fabricated entries**: The PR description claims the exact-count instruction "Reduced haiku's fabricated entries 71% in #458." This was true for PR #458 in isolation (7→2). But PR #460's 6-char prefix change caused a new, larger fabrication pattern: 43 errors vs 7 before. The net effect is a 514% increase in haiku errors compared to the PR #457 baseline.

### Did the PR introduce regressions?

Yes:
1. **Haiku**: 6-char prefix causes haiku to fabricate sequential non-hex identifiers instead of using real lever prefixes. The fabricated entries don't corrupt the actual enriched levers (all real levers are correctly matched), but they generate 43 logged errors per run and add noise.
2. **llama3.1**: 2 new minor errors in hong_kong_game. Low severity.

### Root cause of haiku regression

Haiku is a function-calling model (`is_function_calling_model=True`). It generates structured JSON output via tool use. The `LeverCharacterization.lever_id` field is described as "The 6-character identifier of the lever." When haiku receives a prompt showing `Lever 278aac`, it should return `lever_id: "278aac"`. Instead, it generates sequential examples like `d9e2f1`, `e8f4g2`, etc.

Likely cause: Haiku's tool-use JSON generation is pattern-completing the `lever_id` field based on the "6-character identifier" description rather than looking up the actual value from the prompt. The 6-char hex prefix does not provide a clear enough anchor for haiku's structured output generation, whereas the full UUID (36 chars, globally unique) was memorable enough to match correctly.

### Verdict

**CONDITIONAL** — the PR succeeds in eliminating UUID contamination (a genuine content quality improvement for the 6/7 non-haiku models) but introduces a major regression for haiku that needs follow-up work. The fix should be kept for llama3.1/non-function-calling models; a different identifier strategy is needed for haiku and other function-calling models.

---

## Questions For Later Synthesis

1. Should function-calling models (haiku, gpt-4o-mini) use a different lever identification scheme — either full UUIDs or lever names as the structured output key? Full UUIDs were correctly returned by haiku in PR #457 with only 7 errors (vs 43 now).

2. Could the `prefix_to_full` mapping be extended with a fallback to match by lever name when the prefix doesn't match? The enriched content is usually correct — only the `lever_id` field is fabricated.

3. Is 43 errors per haiku run an acceptable cost for eliminating llama3.1 contamination (32 instances)? The fabricated entries are silently discarded and don't affect downstream steps (the real levers are all correctly enriched). Is this a cosmetic issue or a functional one?

4. Should the exact-count instruction be removed if it doesn't stop haiku from generating extras? Or should the instruction be strengthened?

5. The `LeverCharacterization.lever_id` field description says "The 6-character identifier." Could changing this description to "The exact 6-character prefix shown in 'Lever XXXXXX' above" help haiku ground the value?

---

## Reflect

The PR correctly diagnosed that llama3.1's UUID contamination stemmed from full UUIDs in `lever_details_for_prompt` and applied an appropriate fix. The positive-framing instruction also aligns with the lesson from PR #458.

However, haiku's function-calling behavior differs from text-completion models. Haiku generates structured JSON through a separate tool-call pathway, and 6-char hex prefixes are not sufficiently distinctive anchors for that pathway. The regression went from 2 errors (PR #458) to 43 — entirely attributable to the 6-char prefix change.

OPTIMIZE_INSTRUCTIONS now accurately documents the UUID leakage fix but does not yet mention the haiku-specific degradation under 6-char prefixes. This should be added.

The content quality metrics (field lengths, ratio to baseline) remain healthy across all models. No verbosity regression was introduced.

---

## Potential Code Changes

**C1 (High priority)**: For function-calling models (`is_function_calling_model=True`), use full UUIDs in `lever_details_for_prompt` and `prefix_to_full`. The UUID contamination problem was specific to text-completion models copying IDs into free-text fields; function-calling models use UUIDs only in structured output and do not contaminate free text.

```python
# Proposed change in enrich_potential_levers.py (~line 238):
use_short_id = not (hasattr(probe_llm.metadata, 'is_function_calling_model') and probe_llm.metadata.is_function_calling_model)
if use_short_id:
    prefix_to_full = {lever.lever_id[:6]: lever.lever_id for lever in batch}
    id_in_prompt = lambda l: l.lever_id[:6]
else:
    prefix_to_full = {lever.lever_id: lever.lever_id for lever in batch}
    id_in_prompt = lambda l: l.lever_id
```

**C2 (Medium priority)**: Add a name-based fallback to the `prefix_to_full` lookup when the returned `lever_id` doesn't match any prefix. The fabricated IDs all come with correct lever names. A fallback that matches by name would allow correct lever routing even when the ID is wrong.

**C3 (Low priority)**: Add `pattern="^[0-9a-f]{6}$"` constraint to `LeverCharacterization.lever_id` in the Pydantic schema. This would cause haiku's fabricated non-hex IDs (`d9e2f1` contains only hex chars, but `g3i6j4` does not) to fail schema validation, triggering a retry. This forces haiku to self-correct.

**C4 (Documentation)**: Update `OPTIMIZE_INSTRUCTIONS` to document the haiku degradation pattern:

> "6-char prefix causes function-calling models (haiku) to generate sequential fabricated IDs (d9e2f1, e8f4g2, …) instead of using the actual lever prefixes. The actual lever content is correct, but unknown_lever_id errors multiply with plan complexity. Use full UUIDs for function-calling models."

---

## Hypotheses

**H1**: Using full UUIDs for function-calling models (haiku, gpt-4o-mini) will reduce haiku's unknown_lever_id errors back to ≤2 while preserving the llama3.1 contamination fix.
- Evidence: Run 33 (haiku with full UUIDs, PR #457) had only 7 errors vs 43 in run 47. PR #458 (exact-count + full UUIDs) reduced haiku to 2 errors.
- Expected effect: Restore haiku error count to ~2, no change for other models.

**H2**: A name-based fallback in `prefix_to_full` lookup would silently resolve haiku's fabricated IDs without any prompt change.
- Evidence: Haiku's fabricated entries have correct `description`, `synergy_text`, `conflict_text` content — only `lever_id` is wrong.
- Expected effect: 0 unknown_lever_id errors for haiku, correct enrichment for all levers.

**H3**: The `LeverCharacterization.lever_id` field description change from "The 6-character identifier of the lever" to "The exact 6-character prefix shown before the lever name above (e.g., '278aac')" would ground haiku's generation.
- Evidence: The field description is vague enough to allow any 6-char string; a concrete example anchors the expected format.
- Expected effect: Partial reduction in fabricated IDs (may not fully fix; C2 is more robust).

**C1**: Model-type-aware `lever_details_for_prompt` — use full UUID for function-calling models, 6-char prefix for text-completion models.
- Evidence: The UUID contamination problem is text-completion-specific (llama3.1 copies text; haiku uses structured output).
- Expected effect: Eliminate haiku regression while preserving llama3.1 fix.

**C2**: Name-based fallback in lever matching (when prefix doesn't match, try lever name).
- Evidence: Haiku fabricated entries have correct content, only wrong IDs.
- Expected effect: Silent resolution of unknown_lever_id errors with zero prompt change.

---

## Summary

PR #460 applied three changes: 6-char prefix in `lever_details_for_prompt`, positive framing, and exact-count instruction. The effect was:

**Win**: UUID/placeholder contamination in synergy/conflict text fully eliminated (32 → 0 instances). The 6/7 non-haiku models now produce clean cross-references using lever names throughout. This is a genuine content quality improvement.

**Loss**: Haiku's `unknown_lever_id` errors increased from 7 (PR #457 baseline) to 43 — a 514% increase caused by the 6-char prefix confusing haiku's function-calling JSON generation. The error entries are fabricated sequential IDs (`d9e2f1`, `e8f4g2`, …) that bear no relationship to the real lever prefixes. The actual enriched lever content for all real levers is correct.

**Verdict: CONDITIONAL** — Keep the 6-char prefix for text-completion models (llama3.1 fix is real and clean). Address haiku by either reverting to full UUIDs for function-calling models (C1) or implementing a name-based fallback in the `prefix_to_full` lookup (C2). Both approaches are low-risk. C2 is purely a code change and does not require a new experiment run to validate.
