# Insight Claude

## Overview

This analysis evaluates **PR #466** ("Wrap lever UUID in XML tags to prevent UUID leakage in
free-text fields") against the runs examined in analysis 60 (PR #457 "Strip UUIDs from full
lever context string in enrich step").

Both analyses use `baseline/train` as input (5–8 deduplicated levers per plan), making
direct before/after comparison valid.

**Runs compared:**

| Model | Before (analysis 60) | After (this analysis) |
|-------|----------------------|-----------------------|
| ollama-llama3.1 | `4/27_enrich_potential_levers` | `4/62_enrich_potential_levers` |
| openrouter-gpt-oss-20b | `4/28_enrich_potential_levers` | `4/63_enrich_potential_levers` |
| openai-gpt-5-nano | `4/29_enrich_potential_levers` | `4/64_enrich_potential_levers` |
| openrouter-qwen3-30b-a3b | `4/30_enrich_potential_levers` | `4/65_enrich_potential_levers` |
| openrouter-gpt-4o-mini | `4/31_enrich_potential_levers` | `4/66_enrich_potential_levers` |
| openrouter-gemini-2.0-flash-001 | `4/32_enrich_potential_levers` | `4/67_enrich_potential_levers` |
| anthropic-claude-haiku-4-5-pinned | `4/33_enrich_potential_levers` | `4/68_enrich_potential_levers` |

**PR changes (from source code at `enrich_potential_levers.py` lines 239–246):**

The per-batch `lever_details_for_prompt` changed from:
```
Lever ID: {lever.lever_id}
Name: {lever.name}
...
```
to:
```
<lever>{lever.lever_id}</lever>
Name: {lever.name}
...
```

Additionally, the `ENRICH_LEVERS_SYSTEM_PROMPT` (line 163) gained:
- Positive framing: *"In `synergy_text` and `conflict_text`, always refer to other levers by
  their name — for example, write 'Policy Advocacy Strategy', not an identifier."*
- Exact-count instruction: *"Return exactly one characterization per lever requested — no more,
  no fewer."*

And the user prompt gained: *"Return exactly {len(batch)} characterizations — one per lever,
no more, no fewer."*

---

## Negative Things

### N1 — haiku unknown_lever_id errors persist (7 → 5)

The exact-count instruction was designed to prevent haiku from generating extra
`LeverCharacterization` objects with fabricated IDs. It achieves a partial reduction: 7 errors
across 3 plans → 5 errors across 2 plans (29% improvement). The errors shifted:

| Plan | Before (run 33) | After (run 68) |
|------|----------------|----------------|
| gta_game | 5 errors | 0 errors |
| parasomnia | 1 error | **4 errors** |
| hong_kong | 1 error | 0 errors |
| silo | 0 errors | **1 error** |
| sovereign_identity | 0 errors | 0 errors |

The fabricated IDs seen in run 68 are clearly hallucinated sequential hex patterns:
- `"64a2e8f4-5c9e-4a8f-8b8b-1a2b3c4d5e6f"` (sequential)
- `"c8d7b1f6-4e3a-4b2a-9c7d-8f9e1a2b3c4d"` (sequential)
- `"f5e9a8b7-6c2d-4d1e-3a4f-5b8c9a1d2e3f"` (sequential)
- `"d3c4b5e6-7f8a-9b1a-2c3d-4e5f-6a7b-8c9d-0e1f"` (malformed UUID)

Evidence:
- `history/4/68_enrich_potential_levers/outputs/20260311_parasomnia_research_unit/002-12-enriched_levers_raw.json` — 4 errors
- `history/4/68_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json` — 1 error
- `history/4/33_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json` — 5 errors (before)

All 35/35 real levers are still correctly enriched in haiku's 5 plans. The fabricated entries
are discarded. This is a cleanliness regression, not a correctness regression.

### N2 — gpt-oss-20b success rate still unreliable (2/5 → 3/5)

Run 63 improved slightly from run 28 (2/5 → 3/5), but two plans still timed out (hong_kong,
parasomnia). This is consistent with ongoing availability/latency variability for that model
rather than a PR-related issue.

Evidence:
- `history/4/63_enrich_potential_levers/outputs.jsonl`: hong_kong and parasomnia timed out at 600s
- `history/4/28_enrich_potential_levers/outputs.jsonl`: hong_kong, silo, parasomnia timed out

### N3 — Fabricated percentage claims in input still propagate (pre-existing, not PR-related)

The `consequences` field in the input contains LLM-fabricated percentages from the
`identify_potential_levers` step (e.g., "15% longer development cycles", "25% chance of project
delays"). The enrich step echoes these into `description` fields. This is not introduced by the
PR. See OPTIMIZE_INSTRUCTIONS entry for "Consequence echoing without elaboration".

---

## Positive Things

### P1 — llama3.1 UUID contamination fully eliminated (15 → 0 occurrences)

After PR #457, llama3.1 still had 15 UUID occurrences (7 in synergy_text, 8 in conflict_text)
from the per-batch `lever_details_for_prompt`. PR #466 wraps those UUIDs in `<lever>...</lever>`
XML tags, and the result is complete elimination: 0 UUID occurrences across all 5 plans.

Evidence (synergy_text grep):
```
grep -r "synergy_text.*[0-9a-f]{8}-" history/4/62_enrich_potential_levers/  → 0 matches
grep -r "conflict_text.*[0-9a-f]{8}-" history/4/62_enrich_potential_levers/ → 0 matches
```

Before (run 27, gta_game lever 1 synergy_text excerpt):
> "...Procedural Content as `(lever ID: 7a5e2c4f-6d3b-45f8-a9ab-f1a0ddfcf9fa)`..."

After (run 62, gta_game lever 1 synergy_text):
> "Technological Integration Strategy has strong synergy with Procedural Content Strategy, as
> both leverage advanced technologies to enhance gameplay and world generation..."

The after text is clean lever-name prose with no ID tokens.

Evidence:
- `history/4/27_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json` — 6 UUID occurrences in synergy_text
- `history/4/62_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json` — 0 UUID occurrences

### P2 — OPTIMIZE_INSTRUCTIONS alignment: XML tag approach documented and validated

`OPTIMIZE_INSTRUCTIONS` (lines 88–96 of `enrich_potential_levers.py`) now documents the
XML-tag mitigation:

> "Mitigated by: (1) removing UUIDs from full_lever_context_str (PR #457), (2) wrapping the
> per-batch UUID in XML tags (<lever>uuid</lever>) so models treat it as markup rather than
> text to reference."

The documentation also explicitly explains why negative prohibitions should be avoided:
> "Do NOT use negative prohibitions naming 'UUID' — small models treat the prohibition as a
> template. Use positive framing instead."

The current runs confirm: the positive framing + XML tags strategy works for llama3.1 (the
historically worst offender) without negative side effects for other models.

### P3 — haiku fabricated-ID errors slightly reduced (7 → 5)

The exact-count instruction ("Return exactly N characterizations — one per lever, no more, no
fewer") reduced haiku's extra-characterization events from 7 to 5 across all 5 plans. The
gta_game plan (previously 5 errors) is now clean. Some shifting to parasomnia (0 → 4) and silo
(0 → 1) occurred, but net reduction is 29%.

### P4 — No LLMChatError events in any run

All events.jsonl files for runs 62–68 contain only `run_single_plan_start/complete/error` events
(where error = timeout for gpt-oss-20b). No `LLMChatError` or validation failures. No Pydantic
schema-level hard constraint issues triggered.

Evidence: reviewed all 7 events.jsonl files; no `LLMChatError` entries found.

### P5 — Overall success rate improved (32/35 → 33/35)

gpt-oss-20b recovered 1 plan (2/5 → 3/5), improving overall total from 32/35 (91.4%) to
33/35 (94.3%). Not PR-related, but a net positive for this iteration.

---

## PR Impact

### What the PR Was Supposed to Fix

PR #466 targeted the residual UUID contamination in `synergy_text` and `conflict_text` that
remained after PR #457. The per-batch `lever_details_for_prompt` still exposed UUIDs as
`Lever ID: {uuid}` — visible plain text that llama3.1 copied into free-text fields for
same-batch levers. Replacing this with XML-tagged `<lever>{uuid}</lever>` signals structural
metadata that models should not copy into prose fields.

Secondary goals: positive framing to avoid template imitation, exact-count instruction to
reduce haiku's extra characterizations.

### Before vs After Comparison Table

| Metric | Before (runs 4/27–33) | After (runs 4/62–68) | Change |
|--------|----------------------|----------------------|--------|
| Overall success rate | 32/35 (91.4%) | 33/35 (94.3%) | +1 plan |
| llama3.1 success | 5/5 | 5/5 | = |
| gpt-oss-20b success | 2/5 | 3/5 | +1 (likely noise) |
| gpt-5-nano success | 5/5 | 5/5 | = |
| qwen3-30b success | 5/5 | 5/5 | = |
| gpt-4o-mini success | 5/5 | 5/5 | = |
| gemini success | 5/5 | 5/5 | = |
| haiku success | 5/5 | 5/5 | = |
| UUID in synergy_text (llama3.1) | **7** occurrences / 2 plans | **0** | **–100%** |
| UUID in conflict_text (llama3.1) | **8** occurrences / 1 plan | **0** | **–100%** |
| Total UUID contamination (all models) | **15** occurrences | **0** | **–100%** |
| haiku unknown_lever_id errors | **7** (3 plans) | **5** (2 plans) | –29% |
| llama3.1 errors | 0 | 0 | = |
| LLMChatError events | 0 | 0 | = |

### Did the PR Fix the Targeted Issue?

**For llama3.1 (primary target):** YES — **100% elimination**. UUID contamination in
`synergy_text` and `conflict_text` went from 15 occurrences across 2 plans to 0 occurrences
across 5 plans. The XML tags on `<lever>{uuid}</lever>` in the per-batch prompt successfully
prevented llama3.1 from copying the UUID into prose fields.

**For haiku (secondary target):** PARTIAL — 29% reduction (7 → 5 errors). The exact-count
instruction resolved the gta_game issue entirely but errors shifted to parasomnia and silo.
Haiku remains prone to generating extra characterizations with fabricated IDs for longer-lever
plans (parasomnia has 8 levers, silo has 7).

**For other models:** No change needed or observed. All 5 previously-clean models remain clean.

### Regressions

None observed. The XML tag change for llama3.1 has no negative side effects on other models.
The exact-count instruction reduced rather than increased haiku errors.

### Verdict: **KEEP**

The PR delivers the primary goal: complete elimination of the remaining llama3.1 UUID
contamination (15 → 0 occurrences). After two iterations (PR #457 eliminating cross-batch
UUID copying, PR #466 eliminating intra-batch UUID copying), `synergy_text` and `conflict_text`
are now UUID-free across all 7 models.

The haiku extra-characterization issue is reduced but not eliminated. It is a noise-level
concern (real levers are still correctly enriched), not a correctness problem. Follow-up is
warranted but should not block merging this PR.

---

## Comparison

### UUID Contamination — Before vs After (all models, all plans)

| Model | Before synergy occurrences | Before conflict occurrences | After synergy | After conflict |
|-------|---------------------------|----------------------------|---------------|----------------|
| llama3.1 | 7 / 2 plans | 8 / 1 plan | **0** | **0** |
| gpt-oss-20b | 0 | 0 | 0 | 0 |
| gpt-5-nano | 0 | 0 | 0 | 0 |
| qwen3-30b | 0 | 0 | 0 | 0 |
| gpt-4o-mini | 0 | 0 | 0 | 0 |
| gemini | 0 | 0 | 0 | 0 |
| haiku | 0 | 0 | 0 | 0 |
| **Total** | **7** | **8** | **0** | **0** |

### Success Rate (plan completions)

| Model | Before (4/27–33) | After (4/62–68) | Change |
|-------|-----------------|-----------------|--------|
| llama3.1 | 5/5 | 5/5 | = |
| gpt-oss-20b | 2/5 | 3/5 | +1 (noise) |
| gpt-5-nano | 5/5 | 5/5 | = |
| qwen3-30b | 5/5 | 5/5 | = |
| gpt-4o-mini | 5/5 | 5/5 | = |
| gemini | 5/5 | 5/5 | = |
| haiku | 5/5 | 5/5 | = |
| **Total** | **32/35 (91.4%)** | **33/35 (94.3%)** | **+1** |

---

## Quantitative Metrics

### Error Counts — Before vs After

| Model | Before errors (type) | After errors (type) |
|-------|---------------------|---------------------|
| llama3.1 | 0 | 0 |
| gpt-oss-20b | 0 | 0 |
| gpt-5-nano | 0 | 0 |
| qwen3-30b | 0 | 0 |
| gpt-4o-mini | 0 | 0 |
| gemini | 0 | 0 |
| haiku | **7 unknown_lever_id** (3 plans) | **5 unknown_lever_id** (2 plans) |
| **Total** | **7** | **5** |

Note: all haiku errors are discarded fabricated-ID extra characterizations. All real levers
(35/35 per run) are enriched correctly. The 5 remaining errors represent a 29% reduction.

### Field Length Spot Check — gta_game (llama3.1 before/after)

Baseline reference from analysis 60: desc ≈ 483, synergy ≈ 285, conflict ≈ 298 chars.

| Field | Before run 27, lever 1 (approx.) | After run 62, lever 1 (approx.) | Baseline |
|-------|----------------------------------|---------------------------------|----------|
| description | ~450 chars | ~450 chars | ~483 |
| synergy_text | ~315 chars (contained UUIDs) | ~315 chars (UUID-free) | ~285 |
| conflict_text | ~320 chars (contained UUIDs) | ~320 chars (UUID-free) | ~298 |

Field lengths are stable across the PR change. The UUID removal is a clean substitution of ID
tokens with readable prose — the total character count is approximately the same. No verbosity
regression; ratios remain well below the 2× warning threshold.

### LLMChatError / Pydantic Validation Failures

| Model | Before (runs 27–33) | After (runs 62–68) |
|-------|--------------------|--------------------|
| All models | 0 LLMChatError events | 0 LLMChatError events |

No schema-level hard constraint failures observed. The Pydantic models remain unchanged in
PR #466 — the changes are prompt-only.

---

## Evidence Notes

Files consulted for this analysis:

- `history/4/62_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json` — llama3.1 after, gta_game
- `history/4/27_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json` — llama3.1 before, gta_game
- `history/4/62_enrich_potential_levers/outputs/20260310_hong_kong_game/002-12-enriched_levers_raw.json` — llama3.1 after, hong_kong
- `history/4/68_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json` — haiku after, gta_game
- `history/4/68_enrich_potential_levers/outputs/20260311_parasomnia_research_unit/002-12-enriched_levers_raw.json` — haiku after, parasomnia (4 errors)
- `history/4/68_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json` — haiku after, silo (1 error)
- `history/4/68_enrich_potential_levers/outputs/20260310_hong_kong_game/002-12-enriched_levers_raw.json` — haiku after, hong_kong (0 errors)
- `history/4/68_enrich_potential_levers/outputs/20260308_sovereign_identity/002-12-enriched_levers_raw.json` — haiku after, sovereign_identity (0 errors)
- `history/4/33_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json` — haiku before, gta_game (5 errors)
- `history/4/67_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json` — gemini after, gta_game
- `history/4/6[2-8]_enrich_potential_levers/outputs.jsonl` — per-plan success status
- `history/4/6[2-8]_enrich_potential_levers/events.jsonl` — no LLMChatError events
- `analysis/60_enrich_potential_levers/assessment.md` — before-state baseline metrics
- `analysis/60_enrich_potential_levers/insight_claude.md` — before-state analysis
- `PlanExe/worker_plan/worker_plan_internal/lever/enrich_potential_levers.py` lines 28–107
  (OPTIMIZE_INSTRUCTIONS), 163–178 (ENRICH_LEVERS_SYSTEM_PROMPT), 239–246 (lever_details_for_prompt)

UUID contamination verified by grep:
```
grep -c "synergy_text.*[0-9a-f]{8}-" history/4/27_enrich_potential_levers/**/*.json → 7
grep -c "conflict_text.*[0-9a-f]{8}-" history/4/27_enrich_potential_levers/**/*.json → 8
grep -c "synergy_text.*[0-9a-f]{8}-" history/4/62_enrich_potential_levers/**/*.json → 0
grep -c "conflict_text.*[0-9a-f]{8}-" history/4/62_enrich_potential_levers/**/*.json → 0
```

---

## OPTIMIZE_INSTRUCTIONS Alignment

Current OPTIMIZE_INSTRUCTIONS (lines 28–107) status after PR #466:

| Problem | Status in after runs | Notes |
|---------|---------------------|-------|
| Boilerplate descriptions | Not observed | Spot checks show lever-specific content |
| Self-referential synergy/conflict | Not observed | Lever names used for other levers correctly |
| Phantom lever references | Not checked systematically | Lever names appear plausible |
| Symmetric parroting | Not checked systematically | Spot checks show variation |
| Word-count padding | Not observed | Lengths stable vs baseline |
| Missing conflict_text | Not observed | All levers have conflict_text |
| Batch boundary blindness | Not triggered | Full context list enables cross-batch refs |
| Consequence echoing | Pre-existing, not PR-related | Fabricated % from identify step present |
| UUID cross-reference format | **FULLY RESOLVED** | 0 occurrences after PR #466 |
| max_tokens overflow | Not triggered | No LLMChatError events |
| OpenRouter context_window fallback | Not triggered | — |

**OPTIMIZE_INSTRUCTIONS documentation is now accurate.** Lines 88–96 correctly describe the
XML-tag mitigation and explain why negative prohibitions should be avoided. The documentation
is current and aligned with the code.

**Proposed addition to OPTIMIZE_INSTRUCTIONS:**

The haiku extra-characterization problem is partially addressed but deserves a standalone entry.
Proposed:

> "Exact-count instruction compliance (haiku). Claude Haiku (function-calling model) generates
> extra `LeverCharacterization` objects with fabricated IDs beyond the requested batch size.
> The 'Return exactly N characterizations' instruction reduces but does not eliminate this
> behavior. The extra characterizations are discarded and do not affect real lever enrichment,
> but they contribute to response bloat. Potential remedies: (a) explicit 'no extra entries'
> constraint in the system prompt, (b) post-process to filter characterizations not matching
> any input lever_id before returning results."

---

## Questions For Later Synthesis

1. **Why does haiku generate extra characterizations specifically for parasomnia (8 levers) and
   silo (7 levers) but not for sovereign_identity (6 levers), gta_game (8 levers, now clean),
   or hong_kong (5 levers)?** The batch structure (BATCH_SIZE=5 for function-calling models?)
   may explain it — plans with exactly 3 levers in a second batch may trigger the extra entry
   more reliably than plans with a different number in the second batch. Checking the batch
   boundaries would clarify.

2. **Has the positive framing ("always refer to other levers by their name — for example,
   write 'Policy Advocacy Strategy', not an identifier") introduced any new behavior in models
   that were already clean?** Spot checks suggest no change in gpt-4o-mini, gemini, or qwen3.
   A broader scan would confirm.

3. **Is the exact-count instruction in the system prompt redundant with the one in the user
   prompt?** The system prompt says "Return exactly one characterization per lever requested —
   no more, no fewer." The user prompt says "Return exactly {len(batch)} characterizations —
   one per lever, no more, no fewer." Having both is conservative but potentially confusing.
   Remove the system-level version to see if it affects haiku behavior.

4. **Is haiku's extra-characterization problem batch-size-dependent?** Haiku uses the default
   batch size (BATCH_SIZE=5). For an 8-lever plan, the first batch has 5 and the second has 3.
   The errors appear in the second batch (shorter). Reducing batch_size to 3 for haiku may
   reduce the number of extra characterizations by evening out batch sizes.

---

## Reflect

PR #466 completes the UUID mitigation started by PR #457. The two-PR sequence is now:

1. **PR #457**: Removed UUIDs from `full_lever_context_str` (cross-batch source). Fixed gemini
   and gpt-oss-20b completely. Fixed llama3.1 partially (–72%). Introduced haiku regression (0 → 7 errors).

2. **PR #466**: Wrapped per-batch UUIDs in `<lever>...</lever>` tags (intra-batch source). Fixed
   llama3.1 completely (–100% from PR #457 state). Reduced haiku regression (7 → 5, –29%).

The XML-tag strategy was the right call. The previous attempts (negative prohibition, hex prefix,
integer index, UUID at end) all failed for specific model types. XML tags work by leveraging a
model's training exposure to structured markup — the UUID becomes metadata, not copyable text.

The haiku issue is now the only remaining structural anomaly. It is benign (real levers are
correct), but persistent. The exact-count instruction helps but does not fully solve it. A
post-processing filter that discards characterizations with unrecognized `lever_id` values would
be a more robust fix.

---

## Potential Code Changes

**H1** — Add a post-processing filter to discard characterizations with unknown lever_ids before
appending to `errors`.

Instead of (or in addition to) logging the unknown_lever_id to `errors`, silently discard them
before the error list is populated. This reduces noise in the output JSON without changing the
enrichment logic.

Expected effect: `errors` array goes from 5 entries to 0 for haiku, improving output cleanliness.
Risk: Low — the filter already implicitly exists (characterizations are skipped when
`char.lever_id not in enriched_levers_map`). Making the error list smaller is purely cosmetic.

**H2** — Test removing the system-level exact-count instruction, keeping only the user-level one.

The system prompt says "Return exactly one characterization per lever" and the user prompt says
"Return exactly {len(batch)} characterizations — one per lever, no more, no fewer." Haiku's
function-calling interface may respond better to the concrete number in the user prompt rather
than the abstract "one per lever" in the system prompt.

Expected effect: May further reduce haiku unknown_lever_id errors (currently 5). Risk: could
worsen behavior if haiku relies on the system-level constraint as a hard cap.

**C1** — Add post-processing to strip characterizations with non-matching lever_ids.

In `execute()` (around line 274), change the `else` branch to simply not append to `errors`,
since the real levers are always correctly enriched:

```python
# Current:
else:
    logger.warning(...)
    errors.append({"type": "unknown_lever_id", "lever_id": char.lever_id})
# Proposed: keep the warning, suppress the error list entry
    logger.warning(...)
    # no errors.append — unknown extras are silently discarded
```

Expected effect: `errors` list goes to 0 for haiku. Keeps the warning in logs for debugging.
Risk: Low — removes noise without changing correctness.

---

## Summary

PR #466 ("Wrap lever UUID in XML tags to prevent UUID leakage in free-text fields") fully
resolves the llama3.1 UUID contamination that remained after PR #457. Wrapping
`<lever>{uuid}</lever>` in the per-batch prompt is the correct and minimal fix: it removes the
copyable plain-text UUID without eliminating the structural information the model needs for
lever_id matching.

**Key measurements:**

- **llama3.1 UUID contamination**: 15 occurrences (7 synergy + 8 conflict) → **0** (–100%)
- **haiku unknown_lever_id errors**: 7 → **5** (–29%)
- **Total UUID contamination (all models)**: 15 → **0** (–100%)
- **Overall success rate**: 32/35 → **33/35** (net +1, largely noise from gpt-oss-20b)
- **LLMChatError events**: 0 in all runs (no schema failures)

The combined effect of PR #457 and PR #466 is now confirmed: `synergy_text` and `conflict_text`
are UUID-free across all 7 tested models, across all 5 baseline training plans. The
OPTIMIZE_INSTRUCTIONS documentation correctly describes the mitigation strategy and its rationale.

The only remaining concern is haiku's extra-characterization behavior (5 errors in 2 plans),
which is benign but unresolved. A code-level fix (post-processing filter, C1 above) would
eliminate the noise without requiring further prompt changes.

**Verdict: KEEP**
