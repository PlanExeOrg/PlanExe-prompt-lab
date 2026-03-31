# Insight Claude

## Overview

This analysis evaluates **PR #464** ("Move UUID to end of lever details, add positive
framing and exact-count") against the runs in analysis 60 (PR #457, the registered best
for `enrich_potential_levers`).

Both analyses use `baseline/train` as input (5–8 deduplicated levers per plan), making
direct before/after comparison valid. Both are `enrich_potential_levers` step runs.

**Runs compared**:

| Model | Before (analysis 60) | After (this analysis) |
|-------|----------------------|-----------------------|
| ollama-llama3.1 | `4/27_enrich_potential_levers` | `4/55_enrich_potential_levers` |
| openrouter-gpt-oss-20b | `4/28_enrich_potential_levers` | `4/56_enrich_potential_levers` |
| openai-gpt-5-nano | `4/29_enrich_potential_levers` | `4/57_enrich_potential_levers` |
| openrouter-qwen3-30b-a3b | `4/30_enrich_potential_levers` | `4/58_enrich_potential_levers` |
| openrouter-gpt-4o-mini | `4/31_enrich_potential_levers` | `4/59_enrich_potential_levers` |
| openrouter-gemini-2.0-flash-001 | `4/32_enrich_potential_levers` | `4/60_enrich_potential_levers` |
| anthropic-claude-haiku-4-5 | `4/33_enrich_potential_levers` | `4/61_enrich_potential_levers` |

**PR change summary** (from `enrich_potential_levers.py` lines 240–247):

```python
# Before PR #464 (lever_details_for_prompt format)
f"Lever ID: {lever.lever_id}\n"
f"Name: {lever.name}\n"
f"Consequences: {lever.consequences}\n"
f"Options: {json.dumps(lever.options)}\n"
f"Review: {lever.review}\n"

# After PR #464
f"Name: {lever.name}\n"
f"Consequences: {lever.consequences}\n"
f"Options: {json.dumps(lever.options)}\n"
f"Review: {lever.review}\n"
f"(internal reference: {lever.lever_id})"
```

Additionally:
- System prompt added: "In `synergy_text` and `conflict_text`, always refer to other levers by their name — for example, write 'Policy Advocacy Strategy', not an identifier."
- User prompt added: "Return exactly N characterizations — one per lever, no more, no fewer."

---

## Negative Things

### N1 — llama3.1: 100% success → 0% success (total regression)

After PR #464, llama3.1 failed to characterize a single lever across all 5 plans. Every
plan shows `characterized_levers: []` and only error entries.

The model returns lever **names** instead of UUIDs in the `lever_id` structured-output
field. With the UUID demoted to `(internal reference: {uuid})` at the END of each block,
llama3.1 no longer recognizes it as the identifier to echo back.

Evidence:
- `history/4/55_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json`:
  errors include `{"type": "unknown_lever_id", "lever_id": "Social Control Mechanism"}` — the
  model returned the lever name, not the UUID.
- `history/4/55_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json`:
  errors include lever names like "Technological Integration Strategy", "Narrative Complexity
  Strategy", etc.
- All 5 plans show `char=0, unknown_id=N` where N equals the lever count for that plan.

This is a 100% → 0% regression for llama3.1 across all plans.

### N2 — gpt-5-nano: 100% success → 29% success (severe regression)

gpt-5-nano went from 35/35 levers characterized with 0 errors, to 10/35 levers
characterized with 50 errors (25 unknown_id + 25 incomplete).

Per-plan breakdown:
- `20250321_silo`: 5/7 (was 7/7) — 2 lost
- `20250329_gta_game`: 5/8 (was 8/8) — 3 lost
- `20260308_sovereign_identity`: 0/5 (was 5/5) — total failure
- `20260310_hong_kong_game`: 0/7 (was 7/7) — total failure
- `20260311_parasomnia_research_unit`: 0/8 (was 8/8) — total failure

Evidence:
- `history/4/57_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json`:
  errors for "Technological Adaptation Strategy" and "External Relations Protocol" — names
  returned instead of UUIDs.
- `history/4/57_enrich_potential_levers/outputs/20260308_sovereign_identity/002-12-enriched_levers_raw.json`:
  all 5 levers returned as names, none as UUIDs — 0 characterized.

The failure pattern is the same as llama3.1: the model uses the lever name as the
`lever_id` value, which the matching code does not recognize.

### N3 — gpt-oss-20b: minor regression on 1 plan

Run 56 (gpt-oss-20b after PR) shows parasomnia_research_unit with 5/8 levers
characterized and 3 lost (unknown_id=3, incomplete=3). All other plans remain 100%.

Evidence:
- `history/4/56_enrich_potential_levers/outputs/20260311_parasomnia_research_unit/002-12-enriched_levers_raw.json`

### N4 — haiku: fabricated-UUID errors persist and shift plans

Before PR #464 (run 33): haiku generated 7 hallucinated UUIDs across gta_game (5),
hong_kong (1), parasomnia (1). No `incomplete` errors.

After PR #464 (run 61): haiku generated 10 hallucinated UUIDs across silo (5), gta_game
(1), hong_kong (2), parasomnia (2). Plus 1 `incomplete` error (hong_kong: 6/7 levers).

The net effect: haiku's total error count increased (7 → 11). The errors shifted from
gta_game-heavy to silo-heavy but remained similar in scale. The positive-framing
instruction did not reduce haiku's UUID hallucination behavior.

Evidence:
- `history/4/61_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json`:
  5 errors with hallucinated UUIDs like `"72f9e8a1-7c3f-4a9b-b2d4-e6f5a8c9d2e1"`.
- `history/4/61_enrich_potential_levers/outputs/20260310_hong_kong_game/002-12-enriched_levers_raw.json`:
  1 `incomplete` entry (lever 5e26e456) in addition to unknown_id errors.

---

## Positive Things

### P1 — qwen3, gpt-4o-mini, gemini-flash: unaffected, remain at 100%

The three models that were at 100% before remain at 100% after:
- qwen3-30b (run 58): 35/35, 0 errors
- gpt-4o-mini (run 59): 35/35, 0 errors
- gemini-2.0-flash (run 60): 35/35, 0 errors

These models appear to correctly extract the UUID from `(internal reference: {uuid})` at
the end of each block, regardless of its position.

### P2 — No LLMChatError / Pydantic failures

Events.jsonl for all runs shows `"status": "ok"` with `"calls_succeeded": 2` for all
plans. No Pydantic schema validation failures were observed. The regression is a semantic
failure (wrong field value) not a structural failure (schema rejection).

Evidence:
- `history/4/55_enrich_potential_levers/outputs.jsonl`: all 5 plans `"status": "ok"`.
- `history/4/57_enrich_potential_levers/outputs.jsonl`: all 5 plans `"status": "ok"`.

### P3 — Content quality (field lengths) unchanged for successful levers

For models that still produce characterizations, field lengths are similar before and
after the PR. The content quality change is neutral.

---

## Comparison

### Per-model success rate: before vs after

| Model | Before characterized | After characterized | Before errors | After errors | Change |
|-------|---------------------|--------------------|---------|---------|----|
| llama3.1 | 35/35 | **0/35** | 0 | 71 | **CRITICAL** |
| gpt-5-nano | 35/35 | **10/35** | 0 | 50 | **SEVERE** |
| gpt-oss-20b | 35/35 | 32/35 | 0 | 6 | Minor |
| qwen3-30b | 35/35 | 35/35 | 0 | 0 | None |
| gpt-4o-mini | 35/35 | 35/35 | 0 | 0 | None |
| gemini-2.0-flash | 35/35 | 35/35 | 0 | 0 | None |
| haiku | 35/35 (+7 extra) | 34/35 (+10 extra) | 7 | 11 | Slight regression |

"Before" = runs 27–33 (analysis 60 / PR #457). "After" = runs 55–61 (this analysis / PR #464).
Totals are across all 5 plans (5–8 levers each, 35 levers total expected).

### Per-plan breakdown for regressed models

| Model/Plan | Silo | GTA | SovId | HKGame | Parasomnia |
|-----------|------|-----|-------|--------|-----------|
| llama3.1 BEFORE | 7/7 ✓ | 8/8 ✓ | 5/5 ✓ | 7/7 ✓ | 8/8 ✓ |
| llama3.1 AFTER | **0/7** | **0/8** | **0/5** | **0/7** | **0/8** |
| gpt-5-nano BEFORE | 7/7 ✓ | 8/8 ✓ | 5/5 ✓ | 7/7 ✓ | 8/8 ✓ |
| gpt-5-nano AFTER | 5/7 | 5/8 | **0/5** | **0/7** | **0/8** |

---

## Quantitative Metrics

### Characterization success rate

| Run | Model | Plans OK | Total characterized | Total levers | Success % |
|-----|-------|----------|---------------------|--------------|-----------|
| 27 (BEFORE) | llama3.1 | 5/5 | 35 | 35 | 100% |
| 55 (AFTER) | llama3.1 | 0/5 | 0 | 35 | **0%** |
| 29 (BEFORE) | gpt-5-nano | 5/5 | 35 | 35 | 100% |
| 57 (AFTER) | gpt-5-nano | 2/5 | 10 | 35 | **29%** |
| 28 (BEFORE) | gpt-oss-20b | 5/5 | 35 | 35 | 100% |
| 56 (AFTER) | gpt-oss-20b | 4/5 | 32 | 35 | 91% |
| 30 (BEFORE) | qwen3-30b | 5/5 | 35 | 35 | 100% |
| 58 (AFTER) | qwen3-30b | 5/5 | 35 | 35 | 100% |
| 31 (BEFORE) | gpt-4o-mini | 5/5 | 35 | 35 | 100% |
| 59 (AFTER) | gpt-4o-mini | 5/5 | 35 | 35 | 100% |
| 32 (BEFORE) | gemini-flash | 5/5 | 35 | 35 | 100% |
| 60 (AFTER) | gemini-flash | 5/5 | 35 | 35 | 100% |
| 33 (BEFORE) | haiku | 5/5 | 35 | 35 | 100% |
| 61 (AFTER) | haiku | 4/5 | 34 | 35 | 97% |

### Average field lengths (characterized levers only)

| Run | Model | N | Avg description | Avg synergy | Avg conflict |
|-----|-------|---|-----------------|-------------|--------------|
| 27 (BEFORE) | llama3.1 | 35 | 369 | 348 | 310 |
| 55 (AFTER) | llama3.1 | 0 | — | — | — |
| 29 (BEFORE) | gpt-5-nano | 35 | 677 | 361 | 350 |
| 57 (AFTER) | gpt-5-nano | 10 | 690 | 341 | 345 |
| 28 (BEFORE) | gpt-oss-20b | 35 | 656 | 361 | 347 |
| 56 (AFTER) | gpt-oss-20b | 32 | 642 | 345 | 347 |
| 30 (BEFORE) | qwen3-30b | 35 | 367 | 177 | 188 |
| 58 (AFTER) | qwen3-30b | 35 | 403 | 181 | 193 |
| 31 (BEFORE) | gpt-4o-mini | 35 | 500 | 301 | 338 |
| 59 (AFTER) | gpt-4o-mini | 35 | 463 | 298 | 328 |
| 32 (BEFORE) | gemini-flash | 35 | 489 | 280 | 295 |
| 60 (AFTER) | gemini-flash | 35 | 460 | 285 | 303 |
| 33 (BEFORE) | haiku | 35 | 568 | 444 | 456 |
| 61 (AFTER) | haiku | 34 | 565 | 446 | 475 |
| **Baseline** | (train data) | **35** | **483** | **285** | **298** |

Ratios vs baseline (after PR, unaffected models only):
- qwen3: 0.83×, 0.64×, 0.65× — below baseline (concise)
- gpt-4o-mini: 0.96×, 1.05×, 1.10× — near baseline
- gemini-flash: 0.95×, 1.00×, 1.02× — near baseline
- haiku: 1.17×, 1.57×, 1.59× — synergy/conflict above 1.5× (verbose but within acceptable range)

None of the working models exceed 2× baseline length. No fabricated percentage claims observed
in the content quality spot-check.

### Error breakdown

| Run | Model | unknown_lever_id | incomplete | total_errors |
|-----|-------|-----------------|------------|--------------|
| 27 (BEFORE) | llama3.1 | 0 | 0 | 0 |
| 55 (AFTER) | llama3.1 | **36** | **35** | **71** |
| 29 (BEFORE) | gpt-5-nano | 0 | 0 | 0 |
| 57 (AFTER) | gpt-5-nano | **25** | **25** | **50** |
| 28 (BEFORE) | gpt-oss-20b | 0 | 0 | 0 |
| 56 (AFTER) | gpt-oss-20b | 3 | 3 | 6 |
| 33 (BEFORE) | haiku | 7 | 0 | 7 |
| 61 (AFTER) | haiku | 10 | 1 | 11 |

---

## Evidence Notes

### Why llama3.1 fails after PR #464

The `lever_details_for_prompt` now formats each lever as:
```
Name: {lever.name}
Consequences: ...
Options: [...]
Review: ...
(internal reference: {lever.lever_id})
```

The `LeverCharacterization` Pydantic model has `lever_id: str = Field(description="The uuid of the lever")`. With the UUID as `(internal reference: ...)` at the END of the block, llama3.1 uses the lever **name** as the `lever_id` value. The matching code at line 276 of `enrich_potential_levers.py` checks `if char.lever_id in enriched_levers_map`, which uses UUID keys. Names don't match → `unknown_lever_id` error → lever is never enriched → `incomplete` error.

Evidence:
- `history/4/55_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json`:
  all 7 `unknown_lever_id` errors have lever names as values ("Social Control Mechanism", etc.)

### Why haiku still fabricates UUIDs (before and after PR)

Haiku is a function-calling model that over-generates `LeverCharacterization` objects.
In the before state (run 33), it generated correct characterizations for all real levers
PLUS some phantom entries with fabricated UUIDs. The same behavior occurs after (run 61).
The exact-count instruction "Return exactly N characterizations" did not eliminate this.

The fabricated UUIDs look plausible (e.g., "72f9e8a1-7c3f-4a9b-b2d4-e6f5a8c9d2e1") but
don't match any real lever. They are discarded by the matching code but create noise in
the error log.

### Why qwen3/gpt-4o-mini/gemini correctly return UUIDs despite the change

These models likely extract the `(internal reference: {uuid})` pattern correctly because:
- They are instruction-tuned to follow structured output schemas carefully
- They may process the entire block before populating the output field
- They respect the `lever_id` field description ("The uuid of the lever") and search
  for a UUID in the input

Small models (llama3.1) appear to use positional heuristics: the identifier to echo
is "the first thing in the block." When it's moved to last, they default to using
the `Name:` field instead.

---

## OPTIMIZE_INSTRUCTIONS Alignment

The `OPTIMIZE_INSTRUCTIONS` in `enrich_potential_levers.py` (lines 28–108) documents:

> "UUID leakage into free-text fields. Models copy UUIDs from the prompt into
> synergy_text and conflict_text. Mitigated by: (1) removing UUIDs from
> full_lever_context_str (PR #457), (2) moving the UUID to the end of each lever's
> details as "(internal reference: {uuid})" so models are less likely to copy it."

The constant is up-to-date — it already describes exactly what PR #464 was supposed
to do. However, the known-problems list needs an additional entry:

**Missing from known-problems**: Moving the UUID to the end breaks small models' ability
to echo it back in structured output. llama3.1 and gpt-5-nano use positional heuristics —
the first line of a block is treated as the identifier. When UUID moves to last,
they return the lever name instead, causing 100% failure for llama3.1 and 71% for gpt-5-nano.

**Proposed OPTIMIZE_INSTRUCTIONS addition**:
```
- UUID position vs structured-output matching. Small models (e.g., llama3.1, gpt-5-nano)
  use positional heuristics to echo the `lever_id` field: they treat the first item in
  each block as the identifier. Moving the UUID to the end (even with a clear label like
  "(internal reference:)") causes these models to return the lever name as lever_id,
  which breaks all downstream matching. Keep the UUID prominent (first or labeled early)
  in per-batch lever details, while using separate techniques (PR #457's full-context
  UUID removal) to prevent UUID leakage into free-text fields.
```

---

## Hypotheses

**H1** — Restore UUID to first line of `lever_details_for_prompt` as `Lever ID: {uuid}`.
This was the pre-PR #464 state. It gave 100% matching for llama3.1 and gpt-5-nano. The
UUID leakage problem (which PR #464 was trying to fix) is already partially addressed by
PR #457's removal of UUIDs from `full_lever_context_str`. The per-batch details can still
expose UUIDs without causing cross-batch contamination.
Expected effect: Restore llama3.1 and gpt-5-nano to 100% success rate.

**H2** — Hybrid approach: keep UUID at the end but label it more explicitly for structured
output. For example, change the label from `(internal reference: {uuid})` to
`[RETURN THIS AS lever_id: {uuid}]`. This makes the UUID's role unambiguous even when
it's at the end. Risk: negative instruction framing (the OPTIMIZE_INSTRUCTIONS notes that
negative prohibitions backfire for small models).
Expected effect: May restore gpt-5-nano; unlikely to fully restore llama3.1.

**H3** — Use a two-field approach: provide `lever_id` separately as the first field with a
clear label, then provide the rest of the details. For example:
```
lever_id: {uuid}
Name: {lever.name}
...
```
This is essentially reverting to the pre-PR #464 format, but using a lowercase label to
reduce the visual salience of the UUID and reduce copy-leakage.
Expected effect: Same as H1 with potentially less UUID leakage.

**C1** — Add a post-processing step to resolve lever names to UUIDs. The matching code
at line 276 of `enrich_potential_levers.py` does a strict UUID-key lookup. Adding a
name-to-UUID fallback would recover llama3.1 outputs where the model returns the correct
lever name but not the UUID. This is a pure code fix and doesn't require prompt changes.
Risk: introduces name-matching ambiguity if lever names are similar.
Expected effect: Full recovery for llama3.1 since its names are correct.

**C2** — Add the name-based fallback (C1) AND keep PR #464's UUID-at-end format. This
allows models that return names to succeed, while models that return UUIDs also succeed.
Expected effect: Recover llama3.1 and gpt-5-nano without reverting the UUID positioning.

---

## Questions For Later Synthesis

1. Is UUID leakage into `synergy_text`/`conflict_text` still occurring in the runs that
   use the "after" format? (We observed it in run 27/llama3.1 before PR #457; PR #457
   removed cross-batch UUIDs; PR #464 was supposed to remove same-batch UUIDs too.)
   A comparison of llama3.1 synergy/conflict texts from BEFORE (run 27) vs the few
   successful gpt-5-nano outputs AFTER (run 57) would confirm whether the remaining
   UUID leakage was actually eliminated.

2. Which hypothesis is lower risk — H1 (revert) or C2 (code fallback + keep new format)?
   H1 is a pure prompt revert with known-good behavior. C2 is a code change that introduces
   complexity but preserves the UUID-at-end goal.

3. Haiku's over-generation (fabricated UUIDs) appears to be a persistent model behavior
   unrelated to UUID position. Is there a structured-output constraint (max_items in the
   response schema) that could cap the number of characterizations and prevent phantoms?

---

## Reflect

The core hypothesis behind PR #464 — "models copy identifiers from the beginning of text
blocks" — is empirically correct for the leakage problem but ignores the reverse: models
also NEED identifiers to be prominent at the start in order to echo them correctly into
structured output. By moving the UUID to the end, PR #464 fixed one problem (copy-paste
leakage) while creating a worse problem (zero matching success for small models).

The OPTIMIZE_INSTRUCTIONS note ("Short hex prefixes and integer indices both caused matching
failures across different model types — keep the full UUID for reliable structured-output
matching") foreshadowed this risk but did not explicitly warn that UUID *position* would
also affect matching. This should be added to the known-problems list.

The PR's other two changes (positive framing instruction, exact-count instruction) appear
harmless — the positive framing may help with UUID leakage in free-text but cannot be
confirmed without checking for UUID patterns in the current run's synergy/conflict texts.
The exact-count instruction did not visibly reduce haiku's over-generation.

---

## PR Impact

### What PR #464 was supposed to fix

1. **UUID leakage** into `synergy_text`/`conflict_text`: Models copy UUIDs from the
   beginning of lever blocks into free-text fields. Solution: move UUID to end.
2. **Positive framing**: Replace implicit "don't use IDs" prohibition with an explicit
   positive instruction to use lever names.
3. **Exact-count instruction**: Reduce over/under-generation.

### Before vs after comparison table

| Metric | Before (runs 27–33) | After (runs 55–61) | Change |
|--------|--------------------|--------------------|--------|
| Total characterized (7 models × 35) | 245 (100%*) | 181 (74%) | **-26%** |
| llama3.1 characterized | 35/35 | 0/35 | **-100%** |
| gpt-5-nano characterized | 35/35 | 10/35 | **-71%** |
| gpt-oss-20b characterized | 35/35 | 32/35 | -9% |
| qwen3/4o-mini/gemini characterized | 105/105 | 105/105 | 0% |
| haiku characterized | 35/35 | 34/35 | -3% |
| Total unknown_lever_id errors | 7 (haiku only) | 84 | **+1100%** |
| Total incomplete errors | 0 | 72 | new |
| Field lengths (working models) | similar | similar | neutral |

\* haiku had 7 extra hallucinated entries before; the 35/35 row counts only correct characterizations.

### Did the PR fix the targeted issue?

**UUID leakage**: Cannot fully confirm from output JSON alone (would need to count UUID
occurrences in synergy/conflict text of successful characterizations). However, the
intent of the fix was correct — models that previously copied the `Lever ID:` prefix into
free-text would no longer see it as the first line.

**Positive framing**: The instruction "always refer to other levers by their name" appears
in the system prompt. Spot-checks of synergy/conflict text show lever names used
correctly (no UUID patterns in successful characterizations). This part likely worked.

**Exact-count**: No measurable effect visible in outputs — haiku still over-generates.

### Regressions

- llama3.1: 100% → 0% (35 → 0 levers)
- gpt-5-nano: 100% → 29% (35 → 10 levers)
- gpt-oss-20b: 100% → 91% (35 → 32 levers)
- haiku: slight worsening (7 → 11 errors, 0 → 1 incomplete)

### Verdict: **REVERT**

PR #464 introduced critical regressions for 2 out of 7 models, with a total lever loss
of 64/245 (26%). The targeted fix (UUID leakage into free-text) was not confirmed to
produce measurable benefit, and UUID leakage was already partially addressed by PR #457.

The OPTIMIZE_INSTRUCTIONS should be updated to document that UUID position affects
structured-output matching in small models, not just UUID leakage.

The recommended next step is either:
- **H1**: Revert to `Lever ID: {uuid}` as the first line of `lever_details_for_prompt`.
- **C2**: Keep the UUID-at-end format but add a name-to-UUID fallback in the matching
  code at line 276 of `enrich_potential_levers.py`, so models returning names also succeed.

---

## Summary

PR #464 moved `Lever ID: {uuid}` from the first line to the last line of each lever
block in `lever_details_for_prompt`, relabeled as `(internal reference: {uuid})`. This
change was designed to prevent UUID copy-paste into synergy/conflict free-text fields.

The change caused a critical failure: llama3.1 went from 100% to 0% success (all 5 plans,
all levers lost), and gpt-5-nano went from 100% to 29% (3/5 plans total failure). The
cause is a positional heuristic in small models: they use the first item in each block
as the identifier to echo into structured output. When the UUID moved to last, they
defaulted to using the lever name, which the matching code does not recognize.

Three models (qwen3, gpt-4o-mini, gemini-flash) were unaffected and remain at 100%.
Haiku's pre-existing UUID hallucination problem was slightly worsened.

**Verdict: REVERT**. The approach of moving UUID to the end is incompatible with small
model structured-output behavior. Either restore the UUID to first position (H1/pure
revert) or add a name-based fallback in the matching code (C2/code fix).
