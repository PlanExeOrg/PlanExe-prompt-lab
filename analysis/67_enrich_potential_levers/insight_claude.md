# Insight Claude

## Overview

This analysis evaluates **PR #468** ("Reduce word counts, add anti-echoing, and guide lever_id
extraction") against the runs examined in analysis 65 (PR #466 baseline).

Both analyses use `baseline/train` as input (5–8 deduplicated levers per plan), making
direct before/after comparison valid.

**Runs compared:**

| Model | Before (analysis 65) | After (this analysis) |
|-------|----------------------|-----------------------|
| ollama-llama3.1 | `4/62_enrich_potential_levers` | `4/76_enrich_potential_levers` |
| openrouter-gpt-oss-20b | `4/63_enrich_potential_levers` | `4/77_enrich_potential_levers` |
| openai-gpt-5-nano | `4/64_enrich_potential_levers` | `4/78_enrich_potential_levers` |
| openrouter-qwen3-30b-a3b | `4/65_enrich_potential_levers` | `4/79_enrich_potential_levers` |
| openrouter-gpt-4o-mini | `4/66_enrich_potential_levers` | `4/80_enrich_potential_levers` |
| openrouter-gemini-2.0-flash-001 | `4/67_enrich_potential_levers` | `4/81_enrich_potential_levers` |
| anthropic-claude-haiku-4-5-pinned | `4/68_enrich_potential_levers` | `4/82_enrich_potential_levers` |

**PR #467 runs (to understand the problem PR #468 is fixing):**

The PR description states PR #467 "caused llama3.1 to return `<lever>uuid</lever>` as lever_id."
Runs 69–75 confirm this. In run 69 (llama3.1, PR #467), the `gta_game` plan shows 10 errors:

```
unknown_lever_id: <lever>1a9003f0-5e0b-42a1-bbc5-b4e99bc1e8bd</lever>
unknown_lever_id: <lever>95b255a0-1645-431b-b2d3-d41327fbcdf0</lever>
```

This resulted in only 30/35 levers for run 69. PR #468 adds system prompt guidance to strip
the XML tags, fixing this regression.

**PR #468 changes (from source code at `enrich_potential_levers.py`):**

1. **Reduced word counts** (lines 139–147): description 80-100 → 50-70 words,
   synergy/conflict 40-60 → 20-40 words.
2. **Anti-echoing** (line 141): `"Add new insight beyond what consequences and review already state"`.
3. **lever_id field description** (line 138): `"The hexadecimal uuid of the lever, without XML tags"`.
4. **System prompt XML guidance** (lines 170–171): `"Each lever in the batch is wrapped in
   <lever>uuid</lever> XML tags. When returning lever_id, extract and return only the
   hexadecimal uuid string inside the tags — strip the XML tags themselves."`.

---

## Negative Things

### N1 — gpt-4o-mini regression: lever_id hyphen stripping (0 → 13 unknown_lever_id errors)

Run 80 (gpt-4o-mini) produces 26 errors across 4 of 5 plans, with 13 `unknown_lever_id` errors
and 13 corresponding `incomplete` errors. The cause: the new lever_id field description
`"The hexadecimal uuid of the lever, without XML tags"` causes gpt-4o-mini to interpret
"hexadecimal uuid" as a raw hex string and strip hyphens from the UUID.

Confirmed by examining run 80, plan sovereign_identity — every returned lever_id is hex-only:
```
unknown_lever_id: bd43cd39f2f043589f5be4dbfdccc474
incomplete:       bd43cd39-f2f0-4358-9f5b-e4dbfdccc474  (same ID, with hyphens)
```

Each `unknown_lever_id` error (hex-only) corresponds exactly to an `incomplete` error (UUID
with hyphens) — the returned ID is the correct lever but with hyphens stripped, so it fails
the `enriched_levers_map` lookup. The match would succeed with a simple `str.replace('-', '')`.

Impact: 13 out of 35 expected levers go unenriched across 4 plans. Only silo (7 levers) is
unaffected — gpt-4o-mini happens to return correct UUIDs for that plan.

Evidence:
- `history/4/80_enrich_potential_levers/outputs/20260308_sovereign_identity/002-12-enriched_levers_raw.json` — 0 levers, 10 errors
- `history/4/80_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json` — 5 levers, 6 errors
- `history/4/66_enrich_potential_levers/outputs/20260308_sovereign_identity/002-12-enriched_levers_raw.json` — 5 levers, 0 errors (before)

### N2 — haiku unknown_lever_id errors persist (5 → 4)

Run 82 (haiku) still produces 4 errors across 1 plan. This is the pre-existing behavior
described in analysis 65 (N1). PR #468 did not worsen this; the slight improvement (5 → 4)
is likely noise.

Evidence:
- `history/4/82_enrich_potential_levers/outputs/20260311_parasomnia_research_unit/002-12-enriched_levers_raw.json` — 4 errors

### N3 — qwen3-30b descriptions now slightly below 50-word target

The target description length is 50-70 words (≈ 300-420 chars). After the PR, qwen3-30b
averages 288 chars per description (≈ 48 words), just below the target. This is minor but
indicates qwen3-30b may need the upper end of the range rather than the lower.

Evidence:
- `history/4/79_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json` — spot check confirms brief descriptions

---

## Positive Things

### P1 — llama3.1 XML tag issue fully resolved (10 → 0 errors)

PR #467 caused llama3.1 to return `<lever>uuid</lever>` as lever_id (run 69: gta_game had
10 errors, only 3/8 levers enriched). PR #468 fixes this completely — run 76 shows 35/35
levers enriched with 0 errors across all 5 plans.

Evidence:
- `history/4/69_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json` — 3 levers, 10 errors (before)
- `history/4/76_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json` — 8 levers, 0 errors (after)

### P2 — gpt-oss-20b timeout eliminated: 3/5 → 5/5 plan completions

Run 63 timed out on hong_kong_game and parasomnia (both at 600s), yielding only 30/35 levers.
Run 77 completes all 5 plans with hong_kong_game finishing in 203s. The reduction in
synergy/conflict word count (approx. 41%) reduces output token count and helps gpt-oss-20b
stay within the 600s timeout.

Evidence:
- `history/4/63_enrich_potential_levers/events.jsonl` — two `plan timeout after 600s` events
- `history/4/77_enrich_potential_levers/events.jsonl` — all 5 `run_single_plan_complete` events, max 203s

### P3 — Synergy/conflict word counts reduced as intended (all models)

All 7 models show meaningful reductions in synergy/conflict field lengths:

| Model | Synergy before | Synergy after | Change | Conflict before | Conflict after | Change |
|-------|---------------|---------------|--------|-----------------|----------------|--------|
| llama3.1 | 347 | 226 | −34% | 317 | 255 | −20% |
| gpt-oss-20b | 347 | 197 | −43% | 336 | 201 | −40% |
| gpt-5-nano | 353 | 206 | −42% | 327 | 234 | −28% |
| qwen3-30b | 204 | 158 | −22% | 206 | 159 | −23% |
| gpt-4o-mini | 295 | 179 | −39% | 325 | 185 | −43% |
| gemini-flash | 289 | 170 | −41% | 297 | 187 | −37% |
| haiku-4-5 | 445 | 277 | −38% | 481 | 287 | −40% |

All models moved toward the 20-40 word target (120-240 chars). The reductions are consistent
and substantial across all models.

Evidence: computed from all output files in `history/4/62–68_enrich_potential_levers` and
`history/4/76–82_enrich_potential_levers`.

### P4 — Description lengths moved toward target range (50-70 words ≈ 300-420 chars)

| Model | Desc before | Desc after | vs Baseline (484) |
|-------|-------------|------------|-------------------|
| llama3.1 | 374 | 309 | 0.64× |
| gpt-oss-20b | 652 | 439 | 0.91× |
| gpt-5-nano | 671 | 443 | 0.92× |
| qwen3-30b | 390 | 288 | 0.59× |
| gpt-4o-mini | 478 | 359* | 0.74× |
| gemini-flash | 473 | 353 | 0.73× |
| haiku-4-5 | 593 | 515 | 1.06× |

*gpt-4o-mini avg computed only over 22 enriched levers; 13 failed to enrich.

The over-verbose models (gpt-oss-20b at 1.35×, gpt-5-nano at 1.39× before) are now below
1× baseline. No model exceeds the 2× warning threshold.

### P5 — No LLMChatError events in any current run

All 7 events.jsonl files for runs 76–82 contain only `run_single_plan_start/complete` events.
No Pydantic schema failures, no LLMChatError entries.

---

## Comparison

### Plan Completion Rate

| Model | Before (62–68) | After (76–82) | Change |
|-------|---------------|---------------|--------|
| llama3.1 | 5/5 | 5/5 | = |
| gpt-oss-20b | 3/5 | **5/5** | **+2** |
| gpt-5-nano | 5/5 | 5/5 | = |
| qwen3-30b | 5/5 | 5/5 | = |
| gpt-4o-mini | 5/5 | 5/5 | = |
| gemini-flash | 5/5 | 5/5 | = |
| haiku-4-5 | 5/5 | 5/5 | = |
| **Total** | **33/35** | **35/35** | **+2** |

Note: plan completion counts timeouts/errors at the pipeline level. gpt-4o-mini's 26 internal
errors are not captured here — all 5 plans completed, but 13 levers within those plans went
unenriched.

### Lever Enrichment Quality (per-lever data completeness)

| Model | Levers enriched before | Levers enriched after | Change |
|-------|----------------------|----------------------|--------|
| llama3.1 | 35/35 | 35/35 | = |
| gpt-oss-20b | 30/35 (2 timeout) | **35/35** | **+5** |
| gpt-5-nano | 35/35 | 35/35 | = |
| qwen3-30b | 35/35 | 35/35 | = |
| gpt-4o-mini | 35/35 | **22/35** | **−13** |
| gemini-flash | 35/35 | 35/35 | = |
| haiku-4-5 | 35/35 (5 discarded extras) | 35/35 (4 discarded extras) | ≈= |
| **Total** | **240/245** | **232/245** | **−8** |

The net lever enrichment rate drops slightly (97.6% → 94.7%) despite gpt-oss-20b's improvement,
because gpt-4o-mini's regression (-13) outweighs the gain (+5).

---

## Quantitative Metrics

### Field Length vs Baseline (all current runs)

Baseline averages (computed from `baseline/train`): desc=484, synergy=286, conflict=298 chars.

| Model | Desc | Desc/Baseline | Synergy | Syn/Baseline | Conflict | Conf/Baseline |
|-------|------|--------------|---------|-------------|---------|--------------|
| Baseline | 484 | 1.0× | 286 | 1.0× | 298 | 1.0× |
| llama3.1 (curr) | 309 | 0.64× | 226 | 0.79× | 255 | 0.86× |
| gpt-oss-20b (curr) | 439 | 0.91× | 197 | 0.69× | 201 | 0.67× |
| gpt-5-nano (curr) | 443 | 0.92× | 206 | 0.72× | 234 | 0.79× |
| qwen3-30b (curr) | 288 | 0.59× | 158 | 0.55× | 159 | 0.53× |
| gpt-4o-mini (curr)* | 359 | 0.74× | 179 | 0.63× | 185 | 0.62× |
| gemini-flash (curr) | 353 | 0.73× | 170 | 0.59× | 187 | 0.63× |
| haiku-4-5 (curr) | 515 | 1.06× | 277 | 0.97× | 287 | 0.96× |

*gpt-4o-mini avg computed over only 22/35 levers; 13 levers failed to enrich.

No model exceeds the 2× warning threshold. All models are now at or below baseline length
for synergy and conflict fields.

### Error Counts

| Model | Errors before | Errors after | Type |
|-------|--------------|--------------|------|
| llama3.1 | 0 | 0 | — |
| gpt-oss-20b | 6 (batch_retry, timeout) | 0 | — |
| gpt-5-nano | 0 | 0 | — |
| qwen3-30b | 0 | 0 | — |
| gpt-4o-mini | 0 | **26** | **13 unknown_lever_id + 13 incomplete** |
| gemini-flash | 0 | 0 | — |
| haiku-4-5 | 5 unknown_lever_id | 4 unknown_lever_id | pre-existing |
| **Total** | **11** | **30** | — |

The increase is entirely from gpt-4o-mini's hyphen-stripping regression.

### Fabricated Percentage Claims (description + synergy + conflict fields)

| Model | Claims before | Claims after | Change |
|-------|--------------|--------------|--------|
| llama3.1 | 6 | 5 | −1 |
| gpt-oss-20b | 3 | 6 | +3 |
| gpt-5-nano | 7 | 6 | −1 |
| qwen3-30b | 6 | 4 | −2 |
| gpt-4o-mini | 11 | 7 | −4 |
| gemini-flash | 0 | 0 | = |
| haiku-4-5 | 14 | 13 | −1 |
| **Total** | **47** | **41** | **−6** |

Baseline has 30 percentage claims across all enriched fields. The shorter word counts
modestly reduce fabricated percentage claims (47 → 41), approaching the baseline count of 30.
The anti-echoing instruction may have contributed to this reduction.

---

## Evidence Notes

Files consulted:
- `history/4/76–82_enrich_potential_levers/outputs/*/002-12-enriched_levers_raw.json` — current enriched lever outputs
- `history/4/62–68_enrich_potential_levers/outputs/*/002-12-enriched_levers_raw.json` — previous enriched lever outputs
- `history/4/69–75_enrich_potential_levers/outputs/*/002-12-enriched_levers_raw.json` — PR#467 runs (llama3.1 XML issue)
- `history/4/76–82_enrich_potential_levers/events.jsonl` — all completed without LLMChatError
- `history/4/63_enrich_potential_levers/events.jsonl` — gpt-oss-20b timeout evidence
- `history/4/77_enrich_potential_levers/events.jsonl` — gpt-oss-20b success evidence
- `history/4/80_enrich_potential_levers/outputs/20260308_sovereign_identity/002-12-enriched_levers_raw.json` — gpt-4o-mini lever_id regression
- `baseline/train/*/002-12-enriched_levers_raw.json` — baseline field length reference
- `PlanExe/worker_plan/worker_plan_internal/lever/enrich_potential_levers.py` lines 28–107
  (OPTIMIZE_INSTRUCTIONS), 136–147 (LeverCharacterization schema), 163–180 (ENRICH_LEVERS_SYSTEM_PROMPT),
  241–248 (lever_details_for_prompt), 276–285 (enriched_levers_map lookup)

Lever_id hyphen-stripping confirmed: every `unknown_lever_id` error maps exactly to an
`incomplete` error whose UUID differs only by having hyphens re-inserted at standard positions:
`bd43cd39f2f043589f5be4dbfdccc474` → `bd43cd39-f2f0-4358-9f5b-e4dbfdccc474`.

---

## PR Impact

### What the PR Was Supposed to Fix

PR #468 supersedes PR #467. PR #467 added word count reductions and anti-echoing, but lacked
guidance on extracting the lever UUID from the XML tags — causing llama3.1 to return
`<lever>uuid</lever>` as lever_id. PR #468 adds:
1. System prompt guidance to strip XML tags from lever_id.
2. lever_id Pydantic field description: `"The hexadecimal uuid of the lever, without XML tags"`.

Secondary goal: reduce response size for gpt-oss-20b to avoid 600s timeouts.

### Before vs After Comparison Table

| Metric | Before (runs 62–68) | After (runs 76–82) | Change |
|--------|--------------------|--------------------|--------|
| Plan completion rate | 33/35 (94.3%) | **35/35 (100%)** | **+2 plans** |
| Lever enrichment rate | 240/245 (98.0%) | 232/245 (94.7%) | −8 levers |
| llama3.1 XML-tag lever_id errors | (0 in runs 62-68, 10 in run 69 PR#467) | **0** | Fixed |
| gpt-oss-20b timeouts | **2** plans | 0 plans | **−2** |
| gpt-4o-mini lever enrichments | 35/35 | **22/35** | **−13** |
| gpt-4o-mini unknown_lever_id | 0 | **13** | **Regression** |
| haiku unknown_lever_id | 5 | 4 | −1 (noise) |
| Total errors | 11 | 30 | +19 |
| Avg synergy length (all models) | 347 chars | 203 chars | −41% |
| Avg conflict length (all models) | 337 chars | 210 chars | −38% |
| Avg desc length (all models) | 508 chars | 389 chars | −23% |
| Fabricated % claims | 47 | 41 | −13% |
| LLMChatError events | 0 | 0 | = |

*Before row uses runs 62–68 except for llama3.1 XML issue which is documented from runs 69 (PR#467).*

### Did the PR Fix the Targeted Issue?

**For llama3.1 (primary target):** YES — the XML-tag guidance in the system prompt prevents
llama3.1 from returning `<lever>uuid</lever>` as lever_id. Run 69 (PR#467) had 10 errors in
gta_game (5 XML-tagged IDs causing 5 unknown + 5 incomplete). Run 76 (PR#468) shows 0 errors
across all 5 plans.

**For gpt-oss-20b (secondary target, timeout):** YES — shorter outputs enabled completion of
all 5 plans within 600s. Run 63 had 2 timeouts (hong_kong at 600s, parasomnia at 600s).
Run 77 completed all plans, with the slowest at 203s.

**For other models:** All were previously stable and remain stable, except gpt-4o-mini.

### Regressions

**gpt-4o-mini lever_id hyphen-stripping** is a new regression introduced by PR #468.

Root cause: the lever_id Pydantic field description `"The hexadecimal uuid of the lever,
without XML tags"` is ambiguous. "Hexadecimal uuid" is interpreted by gpt-4o-mini as a
raw hex string (no hyphens), rather than a standard UUID with hyphens. The phrase was
added to prevent llama3.1 from copying XML tags, but it has the unintended side effect of
confusing gpt-4o-mini about the expected UUID format.

Fix required: change the field description from `"The hexadecimal uuid of the lever,
without XML tags"` to `"The UUID of the lever in standard format
(e.g. xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx), without XML tags"`. The system prompt
guidance already correctly says to "extract and return only the hexadecimal uuid string
inside the tags" — the field description just needs to clarify that hyphens must be preserved.

### Verdict: **CONDITIONAL**

The PR achieves its primary goals: the llama3.1 XML-tag lever_id issue is fixed, and
gpt-oss-20b completes reliably within the timeout. The word count reductions work as intended
across all 7 models without content quality loss.

However, the lever_id field description introduces a regression for gpt-4o-mini that causes
13/35 levers to go unenriched (37% loss). This is a production-quality defect that affects
a commonly used model. The fix is trivial (one-line field description change) and should be
applied before this PR can be fully accepted.

---

## OPTIMIZE_INSTRUCTIONS Alignment

Current OPTIMIZE_INSTRUCTIONS (lines 28–107) status after PR #468:

| Problem | Status in after runs | Notes |
|---------|---------------------|-------|
| Boilerplate descriptions | Reduced — shorter target helps | Anti-echoing may help |
| Word-count padding | **Improved** — 50-70 word target enforced | Verified by field length drop |
| Self-referential synergy/conflict | Not measured in this analysis | Unchanged from PR #466 |
| Phantom lever references | Not measured in this analysis | Unchanged from PR #466 |
| Consequence echoing | Partially addressed | Anti-echo instruction added |
| UUID leakage into free-text | Unchanged (still 0) | PR #466 fixed this |
| UUID leakage into lever_id | **New entry needed** — see below | gpt-4o-mini strips hyphens |
| max_tokens overflow | Not triggered | No LLMChatError events |

**Proposed new entry for OPTIMIZE_INSTRUCTIONS:**

> "lever_id format fragility. When field descriptions contain 'hexadecimal uuid', some
> models (e.g., gpt-4o-mini) interpret this as a raw hex string and strip hyphens from
> the UUID. The standard UUID format is `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` (8-4-4-4-12
> with hyphens). Field descriptions must reference the standard format explicitly or provide
> an example pattern. A normalization fix in `execute()` — stripping hyphens from both key
> and lookup before matching — would make the pipeline robust to this formatting variation."

---

## Questions For Later Synthesis

1. **Should the `enriched_levers_map` lookup be normalized?** The simplest fix is to normalize
   both key and lookup by stripping hyphens: `char.lever_id.replace('-', '')`. This would make
   the pipeline robust to both hex-only and hyphenated UUID formats, regardless of model behavior.
   It would also handle any future edge cases from other models. See C1 below.

2. **Why does gpt-4o-mini only strip hyphens in 4/5 plans (not silo)?** The silo plan
   has 7 levers with two batches. Is the hyphen-stripping behavior batch-position-dependent?
   A larger sample size would confirm whether this is plan-specific or model-behavior drift.

3. **Is the anti-echoing instruction having a measurable effect?** The description field
   now says "Add new insight beyond what consequences and review already state." A spot check
   suggests descriptions are more original in some models (gpt-oss-20b, gpt-5-nano), but
   systematic measurement would require semantic similarity analysis with the input fields.

4. **Should the 50-70 word description target be relaxed for haiku?** Haiku averages
   515 chars (≈ 86 words) — slightly above the 70-word upper bound but also closest to
   baseline (1.06×). Tightening the constraint for haiku may improve conciseness without
   losing quality.

5. **Is qwen3-30b's 288-char avg description a concern?** At 48 words it is barely below
   the 50-word target. Spot checks show coherent content, not truncation. Likely acceptable.

---

## Reflect

PR #468 makes three separate changes that each have a distinct profile:

1. **Word count reduction** (description 80-100→50-70, synergy/conflict 40-60→20-40): Works as
   intended for all 7 models. Benefits: reduced verbosity (closer to baseline length ratios),
   gpt-oss-20b timeout fix. No regressions.

2. **Anti-echoing instruction** ("Add new insight beyond what consequences and review already
   state"): Cannot be precisely measured without semantic similarity analysis. Fabricated
   percentage claims decreased slightly (47→41), which could be partly attributable to this.

3. **lever_id XML guidance**: System prompt guidance works correctly for llama3.1 (XML tags
   stripped). But the Pydantic field description "hexadecimal uuid" is ambiguous and causes
   gpt-4o-mini to strip hyphens. The system prompt text is correct; the field description text
   needs to be revised.

The three-in-one nature of PR #468 makes it harder to cleanly revert. Changes (1) and (2)
are positive; change (3) is mostly positive (system prompt) but has a defective side effect
in the field description. A targeted follow-up (one-line fix to the `lever_id` field
description) would be the right remediation without reverting the beneficial changes.

---

## Potential Code Changes

**H1** — Revise `lever_id` field description to preserve standard UUID format with hyphens.

Change:
```python
lever_id: str = Field(description="The hexadecimal uuid of the lever, without XML tags")
```
To:
```python
lever_id: str = Field(description="The UUID of the lever in standard format (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx), without XML tags")
```

Predicted effect: eliminates gpt-4o-mini hyphen-stripping regression (26 errors → 0).
Risk: minimal — the change is clarification only. Source: line 138 of `enrich_potential_levers.py`.

**C1** — Normalize lever_id lookup in `execute()` to be robust to hyphen format.

At line 277 of `enrich_potential_levers.py`, change:
```python
if char.lever_id in enriched_levers_map:
```
to a normalized lookup that strips hyphens before comparison:
```python
normalized_id = char.lever_id.replace('-', '')
matched_id = next((k for k in enriched_levers_map if k.replace('-', '') == normalized_id), None)
if matched_id:
    enriched_levers_map[matched_id].update(...)
```

This makes the pipeline resilient to hex-only vs hyphenated UUID format variations from any
model. It is a defensive code-level fix independent of prompt wording.

Predicted effect: 0 `unknown_lever_id` errors for gpt-4o-mini even with ambiguous field
description. Protects against future regressions from new models. Risk: low.

**H2** — Test removing the Pydantic field description entirely and relying on the system prompt
XML guidance alone.

The system prompt already states clearly: "extract and return only the hexadecimal uuid string
inside the tags — strip the XML tags themselves." If the Pydantic field description is the
source of the confusion, removing it entirely and relying on system-prompt-level guidance
would avoid the "hexadecimal" ambiguity for all models.

Predicted effect: gpt-4o-mini returns UUIDs with hyphens (following system prompt guidance).
Risk: medium — models that use field descriptions for structured output may produce worse
lever_id compliance without the field-level hint.

---

## Summary

PR #468 ("Reduce word counts, add anti-echoing, and guide lever_id extraction") achieves two
of its three goals successfully:

1. **llama3.1 XML-tag lever_id regression fixed** (PR #467 defect resolved): 10 errors → 0.
2. **gpt-oss-20b timeout eliminated**: 3/5 → 5/5 plan completions.
3. **Word count targets enforced** across all 7 models (synergy/conflict −22% to −44% shorter).

One regression is introduced: gpt-4o-mini interprets `"hexadecimal uuid"` in the field
description as a raw hex string, stripping UUID hyphens and causing 13/35 levers to go
unenriched across 4 plans.

**Key measurements:**

| Metric | Before (62–68) | After (76–82) | Change |
|--------|---------------|---------------|--------|
| Plan completions | 33/35 (94.3%) | 35/35 (100%) | +2 |
| Lever enrichments | 240/245 (98.0%) | 232/245 (94.7%) | −8 |
| gpt-4o-mini enrichments | 35/35 | **22/35** | **−13** |
| gpt-oss-20b timeouts | 2 | **0** | −2 |
| Total internal errors | 11 | 30 | +19 |
| Avg synergy length | 337 chars | 203 chars | −41% |
| Avg conflict length | 347 chars | 210 chars | −40% |

The fix for the gpt-4o-mini regression is a single-line change to the `lever_id` field
description (H1) or a one-time normalization in `execute()` (C1). Both are low-risk. The
other changes in PR #468 should be kept.

**Verdict: CONDITIONAL** — keep the PR contingent on fixing the `lever_id` field description
(`"hexadecimal uuid"` → explicit UUID format with hyphens, or normalize the lookup in code).
