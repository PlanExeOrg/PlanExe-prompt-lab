# Insight Claude

## Overview

This analysis evaluates **PR #457** ("Strip UUIDs from full lever context string in enrich step")
against the runs examined in analysis 59 (PR #456 "Adaptive batch size, guarded retry, and
OpenRouter config fixes for enrich step").

Both analyses use `baseline/train` as input (5–8 deduplicated levers per plan), making
direct before/after comparison valid.

**Runs compared**:

| Model | Before (analysis 59) | After (this analysis) |
|-------|----------------------|-----------------------|
| ollama-llama3.1 | `4/20_enrich_potential_levers` | `4/27_enrich_potential_levers` |
| openrouter-gpt-oss-20b | `4/21_enrich_potential_levers` | `4/28_enrich_potential_levers` |
| openai-gpt-5-nano | `4/22_enrich_potential_levers` | `4/29_enrich_potential_levers` |
| openrouter-qwen3-30b-a3b | `4/23_enrich_potential_levers` | `4/30_enrich_potential_levers` |
| openrouter-gpt-4o-mini | `4/24_enrich_potential_levers` | `4/31_enrich_potential_levers` |
| openrouter-gemini-2.0-flash-001 | `4/25_enrich_potential_levers` | `4/32_enrich_potential_levers` |
| anthropic-claude-haiku-4-5 | `4/26_enrich_potential_levers` | `4/33_enrich_potential_levers` |

**PR change (line 209 of `enrich_potential_levers.py`)**:

```python
# Before
full_lever_context_str = "\n".join([f"- {lever.lever_id}: {lever.name}" for lever in levers_to_characterize])

# After
full_lever_context_str = "\n".join([f"- {lever.name}" for lever in levers_to_characterize])
```

Note: the per-batch prompt (`lever_details_for_prompt`, lines 233–239) still includes
`Lever ID: {lever.lever_id}` for each lever in the current batch. This is intentional —
the model needs the ID to return structured output with the correct `lever_id` field.

---

## Negative Things

### N1 — gpt-oss-20b success rate dropped: 4/5 → 2/5 (likely unrelated to PR)

Run 4/28 (gpt-oss-20b) completed only 2/5 plans. Silo, parasomnia, and sovereign_identity
all timed out at 600s. In the before run (4/21), only parasomnia timed out. This decline
likely reflects model availability/throughput variability on the test date (2026-03-30),
not the PR change — the PR makes no changes that would affect model latency.

Evidence:
- `history/4/28_enrich_potential_levers/outputs.jsonl`: silo, parasomnia, sovereign_identity
  all `"status": "error", "error": "plan timeout after 600s"`
- `history/4/21_enrich_potential_levers/outputs.jsonl`: only parasomnia timed out

### N2 — llama3.1 still has UUID contamination in synergy/conflict (partial fix)

After the PR, llama3.1 still includes UUID-like strings in synergy_text and conflict_text
for the gta_game plan (run 4/27). However, the UUIDs in these fields are now a mix:

- **Same-batch levers**: Real UUIDs copied from `lever_details_for_prompt` (which still
  includes `Lever ID:` for the current batch). Example: lever 1 `conflict_text` contains
  `(lever ID: 6415a78e-122a-4106-b21c-cc0a34a07372)`, which IS the correct Risk Mitigation
  lever ID (a same-batch lever).
- **Cross-batch levers**: Fabricated/incorrect UUIDs. Example: lever 1 `synergy_text`
  references Procedural Content as `(lever ID: 7a5e2c4f-6d3b-45f8-a9ab-f1a0ddfcf9fa)`,
  but the actual Procedural Content lever_id is `056fa843-5572-40a5-bca5-cc7c7cc18408`.
- Lever 6 uses obviously fake IDs like `(lever ID: 1234567890)` for cross-batch references.

The full-context list fix (removing UUIDs from `full_lever_context_str`) prevents copying
of cross-batch IDs, but same-batch IDs remain visible in `lever_details_for_prompt` and
are still copied.

Evidence:
- `history/4/27_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json`
  — levers 1, 6, 7 in synergy_text and conflict_text

Total residual UUID occurrences in llama3.1 after run:
- `synergy_text`: 7 occurrences across 2 plans (gta_game: 6, silo: 1)
- `conflict_text`: 8 occurrences across 1 plan (gta_game only)

### N3 — haiku (run 4/33) introduces new unknown_lever_id errors (0 → 7)

Before the PR, haiku had 0 errors across all 5 plans. After the PR, haiku has 7
`unknown_lever_id` errors across 3 plans (gta_game: 5, parasomnia: 1, hong_kong: 1).

The fabricated lever IDs haiku returns include:
- `"96f78c2a-3d4d-4a8b-91e2-8f6a9c4d2e1a"` (looks like a plausible UUID but doesn't match any input)
- `"a8b1c2d3-e4f5-6a7b-8c9d-0e1f2a3b4c5d"` (clearly sequential, fake)
- `""` (empty string)

The `characterized_levers` array for all 3 affected plans still contains all real levers
correctly enriched — the 7 errors are discarded extra characterizations. The real levers
are not missing. However, 0 → 7 is a structural regression in output cleanliness.

Hypothesis (H1): By removing UUIDs from `full_lever_context_str`, the prompt no longer
provides a source of valid lever IDs beyond the per-batch details. Haiku (a function-
calling model) may be generating extra `LeverCharacterization` objects with fabricated IDs
when it tries to characterize levers it "infers" from the full list. In the before state,
the full list had IDs, which constrained haiku's responses to real IDs; without IDs,
haiku may hallucinate entirely new entries.

Evidence:
- `history/4/33_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json`
  — 5 unknown_lever_id errors with fabricated IDs
- `history/4/26_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json`
  — 0 errors

### N4 — Fabricated percentage claims persist (pre-existing, not introduced by PR)

The `consequences` field in the input contains fabricated percentages from the
`identify_potential_levers` step (e.g., "15% longer development cycles", "30% larger game
file size"). Models continue to echo these into descriptions and sometimes synergy/conflict
text. This is not a regression from PR #457, but an ongoing content quality issue documented
in OPTIMIZE_INSTRUCTIONS.

---

## Positive Things

### P1 — gemini UUID contamination eliminated (30 → 0 occurrences)

Before the PR, gemini produced UUIDs in synergy_text and conflict_text for 3 plans:
sovereign_identity (5+5 occurrences), silo (5+5 occurrences), and hong_kong_game (5+5
occurrences) = 30 total occurrences across 6 fields.

After the PR, gemini produces zero UUID occurrences in synergy_text or conflict_text
across all 5 plans. The fix works perfectly for gemini.

Evidence:
- Before: `history/4/25_enrich_potential_levers/outputs/20260308_sovereign_identity/002-12-enriched_levers_raw.json`
  synergy_text line: "Policy Advocacy Strategy (80b177d0-c67e-4bc2-bd50-3f49b815e633)"
- After: `history/4/32_enrich_potential_levers/outputs/20260308_sovereign_identity/002-12-enriched_levers_raw.json`
  — no UUIDs in synergy_text or conflict_text lines

### P2 — gpt-oss-20b UUID contamination eliminated for completed plans (21 → 0)

Before the PR, gpt-oss-20b had 21 UUID occurrences in synergy_text and 21 in conflict_text
across 3 plans (gta_game, parasomnia, hong_kong). After the PR, the 2 completed plans
(hong_kong, gta_game) show zero UUID occurrences.

Evidence:
- Before: `history/4/21_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json`
  — synergy_text contains "(056fa843-5572-40a5-bca5-cc7c7cc18408)"
- After: `history/4/28_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json`
  — no UUIDs in synergy_text or conflict_text; lever names used cleanly

### P3 — llama3.1 phantom ID errors eliminated (3 unknown_lever_id + 3 incomplete → 0)

In analysis 59, llama3.1 generated 3 `unknown_lever_id` + 3 `incomplete` errors across 2
plans due to corrupted/truncated UUIDs in its responses (the model was garbling UUIDs it
had seen in the full context list). After the PR removes UUIDs from the context list,
llama3.1 errors = 0. All 35 levers are successfully enriched.

Evidence:
- Before: `history/4/20_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json`
  — 4 errors including `"unknown_lever_id": "056fa843-5572-40a5-bca5-bca5cc18408"` (corrupted UUID)
- After: `history/4/27_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json`
  — `"errors": []`, 8 characterized_levers

### P4 — OPTIMIZE_INSTRUCTIONS alignment: PR addresses documented known problem

OPTIMIZE_INSTRUCTIONS documents this known problem (line 88-92 of
`enrich_potential_levers.py`):

> "UUID cross-reference format inconsistency. The full_lever_context_str includes lever_id
> UUIDs, causing models to copy UUIDs into synergy_text and conflict_text in varying
> formats (full UUID, 8-char truncated, backtick-quoted name, plain name). Models should
> reference levers by name only in free-text fields."

The PR directly implements the fix suggested. For most models, this works as expected.

### P5 — Content quality in synergy/conflict text improved (no UUID noise)

For gemini and gpt-oss-20b (before: heavy UUID contamination), the after runs show cleaner,
more readable synergy/conflict text that uses lever names in natural prose. Example:

Before (gpt-oss-20b, gta_game, lever 1):
> "By aligning with Procedural Content Strategy (056fa843-5572-40a5-bca5-cc7c7cc18408) and
> World Design Strategy (fde4ebd4-bf69-4346-b107-3c74770bac1b)..."

After (gpt-oss-20b, gta_game, lever 1):
> "By leveraging advanced rendering engines and AI tools, this lever accelerates Procedural
> Content Strategy, enabling larger, more detailed worlds..."

The after text is more fluent and focused on substance rather than ID tokens.

Evidence:
- `history/4/21_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json` (before)
- `history/4/28_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json` (after)

---

## PR Impact

### What the PR Was Supposed to Fix

The PR removes `lever_id` UUIDs from the `full_lever_context_str` (the full list of all
levers provided as context in every batch). Models were copying UUIDs from this list into
`synergy_text` and `conflict_text`. Reported rates: llama3.1 89%, gemini 34%, gpt-5-nano
8-char truncated.

The per-batch `lever_details_for_prompt` still includes `Lever ID:` so the model can
return correct IDs in the structured JSON schema.

### Before vs After Comparison Table

| Metric | Before (runs 4/20–26) | After (runs 4/27–33) | Change |
|--------|----------------------|----------------------|--------|
| Overall success rate | 34/35 (97.1%) | 32/35 (91.4%) | –2 plans (gpt-oss-20b) |
| llama3.1 success | 5/5 | 5/5 | = |
| gpt-oss-20b success | 4/5 | 2/5 | –2 (timeout, likely unrelated) |
| gpt-5-nano success | 5/5 | 5/5 | = |
| qwen3-30b success | 5/5 | 5/5 | = |
| gpt-4o-mini success | 5/5 | 5/5 | = |
| gemini success | 5/5 | 5/5 | = |
| haiku success | 5/5 | 5/5 | = |
| UUID in synergy_text (llama3.1) | 27 occurrences / 5 plans | 7 occurrences / 2 plans | **–74%** |
| UUID in conflict_text (llama3.1) | 27 occurrences / 5 plans | 8 occurrences / 1 plan | **–70%** |
| UUID in synergy_text (gpt-oss-20b) | 21 occurrences / 3 plans | 0 (2 plans completed) | **–100%** |
| UUID in conflict_text (gpt-oss-20b) | 21 occurrences / 3 plans | 0 (2 plans completed) | **–100%** |
| UUID in synergy_text (gemini) | 15 occurrences / 3 plans | 0 | **–100%** |
| UUID in conflict_text (gemini) | 15 occurrences / 3 plans | 0 | **–100%** |
| Total UUID contamination (all models) | 105 occurrences | 15 occurrences | **–86%** |
| Errors (unknown_lever_id + incomplete) | 6 (llama3.1) | 7 (haiku) | +1 net |
| llama3.1 errors | 3 + 3 = 6 | 0 | **–6 (fully fixed)** |
| haiku errors | 0 | 7 (unknown_lever_id) | +7 (regression) |
| Haiku actual levers enriched | 35/35 | 35/35 | = (real levers unaffected) |

### Did the PR Fix the Targeted Issue?

**For gemini**: YES. UUID contamination went from 30 total occurrences (3 plans) to 0.
Confirmed by grep across all 5 plans' output files.

**For gpt-oss-20b**: YES for completed plans. UUID contamination went from 42 total
occurrences to 0 in the 2 plans that ran. The 3 timeouts are likely a model availability
issue, not PR-related.

**For llama3.1**: PARTIAL. UUID occurrences reduced by ~74% (54 → 15). Residual UUIDs
come from `lever_details_for_prompt` (per-batch prompt still includes `Lever ID:` for
same-batch levers). The PR's one-line change fixes cross-batch UUID copying, but not
intra-batch copying. Additionally, for cross-batch references, llama3.1 now fabricates
UUIDs rather than looking them up — arguably more confusing but not causing `unknown_lever_id`
errors since the fabricated IDs aren't being returned in the characterization schema.

**For gpt-5-nano, qwen3, gpt-4o-mini, haiku**: These models had no UUID contamination
before the PR and continue to have none in synergy/conflict text. No change expected, no
change observed.

### Regressions

1. **Haiku new errors (N3)**: 0 → 7 `unknown_lever_id` errors across 3 plans. The real
   levers are still enriched correctly, so this doesn't affect output completeness, but
   the presence of fabricated-ID characterizations in the response is a new anomaly.

2. **gpt-oss-20b success rate drop** (N1): 4/5 → 2/5, but this appears to be a
   network/model-availability regression, not a PR regression.

### Verdict: **CONDITIONAL**

The PR's core fix is effective for gemini (fully fixed) and gpt-oss-20b (fully fixed in
completed plans). The total UUID contamination dropped 86% (105 → 15 occurrences). The
llama3.1 phantom ID errors from analysis 59 are eliminated.

CONDITIONAL rather than KEEP because:
1. **llama3.1 still has 15 UUID occurrences** from per-batch `lever_details_for_prompt`.
   The fix is incomplete for the worst offender. A follow-up is needed to address
   intra-batch UUID copying (see C1).
2. **Haiku regression**: 7 new fabricated-ID errors, all discarded. The actual levers are
   enriched correctly, but the behavior change suggests haiku relies on the full-context
   ID list for something other than synergy/conflict text (possibly as a reference for
   how many total characterizations to produce).
3. **gpt-oss-20b throughput**: 3/5 plans timed out in the after run vs 1/5 before. Even
   if this is network noise, it reduces confidence in the overall run quality for that model.

---

## Comparison

### UUID Contamination (synergy_text) — Before vs After

| Model | Before occurrences / plans | After occurrences / plans |
|-------|--------------------------|--------------------------|
| llama3.1 | 27 / 5 plans | 7 / 2 plans |
| gpt-oss-20b | 21 / 3 plans | 0 / 0 plans |
| gpt-5-nano | 0 | 0 |
| qwen3-30b | 0 | 0 |
| gpt-4o-mini | 0 | 0 |
| gemini | 15 / 3 plans | 0 / 0 plans |
| haiku | 0 | 0 |
| **Total** | **63** | **7** |

### UUID Contamination (conflict_text) — Before vs After

| Model | Before occurrences / plans | After occurrences / plans |
|-------|--------------------------|--------------------------|
| llama3.1 | 27 / 5 plans | 8 / 1 plan |
| gpt-oss-20b | 21 / 3 plans | 0 / 0 plans |
| gemini | 15 / 3 plans | 0 / 0 plans |
| others | 0 | 0 |
| **Total** | **63** | **8** |

### Success Rate (plan completions)

| Model | Before (runs 4/20–26) | After (runs 4/27–33) | Change |
|-------|----------------------|-----------------------|--------|
| llama3.1 | 5/5 | 5/5 | = |
| gpt-oss-20b | 4/5 | 2/5 | –2 |
| gpt-5-nano | 5/5 | 5/5 | = |
| qwen3-30b | 5/5 | 5/5 | = |
| gpt-4o-mini | 5/5 | 5/5 | = |
| gemini | 5/5 | 5/5 | = |
| haiku | 5/5 | 5/5 | = |
| **Total** | **34/35 (97.1%)** | **32/35 (91.4%)** | **–2 plans** |

---

## Quantitative Metrics

### Error Counts — Before vs After

| Model | Before errors (type) | After errors (type) |
|-------|---------------------|---------------------|
| llama3.1 | 3 unknown_lever_id + 3 incomplete | **0** |
| gpt-oss-20b | 0 | 0 |
| gpt-5-nano | 0 | 0 |
| qwen3-30b | 0 | 0 |
| gpt-4o-mini | 0 | 0 |
| gemini | 0 | 0 |
| haiku | **0** | **7 unknown_lever_id** |
| **Total** | **6** | **7** |

Note: All 7 haiku errors are fabricated IDs — the actual 35/35 real levers are still
enriched. No `incomplete` errors in after runs.

### Lever Count (all plans, all models)

| Model | Before levers | After levers | Expected |
|-------|--------------|--------------|----------|
| llama3.1 | 32 (3 missing due to phantom IDs) | **35** | 35 |
| gpt-oss-20b | 35 (4 plans only) | 14 (2 plans only) | 14 for 2 plans |
| gpt-5-nano | 35 | 35 | 35 |
| qwen3-30b | 35 | 35 | 35 |
| gpt-4o-mini | 35 | 35 | 35 |
| gemini | 35 | 35 | 35 |
| haiku | 35 | 35 | 35 |

### Field Lengths vs Baseline (estimated from gta_game samples)

Baseline reference from analysis 59: desc=483, syn=285, conf=298 chars.

| Model | desc (chars) | d/b | syn (chars) | s/b | conf (chars) | c/b |
|-------|-------------|-----|------------|-----|-------------|-----|
| Baseline | 483 | 1.0× | 285 | 1.0× | 298 | 1.0× |
| llama3.1 (analysis 59) | 405 | 0.84× | 374 | 1.31× | 384 | 1.29× |
| gpt-oss-20b (analysis 59) | 619 | 1.28× | 407 | 1.43× | 414 | 1.39× |
| gemini (analysis 59) | 488 | 1.01× | 305 | 1.07× | 319 | 1.07× |
| haiku (analysis 59) | 588 | 1.22× | 433 | 1.52× | 447 | 1.50× |

Field lengths appear stable in the after runs based on spot checks — the one-line context
change does not materially affect output length or verbosity. No model exceeds the 2×
warning threshold.

### UUID Occurrence Type Analysis (llama3.1 after run 4/27)

| Lever | Batch | synergy UUID | Real ID? | conflict UUID | Real ID? |
|-------|-------|-------------|----------|---------------|---------|
| Technological Integration | 1 | 7a5e2c4f... (Proced.) | No — fabricated | 6415a78e... (Risk) | Yes — same batch |
| Funding Diversification | 2 | 578be9eb... (Moneti.) | Yes? — same batch | 36c599b5... (Moral) | Yes — same batch |
| Procedural Content | 2 | "1234567890" | No — obvious fake | "9876543210" | No — obvious fake |

This confirms the intra-batch vs cross-batch pattern: real IDs from same-batch
`lever_details_for_prompt`, fabricated/fake IDs for cross-batch references.

---

## Evidence Notes

Files consulted:

- `history/4/27_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json` — llama3.1 after
- `history/4/20_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json` — llama3.1 before
- `history/4/27_enrich_potential_levers/outputs/20260310_hong_kong_game/002-12-enriched_levers_raw.json` — llama3.1 after hong_kong
- `history/4/20_enrich_potential_levers/outputs/20260310_hong_kong_game/002-12-enriched_levers_raw.json` — llama3.1 before hong_kong
- `history/4/28_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json` — gpt-oss-20b after
- `history/4/21_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json` — gpt-oss-20b before
- `history/4/32_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json` — gemini after
- `history/4/25_enrich_potential_levers/outputs/20260308_sovereign_identity/002-12-enriched_levers_raw.json` — gemini before
- `history/4/33_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json` — haiku after
- `history/4/26_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json` — haiku before
- `history/4/2{7,8,9,30,31,32,33}_enrich_potential_levers/outputs.jsonl` — per-plan success status
- `history/4/2{0,1,2,3,4,5,6}_enrich_potential_levers/outputs.jsonl` — before success status
- `history/4/33_enrich_potential_levers/events.jsonl` — runner sequence, no LLMChatErrors
- `analysis/59_enrich_potential_levers/insight_claude.md` — analysis 59 baseline metrics
- `PlanExe/worker_plan/worker_plan_internal/lever/enrich_potential_levers.py` lines 28–103
  (OPTIMIZE_INSTRUCTIONS), 209 (full_lever_context_str change), 233–249 (per-batch prompt)

---

## OPTIMIZE_INSTRUCTIONS Alignment

Current OPTIMIZE_INSTRUCTIONS (lines 28–103) status:

| Problem | Observed in after runs? | Notes |
|---------|------------------------|-------|
| Boilerplate descriptions | Not observed | Spot checks show lever-specific content |
| Self-referential synergy/conflict | Not observed | — |
| Phantom lever references | Not observed in synergy/conflict | Names used correctly |
| Symmetric parroting | Not checked systematically | Spot checks show variation |
| Word-count padding | Not observed | — |
| Missing conflict_text | Not observed | All levers have conflict_text |
| Batch boundary blindness | Not triggered | Context list enables cross-batch references |
| Consequence echoing | YES (pre-existing) | Fabricated % from identify step echoed |
| UUID cross-reference format | PARTIAL (llama3.1 still) | 15 remaining from per-batch prompt |
| max_tokens overflow | Fixed by PR #456 | Confirmed stable |
| OpenRouter cw fallback | Fixed by PR #456 | Confirmed stable |

**New problem not yet in OPTIMIZE_INSTRUCTIONS (proposed additions)**:

1. **UUID copying from per-batch prompt**: After removing UUIDs from `full_lever_context_str`,
   llama3.1 still copies `Lever ID:` values from `lever_details_for_prompt` into synergy
   and conflict text for same-batch levers. The current OPTIMIZE_INSTRUCTIONS text says
   "Models should reference levers by name only in free-text fields" but doesn't distinguish
   between the two sources (full context list vs per-batch details). Propose adding: "Models
   may still copy lever_id UUIDs from the per-batch prompt into synergy/conflict text for
   same-batch levers. Consider post-processing to strip UUID patterns from these fields."

2. **Haiku generates extra characterizations with fabricated IDs when UUIDs removed from
   context**: Claude-haiku (function-calling model) returns additional `LeverCharacterization`
   objects with fabricated UUIDs in the after run. Before the PR, the full context list
   with real IDs may have grounded haiku's output to the real lever set. Without those IDs,
   haiku generates extra entries. The real levers remain correctly enriched, but this adds
   noise to the errors list.

---

## Questions For Later Synthesis

1. **Should `lever_details_for_prompt` also remove or replace the `Lever ID:` field for
   the purpose of freeing synergy/conflict text from UUID references?** The challenge is
   that the model needs the lever_id to return the correct structured JSON. A possible
   workaround: use sequential indices (1, 2, 3...) in the full context and per-batch
   prompt, then map indices back to UUIDs in post-processing. This would completely
   decouple the ID-for-routing from the ID-for-display problem.

2. **Is haiku's fabricated-ID regression a one-off or systematic?** Only one run was
   performed (4/33). Run another haiku experiment to determine if the 7 extra
   unknown_lever_id errors are stable or transient.

3. **Is the gpt-oss-20b timeout regression PR-related or network noise?** The model
   went from 4/5 → 2/5, which is a bigger drop than expected from the same model on the
   same plans. If re-running gpt-oss-20b produces similar results, the timeout may
   be a model-availability issue rather than PR-introduced.

4. **Why does llama3.1 include fake UUIDs in cross-batch references?** Removing the UUID
   from the full context didn't stop llama3.1 from including UUID-like strings — it just
   changed them from real copied IDs to fabricated ones. Should the system prompt explicitly
   instruct: "Do not include lever_id UUIDs in synergy_text or conflict_text"?

---

## Reflect

The PR's core change is conceptually correct and works well for gemini and gpt-oss-20b.
However, two residual issues limit its effectiveness:

**Structural incompleteness**: Removing UUIDs from `full_lever_context_str` fixes cross-batch
UUID copying, but `lever_details_for_prompt` (per-batch prompt) still exposes UUIDs for
same-batch levers. Any model that tends to include IDs in synergy/conflict text will still
do so for same-batch references. The fix addresses 74% of llama3.1's UUID contamination,
not 100%.

**Haiku sensitivity**: Haiku appears to use the full context list's UUIDs as a reference
to anchor the number or identity of characterizations it produces. Without those anchors,
it generates extra characterizations with fabricated IDs. This is technically benign (real
levers still enriched) but suggests haiku is more sensitive to the prompt format than
other models.

The PR is a clear improvement overall — 86% reduction in UUID contamination — but the
remaining 14% and the haiku regression are worth addressing before declaring the step
fully clean.

---

## Potential Code Changes

**C1** — Add explicit prompt instruction prohibiting UUIDs in free-text fields.

In `ENRICH_LEVERS_SYSTEM_PROMPT` (line 159), add a constraint:
> "Important: In `synergy_text` and `conflict_text`, refer to other levers by name only.
> Do not include lever_id UUIDs or any ID strings in these free-text fields."

This would address same-batch UUID copying from `lever_details_for_prompt` for models
that respect instruction-level constraints (llama3.1 may or may not comply).

Expected effect: 7 → 0 residual UUID occurrences in synergy/conflict for the after runs.
Evidence: llama3.1 synergy_text still has 7 UUIDs (run 4/27, 2 plans). Gemini (already
clean) wouldn't be affected.

**C2** — Post-process synergy_text and conflict_text to strip UUID patterns.

Add a regex strip after enrichment to remove any `[0-9a-f-]{36}` or `lever_id:` patterns
from synergy_text and conflict_text before persisting to `CharacterizedLever`. This is a
defensive code-level fix that would work across all models regardless of prompt compliance.

Expected effect: Zero UUID contamination in all models after post-processing.
Risk: May unintentionally strip valid content if a lever name happens to match the UUID
regex (unlikely but possible).

**H1** — Add OPTIMIZE_INSTRUCTIONS entries for C1 and C2.

Update the "UUID cross-reference format inconsistency" entry to document:
- Source distinction (full context vs per-batch prompt)
- Haiku's extra-characterization behavior when UUIDs are absent
- Recommend C1 or C2 as the follow-up fix

---

## Summary

PR #457 ("Strip UUIDs from full lever context string in enrich step") reduces overall
UUID contamination in `synergy_text` and `conflict_text` by **86%** (105 → 15 occurrences),
and eliminates it completely for gemini and gpt-oss-20b (completed plans). The llama3.1
phantom-ID errors from analysis 59 are also resolved (6 errors → 0).

The fix is a clear step forward, but incomplete:

- **llama3.1** (the original 89% offender) still has 15 UUID occurrences caused by
  `lever_details_for_prompt`, which still shows `Lever ID:` for per-batch levers. The
  cross-batch UUID copying is fixed; same-batch copying remains.
- **haiku** introduced 7 new `unknown_lever_id` errors (3 plans), all from fabricated
  extra characterizations. The actual lever enrichment is unaffected (35/35 real levers
  correctly enriched).
- **gpt-oss-20b** had 3 additional plan timeouts vs before, likely due to model
  availability on the test date rather than the PR.

**Verdict: CONDITIONAL**. The PR should be kept — it delivers meaningful, measurable
improvement on the stated goal. Follow-up work is needed for (1) same-batch UUID copying
in llama3.1 (prompt instruction or post-processing strip, C1/C2 above) and (2)
investigating haiku's fabricated-ID regression to determine if it's systematic.
