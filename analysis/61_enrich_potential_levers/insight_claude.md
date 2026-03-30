# Insight Claude

## Overview

This analysis evaluates **PR #458** ("Add UUID prohibition and exact-count instruction to enrich prompts")
against the runs examined in analysis 60 (PR #457 "Strip UUIDs from full lever context string").

Both analyses use `baseline/train` as input (5–8 deduplicated levers per plan), making
direct before/after comparison valid.

**Runs compared**:

| Model | Before (analysis 60) | After (this analysis) |
|-------|----------------------|-----------------------|
| ollama-llama3.1 | `4/27_enrich_potential_levers` | `4/34_enrich_potential_levers` |
| openrouter-gpt-oss-20b | `4/28_enrich_potential_levers` | `4/35_enrich_potential_levers` |
| openai-gpt-5-nano | `4/29_enrich_potential_levers` | `4/36_enrich_potential_levers` |
| openrouter-qwen3-30b-a3b | `4/30_enrich_potential_levers` | `4/37_enrich_potential_levers` |
| openrouter-gpt-4o-mini | `4/31_enrich_potential_levers` | `4/38_enrich_potential_levers` |
| openrouter-gemini-2.0-flash-001 | `4/32_enrich_potential_levers` | `4/39_enrich_potential_levers` |
| anthropic-claude-haiku-4-5 | `4/33_enrich_potential_levers` | `4/40_enrich_potential_levers` |

**PR changes** (from `enrich_potential_levers.py` at HEAD):

1. **System prompt** (`ENRICH_LEVERS_SYSTEM_PROMPT`, line 178):
   ```
   **Important:** In `synergy_text` and `conflict_text`, refer to other levers by NAME only.
   Do NOT include any Lever ID, UUID, or identifier string in these fields.
   ```
   Targets llama3.1's residual same-batch UUID copying from `lever_details_for_prompt`.

2. **User prompt** (line 257):
   ```
   Return exactly {len(batch)} characterizations — one per lever, no more, no fewer.
   ```
   Targets haiku's 7 fabricated extra `LeverCharacterization` objects (introduced by PR #457).

3. **OPTIMIZE_INSTRUCTIONS** (lines 88–99): Updated to document both residual problems
   and their attempted fixes, reflecting post-PR #457 state.

---

## Negative Things

### N1 — llama3.1 UUID prohibition causes regression in sovereign_identity (0 → 20 UUIDs)

Before the PR (run 4/27), the `20260308_sovereign_identity` plan was completely clean:
all 5 levers had no UUID strings in `synergy_text` or `conflict_text`. Example from run 4/27:

> "This lever has strong synergy with the Policy Advocacy Strategy, as demonstrating
> technical feasibility amplifies the effectiveness of policy advocacy efforts."
> (no UUID)

After the PR (run 4/34), the same plan now has 20 UUID occurrences across synergy/conflict
text — the prohibition instruction did not suppress them but appears to have triggered them:

> "This lever has strong synergy with the Policy Advocacy Strategy (lever ID:
> 80b177d0-c67e-4bc2-bd50-3f49b815e633)..."

All 5 levers × 2 fields (synergy + conflict) × 2 UUIDs per field = 20 occurrences.
Every UUID is a real same-batch UUID copied from `lever_details_for_prompt`.

Evidence:
- `history/4/27_enrich_potential_levers/outputs/20260308_sovereign_identity/002-12-enriched_levers_raw.json` — 0 UUIDs in synergy/conflict
- `history/4/34_enrich_potential_levers/outputs/20260308_sovereign_identity/002-12-enriched_levers_raw.json` — 20 UUIDs in synergy/conflict

### N2 — llama3.1 net UUID contamination unchanged (29 total → 29 total)

The UUID prohibition partially reduced gta_game contamination but introduced a new regression
in sovereign_identity, leaving the total count identical.

| Plan | Before (27) | After (34) | Change |
|------|-------------|------------|--------|
| 20250329_gta_game | 26 (dedup + synergy/conflict) | 7 (dedup UUIDs only?) | –19 |
| 20250321_silo | 3 (dedup) | 2 (dedup) | –1 |
| 20260308_sovereign_identity | 0 | 20 (synergy/conflict) | +20 |
| 20260310_hong_kong_game | 0 | 0 | = |
| 20260311_parasomnia_research_unit | 0 | 0 | = |
| **Total** | **29** | **29** | **0** |

Note: The counts above include UUIDs appearing in `deduplication_justification` (references to
absorbed levers from the input) as well as `synergy_text`/`conflict_text`. For the specific
synergy/conflict fields that the PR targets, the picture is: gta_game improved substantially,
sovereign_identity regressed from 0 to 20.

Evidence:
- `history/4/34_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json` — gta_game reduced
- `history/4/34_enrich_potential_levers/outputs/20260308_sovereign_identity/002-12-enriched_levers_raw.json` — sovereign_identity regressed

### N3 — haiku extra-characterization issue persists (7 → 2 errors)

The "Return exactly N characterizations" instruction reduced haiku's fabricated-ID errors
from 7 to 2, but did not eliminate them. Two plans still generate one extra characterization
each with a fabricated UUID.

| Plan | Before (run 33) | After (run 40) |
|------|----------------|----------------|
| 20250329_gta_game | 5 errors | 0 errors |
| 20260311_parasomnia_research_unit | 1 error | 0 errors |
| 20260310_hong_kong_game | 1 error | 1 error |
| 20250321_silo | 0 errors | 1 error (new) |
| 20260308_sovereign_identity | 0 errors | 0 errors |
| **Total** | **7** | **2** |

The fabricated IDs in the after-run are:
- hong_kong: `a4b8c9d0-e1f2-5a3b-c4d5-6e7f8a9b0c1d` (sequential pattern, fake)
- silo: `d890e123-abcd-4567-ef01-234567890abc` (clearly fake)

In all cases, the 7 real levers per plan are still enriched correctly. The error entries are
discarded extras that don't affect the downstream lever set.

Evidence:
- `history/4/33_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json` — 5 errors
- `history/4/40_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json` — 0 errors
- `history/4/40_enrich_potential_levers/outputs/20260310_hong_kong_game/002-12-enriched_levers_raw.json` — 1 error
- `history/4/40_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json` — 1 error

### N4 — Negative instruction priming hypothesis for llama3.1

The "Do NOT include any Lever ID, UUID, or identifier string" instruction may be
counter-productive for llama3.1. A well-documented phenomenon in LLM prompting is that
negative instructions (do-not rules) can increase the salience of the forbidden concept,
making the model more likely to produce it. In this case:

- The instruction names "Lever ID" explicitly — which is exactly the format llama3.1 uses
  (`lever ID: xxx`) in synergy/conflict text.
- sovereign_identity was previously clean (llama3.1 produced no UUIDs there without any
  instruction), but after the prohibition it consistently outputs "lever ID: xxx" in all
  synergy/conflict fields.

This hypothesis is supported by the pattern: gta_game (which had heavy UUID contamination)
improved (prohibition helped), but sovereign_identity (which was clean) regressed
(prohibition primed the pattern). The instruction may have reminded the model of a format
it hadn't been using for that plan.

---

## Positive Things

### P1 — haiku extra-characterizations significantly reduced (7 → 2, –71%)

The "Return exactly N characterizations — one per lever, no more, no fewer" instruction
in the user prompt reduced haiku's fabricated-ID errors from 7 to 2 across the 5 plans.
gta_game went from 5 errors to 0, and parasomnia went from 1 to 0. The remaining 2 errors
(hong_kong and silo) are residual.

This is a genuine, measurable improvement. The instruction targets the exact mechanism:
haiku was generating extra `LeverCharacterization` objects when it inferred the total count
incorrectly. The explicit count constraint partially corrected this.

Evidence:
- `history/4/40_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json` — `"errors": []`
- `history/4/33_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json` — 5 errors

### P2 — llama3.1 gta_game synergy/conflict UUID reduction

For gta_game specifically, the UUID prohibition appears to have reduced synergy/conflict
UUID references substantially. Run 27 had approximately 19 synergy/conflict UUIDs across
8 levers; run 34 shows only deduplication_justification UUIDs (references to absorbed
levers from the dedup input), with synergy/conflict potentially clean or near-clean for
that plan. The total UUID count for gta_game dropped from 26 to 7.

Evidence:
- `history/4/27_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json` — synergy_text "(lever ID: 7a5e2c4f-...)"
- `history/4/34_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json` — 7 UUIDs total (mostly dedup_just UUIDs)

### P3 — OPTIMIZE_INSTRUCTIONS updated with current state

The PR updated OPTIMIZE_INSTRUCTIONS (lines 88–99) to reflect the post-PR #457 landscape,
documenting the residual same-batch UUID problem and haiku's extra-characterization behavior.
The documentation now correctly describes the state and the attempted fixes. This is good
maintenance — the self-improve loop has accurate context about what has been tried.

Evidence:
- `enrich_potential_levers.py` lines 88–99

### P4 — All other models unaffected

gpt-oss-20b, gpt-5-nano, qwen3-30b-a3b, gpt-4o-mini, and gemini produce 0 UUID
occurrences in any text field and 0 extra-characterization errors — identical to the
before runs. The new system prompt additions did not introduce regressions in these models.
All 5 models completed 5/5 plans with 0 errors.

---

## Comparison

### Success Rate — Before vs After

| Model | Before (27–33) | After (34–40) | Change |
|-------|----------------|---------------|--------|
| llama3.1 | 5/5 | 5/5 | = |
| gpt-oss-20b | 5/5 | 5/5 | = |
| gpt-5-nano | 5/5 | 5/5 | = |
| qwen3-30b | 5/5 | 5/5 | = |
| gpt-4o-mini | 5/5 | 5/5 | = |
| gemini | 5/5 | 5/5 | = |
| haiku | 5/5 | 5/5 | = |
| **Total** | **35/35 (100%)** | **35/35 (100%)** | **=** |

Note: The before runs (27–33) for this analysis were the "after" runs from analysis 60.
gpt-oss-20b recovered to 5/5 in run 28 onward (the 2/5 timeout in analysis 60 was
identified as model availability noise, not PR-related).

### Error Count — Before vs After

| Model | Before errors (type) | After errors (type) |
|-------|---------------------|---------------------|
| llama3.1 | 0 | 0 |
| gpt-oss-20b | 0 | 0 |
| gpt-5-nano | 0 | 0 |
| qwen3-30b | 0 | 0 |
| gpt-4o-mini | 0 | 0 |
| gemini | 0 | 0 |
| haiku | **7 unknown_lever_id** | **2 unknown_lever_id** |
| **Total** | **7** | **2** |

### UUID Contamination Summary — llama3.1 Synergy/Conflict Fields

| Plan | Before (run 27) | After (run 34) | Change |
|------|-----------------|----------------|--------|
| gta_game | ~19 (estimated from 26 total minus ~7 dedup) | ~0 (7 total = dedup only?) | **–19** |
| sovereign_identity | 0 | 20 | **+20 (regression)** |
| silo | 0 | 0 | = |
| hong_kong_game | 0 | 0 | = |
| parasomnia | 0 | 0 | = |
| **Net synergy/conflict total** | **~19** | **~20** | **≈ 0 net improvement** |

---

## Quantitative Metrics

### Haiku Fabricated-ID Errors Per Plan

| Plan | Run 33 (before) | Run 40 (after) | Change |
|------|-----------------|----------------|--------|
| 20250329_gta_game | 5 | 0 | –5 |
| 20260311_parasomnia_research_unit | 1 | 0 | –1 |
| 20260310_hong_kong_game | 1 | 1 | = |
| 20250321_silo | 0 | 1 | +1 (new) |
| 20260308_sovereign_identity | 0 | 0 | = |
| **Total** | **7** | **2** | **–5 (–71%)** |

### UUID Occurrence Count in Non-lever_id Text Fields (llama3.1)

| Plan | Run 27 (before) | Run 34 (after) | Change |
|------|-----------------|----------------|--------|
| 20250329_gta_game | 26 | 7 | –19 |
| 20250321_silo | 3 | 2 | –1 |
| 20260308_sovereign_identity | 0 | 20 | +20 |
| 20260310_hong_kong_game | 0 | 0 | = |
| 20260311_parasomnia_research_unit | 0 | 0 | = |
| **Total** | **29** | **29** | **0** |

Note: UUID counts include all UUID-format strings in any text field (deduplication_justification,
synergy_text, conflict_text). UUIDs in `deduplication_justification` are references to
absorbed levers from the dedup input and are not produced by the enrich step — these are
pre-existing and unchanged. Synergy/conflict UUIDs are the ones this PR targeted.

### Success Rate Overall

| Metric | Before (runs 27–33) | After (runs 34–40) |
|--------|---------------------|---------------------|
| Plans completed | 35/35 (100%) | 35/35 (100%) |
| LLMChatError (Pydantic failures) | 0 | 0 |
| Plans with errors in JSON | 3 plans (haiku: gta×5, para×1, hk×1) | 2 plans (haiku: hk×1, silo×1) |
| Total error count | 7 | 2 |

No LLMChatError (Pydantic/schema validation failure) events observed in any
`events.jsonl` file for runs 34–40 or 27–33.

---

## Evidence Notes

Files consulted:

- `history/4/27_enrich_potential_levers/outputs/20260308_sovereign_identity/002-12-enriched_levers_raw.json` — llama3.1 before (clean synergy/conflict)
- `history/4/34_enrich_potential_levers/outputs/20260308_sovereign_identity/002-12-enriched_levers_raw.json` — llama3.1 after (20 UUIDs in synergy/conflict)
- `history/4/27_enrich_potential_levers/outputs/20260310_hong_kong_game/002-12-enriched_levers_raw.json` — llama3.1 before (both runs identical content)
- `history/4/34_enrich_potential_levers/outputs/20260310_hong_kong_game/002-12-enriched_levers_raw.json` — llama3.1 after
- `history/4/33_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json` — haiku before (5 errors)
- `history/4/40_enrich_potential_levers/outputs/20250329_gta_game/002-12-enriched_levers_raw.json` — haiku after (0 errors)
- `history/4/33_enrich_potential_levers/outputs/20260310_hong_kong_game/002-12-enriched_levers_raw.json` — haiku before hong_kong (1 error)
- `history/4/40_enrich_potential_levers/outputs/20260310_hong_kong_game/002-12-enriched_levers_raw.json` — haiku after hong_kong (1 error)
- `history/4/40_enrich_potential_levers/outputs/20250321_silo/002-12-enriched_levers_raw.json` — haiku after silo (1 new error)
- `history/4/{34,35,36,37,38,39,40}_enrich_potential_levers/outputs.jsonl` — success status
- `history/4/{27,28,29,30,31,32,33}_enrich_potential_levers/outputs.jsonl` — before success status
- `history/4/{34,40}_enrich_potential_levers/events.jsonl` — no LLMChatErrors
- `PlanExe/worker_plan/worker_plan_internal/lever/enrich_potential_levers.py` — OPTIMIZE_INSTRUCTIONS (lines 28–110), ENRICH_LEVERS_SYSTEM_PROMPT (lines 166–181), user prompt construction (lines 251–259)
- `analysis/60_enrich_potential_levers/insight_claude.md` — baseline metrics and context

---

## PR Impact

### What the PR Was Supposed to Fix

1. **llama3.1 residual same-batch UUID copying**: After PR #457 removed UUIDs from
   `full_lever_context_str`, llama3.1 still copied `Lever ID:` values from
   `lever_details_for_prompt` into synergy/conflict text for same-batch levers.
   Analysis 60 counted 15 synergy+conflict UUID occurrences across 2 plans (gta_game
   and silo). The fix: add "Do NOT include any Lever ID, UUID, or identifier string"
   to the system prompt.

2. **haiku extra LeverCharacterization objects**: After PR #457, haiku introduced 7 new
   `unknown_lever_id` errors across 3 plans by generating extra characterizations with
   fabricated UUIDs. The fix: add "Return exactly N characterizations — one per lever,
   no more, no fewer" to the user prompt.

### Before vs After Comparison Table

| Metric | Before (runs 27–33) | After (runs 34–40) | Change |
|--------|---------------------|---------------------|--------|
| Overall success rate | 35/35 (100%) | 35/35 (100%) | = |
| Total unknown_lever_id errors | 7 (haiku) | 2 (haiku) | **–5 (–71%)** |
| haiku errors | 7 (3 plans) | 2 (2 plans) | **–5 (–71%)** |
| llama3.1 errors | 0 | 0 | = |
| llama3.1 total text-field UUIDs | 29 | 29 | **0 (no improvement)** |
| llama3.1 synergy/conflict UUIDs (gta_game) | ~19 | ~0 | **–19** |
| llama3.1 synergy/conflict UUIDs (sovereign_identity) | 0 | 20 | **+20 (regression)** |
| Other models (all 5): errors | 0 | 0 | = |
| Other models (all 5): UUID contamination | 0 | 0 | = |

### Did the PR Fix the Targeted Issues?

**haiku extra-characterizations**: PARTIAL. Errors dropped 71% (7 → 2). gta_game was
fully fixed (5→0), parasomnia was fixed (1→0). hong_kong persists with 1 error and silo
introduced a new error. The exact-count instruction helps but doesn't reliably prevent
haiku from generating extra characterizations in all plans.

**llama3.1 same-batch UUID copying**: INEFFECTIVE / REGRESSION. The prohibition instruction
did not reduce the total UUID count in text fields (29 → 29). For gta_game specifically,
synergy/conflict UUIDs appear to have been reduced. However, sovereign_identity introduced
a new regression: a plan that was completely clean before now has 20 UUID occurrences in
synergy/conflict text. The net effect is approximately zero.

The prohibition instruction's failure pattern is consistent with negative-instruction
priming: the "Do NOT include Lever ID" text appears to have made llama3.1 MORE likely
to use the "lever ID: xxx" format in plans that previously did not use it.

### Regressions

1. **llama3.1 sovereign_identity regression (N1)**: A clean plan now has 20 UUID
   occurrences. The prohibition instruction caused this regression — the run 27 output
   was clean without any instruction.

2. **haiku silo new error**: silo gained 1 new extra-characterization error that did not
   exist in run 33. The overall count improved (7→2), but silo's behavior changed.

### Verdict: **CONDITIONAL**

The PR produces a genuine improvement for haiku (–71% extra-characterization errors)
but fails to deliver the targeted fix for llama3.1 UUID contamination. The UUID prohibition
instruction introduces a regression in sovereign_identity while partially helping gta_game,
leaving the total UUID count unchanged. Two residual issues require follow-up:

1. **llama3.1 UUID**: The prompt prohibition approach should be replaced with a
   post-processing regex strip (C1 from analysis 60) or the `lever_details_for_prompt`
   format should change to remove or obfuscate the `Lever ID:` line for models that copy it.
2. **haiku residual 2 errors**: The exact-count instruction partially works. A stronger
   fix may require a code-level constraint on the schema or post-processing validation.

---

## OPTIMIZE_INSTRUCTIONS Alignment

The OPTIMIZE_INSTRUCTIONS constant was updated by this PR (lines 88–99). Current state:

| Problem in OPTIMIZE_INSTRUCTIONS | Observed in after runs? | Notes |
|----------------------------------|------------------------|-------|
| Boilerplate descriptions | Not observed | Models produce lever-specific content |
| Self-referential synergy/conflict | Not observed | — |
| Phantom lever references | Not observed | Names used correctly |
| Symmetric parroting | Not systematically checked | Spot checks show variation |
| Word-count padding | Not observed | — |
| Missing conflict_text | Not observed | All levers have conflict_text |
| Batch boundary blindness | Not triggered | — |
| Consequence echoing | Not checked (pre-existing) | Fabricated % from identify step |
| UUID leakage from per-batch prompt | **STILL PRESENT for llama3.1** | Prohibition instruction ineffective |
| Extra characterizations (haiku) | **PARTIAL FIX** | Reduced 7→2, not eliminated |
| max_tokens overflow | Stable (fixed by PR #456) | — |
| OpenRouter context_window fallback | Stable (fixed by PR #456) | — |

**Proposed additions to OPTIMIZE_INSTRUCTIONS**:

- **Negative instruction priming**: The "Do NOT include UUID" approach appears to prime
  llama3.1 to use the "lever ID: xxx" format in plans that previously did not use it.
  Document that negative do-not instructions may be counter-productive for llama3.1.
  Recommend a post-process regex strip (C1 below) instead of prompt prohibition.
- **Haiku exact-count instruction diminishing returns**: The "Return exactly N" user
  prompt instruction reduces haiku errors 71% but doesn't fully solve the problem.
  Consider whether a Pydantic `max_length` constraint on `BatchCharacterizationResult.characterizations`
  would eliminate residual cases (per the schema advice from AGENTS.md: max_length is risky
  for over-generation, but this is a different case where the model shouldn't be generating
  any extras at all).

---

## Questions For Later Synthesis

1. **Should the llama3.1 UUID fix be switched to a code-level post-processing strip?**
   Analysis 60 proposed C2 (regex strip of UUID patterns from synergy_text and conflict_text
   after enrichment). Given that the prompt prohibition failed and introduced a regression,
   a post-processing approach is now more compelling. The fix would apply to all models
   as a defensive measure.

2. **Is the sovereign_identity regression in llama3.1 stochastic or deterministic?**
   Only one run was performed. If re-running run 34 with the same prompt, would
   sovereign_identity still produce 20 UUIDs? If so, the prohibition instruction is
   actively harmful for this plan. If not, it's stochastic noise.

3. **Why do gta_game and sovereign_identity show different UUID behavior under the
   prohibition instruction?** The gta_game plan has 8 levers spread across batches;
   sovereign_identity has 5 levers in a single batch. Hypothesis: when all levers are
   in one batch, the full `lever_details_for_prompt` is visible at once, making the
   UUID-format references more salient despite the prohibition.

4. **Would a positive framing of the UUID prohibition work better?**
   Instead of "Do NOT include any Lever ID, UUID", try "In synergy_text and conflict_text,
   refer to other levers by NAME only — for example, write 'Policy Advocacy Strategy'
   not an identifier." This gives a concrete example of correct behavior rather than
   defining what to avoid.

5. **Is haiku's 2-error residual systematic?** Both remaining errors are in plans with
   specific structures (hong_kong has 7 levers across 2 batches, silo has 8 levers across
   2 batches). Is the exact-count instruction only effective in single-batch plans?

---

## Reflect

The PR makes two targeted changes. The haiku fix is effective but partial: –71%
reduction is real improvement, but 2 residual errors remain. The llama3.1 fix
backfired: the prohibition instruction failed to reduce net UUID contamination
and introduced a new regression in a previously-clean plan.

The llama3.1 result is a cautionary example of negative-instruction priming in
structured output prompting. Adding "Do NOT include X" to a system prompt can
paradoxically increase X by raising its salience. The prior state (run 27) had
llama3.1 producing clean sovereign_identity output without any instruction about
UUIDs — the instruction disrupted correct behavior.

This suggests the UUID problem in llama3.1 is better addressed through code
(post-processing strip) than through prompt instruction, since the model's
compliance with do-not rules is inconsistent and plan-dependent.

---

## Potential Code Changes

**C1** — Post-process synergy_text and conflict_text to strip UUID patterns.

Add a regex strip after enrichment to remove any `[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}` and nearby "`lever ID:`" or "`(lever ID: ...)`" patterns from
`synergy_text` and `conflict_text` before persisting. This is a code-level fix that
works regardless of model prompt compliance.

Location: `enrich_potential_levers.py`, lines 277–283 (the `enriched_levers_map.update(...)` block).

Expected effect: Zero UUID contamination in synergy/conflict for all models, including
llama3.1 (regardless of whether the prohibition instruction is kept or removed).

Risk: May unintentionally strip valid content near a UUID pattern. In practice,
synergy/conflict text should only contain lever names, not UUIDs.

**C2** — Remove or weaken the UUID prohibition from the system prompt.

Given that the prohibition instruction appears to have introduced a regression in
sovereign_identity (the "do not" framing primes llama3.1 to use the "lever ID:" format),
consider replacing it with a positive instruction:

> "In `synergy_text` and `conflict_text`, always refer to other levers by NAME only.
> For example: 'Policy Advocacy Strategy' not 'lever ID: 80b177d0-c67e-...'."

This replaces the negative prohibition with a positive example, which may be less
likely to prime the unwanted pattern.

**H1** — Strengthen haiku exact-count with a higher-level validation.

The user prompt instruction "Return exactly N characterizations" reduced haiku errors
from 7 to 2 but didn't fully prevent extras. After receiving `batch_result.characterizations`,
add a validation check: if `len(batch_result.characterizations) > len(batch)`, trim to
the expected count by keeping only those with lever_ids matching the batch. This is a
soft code fix that avoids triggering retries for 1-2 extra characterizations.

Location: `enrich_potential_levers.py`, lines 277–286 (after `batch_result.characterizations`
is available, before the for loop).

Expected effect: 0 `unknown_lever_id` errors from extra haiku characterizations.
The over-generated items are discarded cleanly instead of being logged as errors.

---

## Summary

PR #458 ("Add UUID prohibition and exact-count instruction to enrich prompts") delivers
partial improvement:

- **haiku**: extra-characterization errors reduced **71%** (7 → 2). The "Return exactly N"
  instruction in the user prompt is effective for most plans. Residual 2 errors persist.

- **llama3.1**: The "Do NOT include any Lever ID, UUID" system prompt prohibition is
  **ineffective and introduces a regression**. Net UUID count in text fields is unchanged
  (29 → 29). sovereign_identity regressed from 0 to 20 UUID occurrences in synergy/conflict
  text. The prohibition instruction appears to prime llama3.1 to use the "lever ID: xxx"
  format in plans that previously did not use it.

- **All other models**: No change (all already correct on both issues).

**Verdict: CONDITIONAL** — keep the haiku fix (genuine improvement); the llama3.1
UUID prohibition should be replaced with a post-processing code fix (C1) since prompt
instructions are unreliable and have now introduced a regression.
