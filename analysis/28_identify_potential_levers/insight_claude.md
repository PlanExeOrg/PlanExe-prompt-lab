# Insight Claude

## Scope

Analyzing runs `2/03–2/09` (after PR #340) against `1/96–2/02` (before, from analysis 27) for the `identify_potential_levers` step.

**PR under evaluation:** PR #340 "fix: remove template-lock phrase and deduplicate examples"

Changes made:
1. **B1**: Replace the third `review_lever` example in the system prompt to remove the lockable phrase "the options neglect" — confirmed source of llama3.1 secondary template lock (100% gta_game, 92% parasomnia in run 96).
2. **B2**: Remove duplicate examples from the `Lever` Pydantic field description, keeping them only in the system prompt (saves ~150-200 wasted tokens per call, removes doubled copyable-phrase signal).

**Model mapping:**

| Run (before) | Run (after) | Model |
|---|---|---|
| 1/96 | 2/03 | ollama-llama3.1 |
| 1/97 | 2/04 | openrouter-openai-gpt-oss-20b |
| 1/98 | 2/05 | openai-gpt-5-nano |
| 1/99 | 2/06 | openrouter-qwen3-30b-a3b |
| 2/00 | 2/07 | openrouter-openai-gpt-4o-mini |
| 2/01 | 2/08 | openrouter-gemini-2.0-flash-001 |
| 2/02 | 2/09 | anthropic-claude-haiku-4-5-pinned |

---

## Positive Things

1. **Partial reduction in llama3.1 template lock for gta_game.** The primary `review_lever` lock ("The options [fail/neglect/overlook]…") dropped from 16/16 (100%) to 10/16 (62.5%) for gta_game run 03. The first LLM call (levers 1–6) now uses a different format: "[Lever name] lever overlooks/neglects/fails to…" — e.g., "Urban Sprawl Design lever overlooks the potential trade-off…" and "The Gameplay Innovation lever neglects the potential correlation…". This format did not appear in run 96 and shows some diversification away from the single "The options" opener.
   Evidence: `history/2/03_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json` levers 1–6 vs `history/1/96_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`.

2. **Consequences contamination resolved for llama3.1.** In run 96 (before), gta_game levers 1–6 had "A weakness in this approach is that it might overlook…" and "A weakness in this approach is that it might not account for…" embedded in the `consequences` field — a cross-field contamination issue flagged in analysis 27. In run 03 (after), this contamination is absent: all consequences are structurally clean without embedded critique text.
   Evidence: `history/2/03_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json` — no "weakness" text in consequences for any lever.

3. **B2 token savings confirmed.** The activity_overview for parasomnia run 03 (llama3.1) shows `input_tokens: 6433` — a reduction compared to the doubled-example prompt. This validates the 150-200 token saving per call claimed in the PR description.
   Evidence: `history/2/03_identify_potential_levers/outputs/20260311_parasomnia_research_unit/activity_overview.json`.

4. **Partial recovery events decreased (4 → 2).** Before PR: 4 partial recoveries across runs 96, 99, 01 (including one 1/3-call case). After PR: 2 partial recoveries, both in run 03 llama3.1 (sovereign_identity 2/3, hong_kong_game 2/3). No 1/3-call cases.

5. **Content quality stable for all other models.** Runs 05 (gpt-5-nano), 06 (qwen3-30b), 07 (gpt-4o-mini), 08 (gemini-2.0-flash), and 09 (haiku) all completed 5/5 plans with zero errors, zero partial recoveries, and output content consistent with prior batches in length and structure.

---

## Negative Things

1. **B1 did not fix the lock for parasomnia (llama3.1).** The "The options [verb]" pattern in parasomnia reviews was 11/12 (92%) in run 96 and is now 18/18 (100%) in run 03 — marginally worse, not better. The pattern has also broadened: run 03 parasomnia uses "The options assume…", "The options overlook…", "The options neglect…", "The options miss…", "The options do not account for…", and "While…, the options overlook…". Removing example 3's "the options neglect" shifted the model to synonymous openers, not a genuinely different analytical style.
   Evidence: `history/2/03_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json` — 18/18 reviews use "The options [verb]" variants.

2. **Secondary lock shift for gta_game: old lock → new lock.** While the first call (levers 1–6) in run 03 gta_game switched from "The options…" to "[Lever name] lever overlooks/neglects…", this is itself a formulaic pattern applied identically across all 6 levers. The first-call levers now use a different template but still a template. Subsequent calls (levers 7–16) revert to "The options [fail/neglect/overlook/assume]…" exactly as before. The lock is partially displaced but not eliminated.

3. **New fabricated % claims in llama3.1 consequences (first call).** Run 03 gta_game levers 1–6 contain 5 fabricated percentage claims in `consequences` — e.g., "increases development time and resource costs by at least 20%", "increases computational requirements and potential bugs by at least 15%", "increases development time and server requirements by at least 30%". These are fabricated numbers with no basis in the project context. Run 96 gta_game had 0 fabricated % claims in consequences. This regression appears confined to the first LLM call and may be caused by a replacement example 3 that itself contains percentage-claim language in its `consequences` portion.
   Evidence: `history/2/03_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json` levers 1–6 consequences fields.

4. **Success rate regressed: 100% → 97.1%.** Run 04 (gpt-oss-20b) failed on sovereign_identity with: `"Invalid JSON: EOF while parsing a list at line 58 column 5"`. This is a JSON truncation error (LLM output was cut off mid-array). Only 4/5 plans succeeded for gpt-oss-20b. This failure is likely non-deterministic (network timeout or LLM output length cutoff), but it is observable.
   Evidence: `history/2/04_identify_potential_levers/events.jsonl` line 8 — `run_single_plan_error` for sovereign_identity.

5. **"the options neglect" phrase persists in gpt-5-nano.** Examining run 05 (gpt-5-nano) gta_game outputs, lever 2 review reads: "Core tension: balancing funding certainty versus strategic flexibility; weakness: the options neglect explicit risk hedges against milestone slippage or grant-revenue volatility." The exact phrase "the options neglect" appears in the after-PR batch for a different model. This confirms the lock source extends beyond example 3 — examples 1 or 2 also use copyable "the options [verb]" structures that other models copy from.
   Evidence: `history/2/05_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json` lever 2.

6. **llama3.1 still producing duplicate lever names.** Run 03 gta_game includes both "Multplayer Modes" (lever 5, typo) and "Multiplayer Modes" (lever 9) — different levers with the same semantic content. The DeduplicateLevarsTask downstream handles this, but the upstream generation is still producing semantic duplicates.

---

## Comparison

| Metric | Before (runs 96–02) | After (runs 03–09) | Change |
|--------|--------------------|--------------------|--------|
| **Overall success rate** | 35/35 = 100.0% | 34/35 = 97.1% | **-2.9pp REGRESSION** |
| **LLMChatErrors** | 0 | 1 (run 04, gpt-oss-20b, JSON EOF) | **REGRESSION** |
| **Partial recovery events** | 4 (runs 96, 99, 01×2) | 2 (run 03×2) | **IMPROVED** |
| **llama3.1 lock "The options" — gta_game** | 16/16 = 100% (run 96) | 10/16 = 62.5% (run 03) | **PARTIALLY IMPROVED** |
| **llama3.1 lock "The options" — parasomnia** | 11/12 = 92% (run 96) | 18/18 = 100% (run 03) | REGRESSED (sample change) |
| **Consequences contamination (llama3.1 gta_game)** | Present (run 96, levers 1–6) | Absent (run 03) | **FIXED** |
| **Fabricated % in consequences (llama3.1 gta_game)** | 0 (run 96) | 5 (run 03, levers 1–6) | **NEW REGRESSION** |
| **"the options neglect" in gpt-5-nano** | (untracked) | Present (run 05) | PERSISTS |
| **Field length ratios vs baseline** | Stable | Stable | No change |
| **haiku fabricated % claims** | 35 (run 02) | (estimated similar) | STABLE |

---

## Quantitative Metrics

### Template Lock Pattern Counts

| Era | Run | Model | Plan | n_levers | "The options [verb]" count | Rate |
|-----|-----|-------|------|----------|---------------------------|------|
| PREV | 96 | llama3.1 | gta_game | 16 | 16 | 100% |
| CURR | 03 | llama3.1 | gta_game | 16 | 10 | 62.5% |
| PREV | 96 | llama3.1 | parasomnia | 12 | 11 | 92% |
| CURR | 03 | llama3.1 | parasomnia | 18 | 18 | 100% |

Note: gta_game improvement is real but bounded — only first-call levers (1–6) switched to "[Lever name] lever [verb]" format. Second and third call levers (7–16) remain at 100% "The options" pattern. The lock is displaced from example 3's specific phrase but not eliminated.

### Fabricated % Claims in consequences field

| Era | Run | Model | Plan | Levers with fabricated % in consequences |
|-----|-----|-------|------|------------------------------------------|
| PREV | 96 | llama3.1 | gta_game | 0 |
| CURR | 03 | llama3.1 | gta_game | 5 (levers 1–6: "by at least 20/15/25/30/20%") |

### LLMChatErrors and Plan Failures

| Era | Run | Model | Plan | Error type |
|-----|-----|-------|------|------------|
| PREV | 96–02 | all | — | None |
| CURR | 04 | gpt-oss-20b | sovereign_identity | JSON EOF truncation at line 58 |

### Partial Recoveries

| Era | Run | Model | Plan | calls_succeeded / expected |
|-----|-----|-------|------|---------------------------|
| PREV | 96 | llama3.1 | silo | 2/3 |
| PREV | 99 | qwen3-30b | hong_kong_game | 2/3 |
| PREV | 01 | gemini | hong_kong_game | 1/3 |
| PREV | 01 | gemini | sovereign_identity | 2/3 |
| CURR | 03 | llama3.1 | sovereign_identity | 2/3 |
| CURR | 03 | llama3.1 | hong_kong_game | 2/3 |

### Lever Count Comparison

| Era | Run | Model | gta_game levers | parasomnia levers |
|-----|-----|-------|----------------|-------------------|
| PREV | 96 | llama3.1 | 16 | 12 |
| CURR | 03 | llama3.1 | 16 | 18 |
| PREV | 02 | haiku | (estimated ~22) | (estimated ~22) |
| CURR | 09 | haiku | 20 | (not read) |

### Field Length Estimates — Current Runs

Computed from directly read output files. Estimates from sampled plans; not all 5 plans read per run.

| Run | Model | Sampled plan | avg_conseq (est) | avg_review (est) | Notes |
|-----|-------|-------------|-----------------|-----------------|-------|
| 03 | llama3.1 | gta_game (16 levers) | ~136 | ~104 | Shorter reviews in calls 2–3 |
| 03 | llama3.1 | parasomnia (18 levers) | ~155 | ~148 | All "The options" format |
| 09 | haiku | gta_game (20 levers) | ~450 | ~350 | Very long, highly grounded |
| Baseline | — | 5 plans | 279 | 152 | From `baseline/train/` |

Haiku run 09 consequences remain well above baseline (>1.6× for gta_game). Llama3.1 run 03 review length for gta_game is lower than baseline (0.68× estimated), consistent with short formulaic reviews.

---

## Evidence Notes

- gpt-oss-20b failure: `history/2/04_identify_potential_levers/events.jsonl` line 8 — `run_single_plan_error` for sovereign_identity, `EOF while parsing a list at line 58 column 5`
- llama3.1 gta_game template lock improvement: `history/2/03_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json` levers 1–6 use "[Lever name] lever [verb]" vs levers 7–16 use "The options [verb]"
- llama3.1 gta_game fabricated % claims: same file, levers 1–6 consequences contain "by at least X%"
- llama3.1 gta_game contamination resolved: same file, no "weakness" text in any consequences field
- gpt-5-nano lock persistence: `history/2/05_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json` lever 2 review contains "the options neglect"
- Parasomnia template lock: `history/2/03_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json` — 18/18 reviews open with "The options [verb]" variant
- B2 token savings: `history/2/03_identify_potential_levers/outputs/20260311_parasomnia_research_unit/activity_overview.json` — `input_tokens: 6433` for llama3.1 parasomnia
- Partial recoveries: `history/2/03_identify_potential_levers/events.jsonl` lines 7 and 10 — `partial_recovery` for sovereign_identity (2/3) and hong_kong_game (2/3)
- Baseline averages: computed from `baseline/train/*/002-10-potential_levers.json` (analysis 27 established avg_conseq=279, avg_review=152, avg_opts=453)

---

## OPTIMIZE_INSTRUCTIONS Alignment

The current `OPTIMIZE_INSTRUCTIONS` (as reflected in analysis 27, lines 27–80) documents:
1. Overly optimistic scenarios — addressed
2. Fabricated numbers — addressed
3. Hype and marketing copy — addressed
4. Vague aspirations — addressed
5. Fragile English-only validation — addressed
6. Single-example template lock — addressed
7. Template-lock migration pattern — added by PR #339

**Gap identified by this analysis — new point to add to OPTIMIZE_INSTRUCTIONS**: "Removing one copyable phrase from one example does not eliminate a template lock if other examples in the same prompt still use equivalent patterns. When a model shows 'The options [verb]' lock, ALL review_lever examples should be audited for 'The options…' openers, not just the most recently flagged one. If examples 1 and 2 also use 'The options [verb]', replacing example 3 only partially displaces the lock."

**Gap — first-call vs later-call divergence**: The finding that llama3.1's first LLM call now generates a different pattern ("[Lever name] lever [verb]") while second and third calls revert to the old pattern suggests the prompt context for later calls includes enough prior levers to re-establish the old template. This multi-call pattern divergence has not been documented in OPTIMIZE_INSTRUCTIONS.

**Misalignment — new fabricated % claims introduced**: If PR #340's replacement example 3 contains percentage claims in its `consequences` field (the most likely explanation for levers 1–6 of run 03 gta_game suddenly having fabricated %s), this would contradict the OPTIMIZE_INSTRUCTIONS goal of eliminating fabricated numbers. The replacement example should be checked against this guideline.

---

## PR Impact

### What the PR was supposed to fix

1. **B1**: Remove "the options neglect" from the third `review_lever` example — the confirmed source of llama3.1 secondary template lock (100% gta_game, 92% parasomnia in run 96)
2. **B2**: Remove duplicate examples from `Lever` Pydantic field description (save ~150-200 tokens, reduce doubled copyable-phrase signal)

### Before vs After Comparison

| Metric | Before (runs 96–02) | After (runs 03–09) | Change |
|--------|--------------------|--------------------|--------|
| Success rate | 35/35 = 100.0% | 34/35 = 97.1% | **-2.9pp** |
| LLMChatErrors | 0 | 1 (gpt-oss-20b JSON EOF) | **REGRESSION** |
| Partial recoveries | 4 | 2 | IMPROVED |
| llama3.1 lock — gta_game | 100% (16/16) | 62.5% (10/16) | **PARTIALLY IMPROVED** |
| llama3.1 lock — parasomnia | 92% (11/12) | ~100% (18/18) | UNCHANGED / WORSE |
| Consequences contamination (llama3.1) | Present (run 96) | Absent (run 03) | **FIXED** |
| Fabricated % in consequences (llama3.1) | 0 (run 96) | 5 (run 03) | **NEW REGRESSION** |
| "the options neglect" in gpt-5-nano | (not tracked) | Present | PERSISTS |
| Field length ratios | Stable | Stable | No change |

### Did the PR fix the targeted issue?

**Partially, for B1.** The template lock for gta_game was reduced from 100% to 62.5% — a measurable improvement. However:
- Parasomnia shows no improvement (18/18 = 100%), with the model simply substituting equivalent openers
- "the options neglect" itself was reduced (only 2 occurrences in run 03 gta_game vs formerly dominant), but "The options overlook", "The options assume", and "The options fail to" increased proportionally
- gpt-5-nano's run 05 still contains "the options neglect" — confirming the lock source extends to examples 1 or 2, not just the now-changed example 3

**Yes, for B2.** Token savings confirmed (activity_overview shows reduced input tokens). The consequences contamination ("A weakness in this approach is that…") is absent in run 03, which may be attributable to B2's reduced example duplication.

### Were any regressions introduced?

1. **Success rate regression** (100% → 97.1%): The gpt-oss-20b JSON truncation failure is likely non-deterministic. B2 actually reduces prompt token count, which should make truncation *less* likely, not more. This is not credibly caused by PR #340.

2. **New fabricated % claims in llama3.1 consequences**: Run 03 gta_game shows 5 fabricated percentage claims ("by at least X%") in levers 1–6 consequences — claims not present in run 96. This may indicate the replacement example 3's consequences text includes percentage-style language that llama3.1 is copying in the first call. This requires verification against the actual replacement example text in the PlanExe codebase.

3. **Lock not eliminated, only displaced**: The PR's stated goal was to fix the 100% gta_game and 92% parasomnia secondary lock. The actual outcome is 62.5% for gta_game (partial) and ~100% for parasomnia (none). This falls short of the stated objective.

### Verdict

**CONDITIONAL**

B2 (duplicate example removal) is unambiguously positive — confirmed token savings, reduced example duplication, and likely contributed to eliminating consequences contamination in llama3.1. It should be kept regardless.

B1 (template lock fix) only partially achieved its stated goal. gta_game improved from 100% to 62.5%, but parasomnia did not improve, "the options neglect" persists in gpt-5-nano, and the remaining lock is driven by examples 1 and 2 — not just the now-changed example 3. A potential new regression (fabricated % in consequences) may trace to the replacement example text.

Recommended follow-up before declaring this fixed:
1. Audit examples 1 and 2 in `review_lever` system prompt section for "The options [verb]" openers and replace them with non-copyable patterns
2. Check whether the replacement example 3 contains percentage claims in its consequences field (explains run 03 gta_game regression)
3. Run one more iteration targeting all three examples simultaneously

---

## Questions For Later Synthesis

1. **What is the exact text of the new example 3?** The replacement text determines whether the fabricated % claims in llama3.1 consequences are caused by copying from it. If yes, the replacement example itself is a new template-lock source for `consequences`.

2. **Do examples 1 and 2 in the review_lever system prompt section also use "The options [verb]" openers?** If yes, B1 fixed the weakest example but left stronger copies in place. The full fix requires changing all three examples.

3. **Why does llama3.1's first LLM call now produce "[Lever name] lever [verb]" reviews while subsequent calls revert to "The options [verb]"?** Does the presence of prior levers in the context window re-trigger the old pattern? If so, the multi-call architecture may perpetuate lock regardless of prompt changes.

4. **Is the gpt-oss-20b JSON truncation error repeatable?** If re-running sovereign_identity produces a clean result, it is non-deterministic and not PR-related. If it recurs, there may be a context-window issue for that specific model/plan combination.

5. **Did B2 (duplicate removal) cause the consequences contamination to disappear?** In run 96, llama3.1 put "A weakness in this approach is that…" into `consequences` for gta_game levers 1–6. In run 03 this is absent. Is this stable or was run 96 contamination an isolated occurrence?

6. **Is the parasomnia "The options" lock at 100% stable across runs?** Parasomnia showed 92% in run 96 but 100% in run 03. With 12 vs 18 levers the sample sizes differ. Is this consistent with the lock being universal for llama3.1 on parasomnia?

---

## Reflect

The PR's two components have different quality levels. B2 (duplicate removal) is clean and verified — it reduces token waste, has no known downside, and likely contributed to eliminating the consequences contamination. B1 (template lock fix) is a partial fix that confirms the template lock hypothesis (removing the specific phrase did reduce usage of that specific phrase in gta_game's first call) but underestimates how deeply the lock is embedded in the other examples.

The most actionable finding from this batch: the lock is driven by ALL three review_lever examples sharing a common "The options [verb]" structure, not just example 3. Fixing example 3 moved gta_game from 100% to 63%, but left parasomnia unchanged and left other models unaffected. The complete fix requires changing the structural pattern in examples 1 and 2 as well.

The potential new fabricated % regression in llama3.1 consequences (if confirmed to originate from the replacement example 3) is a cautionary reminder: when replacing a template-locking element, care must be taken not to introduce a new one in the replacement text.

---

## Potential Code Changes

**C1 — Audit and replace examples 1 and 2 in review_lever section**

Examples 1 and 2 in `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT`'s review_lever section likely use "The options [verb]" openers similar to the old example 3. Evidence: gpt-5-nano (run 05) and subsequent llama3.1 calls (levers 7–16) still produce "the options neglect/overlook/fail" — these can only be copied from examples 1 or 2 after example 3 was changed. Replace all three examples with review text that avoids "The options" as an opener.

Predicted effect: eliminate the "The options [verb]" template lock completely across all models and all LLM calls, not just partially for gta_game first call.

**C2 — Verify replacement example 3 does not contain fabricated percentages**

If the replacement example 3 introduced by PR #340 contains percentage claims in its `consequences` field (e.g., "increases costs by X%"), this explains why llama3.1 now generates "by at least X%" in first-call consequences. The fix: replace any percentage claims in the new example 3 consequences with specific, qualitative descriptions grounded in the example plan context.

Predicted effect: eliminate the fabricated % claims from llama3.1 first-call consequences.

**H1 — Replace all three review_lever examples with non-"The options" openers**

Every review in the three system prompt examples should demonstrate a different analytical stance (e.g., naming the specific constraint that the options ignore, or naming the stakeholder whose perspective is missing, or describing the conditions under which all three options fail). None should use "The options [verb]" as the sentence opener.

Evidence: run 05 gpt-5-nano review in `history/2/05_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json` lever 2 uses "the options neglect" — showing examples 1 or 2 are still providing this template.

Predicted effect: break the "The options [verb]" pattern across all models and all calls. The partial improvement seen in gta_game run 03 (first call) shows that when one example is changed, models do shift — changing all three should complete the shift.

**H2 — Audit consequences field in the new replacement example 3**

Verify the exact text of the replacement example 3's `consequences` portion (introduced by PR #340). If it uses "increases X by Y%", rewrite to a qualitative description.

Evidence: run 03 llama3.1 gta_game levers 1–6 all show "by at least X%" claims in consequences (`history/2/03_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`) — absent in run 96 — suggesting the replacement example introduced this pattern.

---

## Summary

PR #340 delivers a confirmed benefit through B2 (duplicate example removal): token savings are verified, and consequences contamination in llama3.1 is resolved. B1 (template lock fix) partially achieved its stated goal: the gta_game "The options [verb]" rate dropped from 100% to 62.5%, but parasomnia remained locked at ~100%, and "the options neglect" persists in other models' outputs. The lock's root cause is the shared "The options [verb]" structure in all three review examples — fixing example 3 alone was insufficient. A new potential regression is the appearance of fabricated percentage claims in llama3.1 consequences for gta_game first-call levers (5 instances in run 03 vs 0 in run 96), which may originate from the replacement example 3 text. Success rate regressed from 100% to 97.1% due to a single gpt-oss-20b JSON truncation failure, likely non-deterministic. **Verdict: CONDITIONAL** — keep B2, follow up on B1 by auditing all three review examples for copyable "The options [verb]" openers.
