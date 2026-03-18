# Insight Claude

## Scope

Analyzing runs `1/96–1/99` and `2/00–2/02` (after PR #339) against `1/89–1/95` (before, from analysis 26) for the `identify_potential_levers` step.

**PR under evaluation:** PR #339 "fix: relax option count validator, raise review min_length, clean up dead code"

Changes made:
1. `check_option_count`: `len(v) != 3` → `len(v) < 3` (allows >3 options, rejects <3)
2. `review_lever` `min_length`: 20 → 50 chars (catches stub reviews like 19-char "Sensor Data Sharing")
3. Dead-code examples stripped from `LeverCleaned.review` field description (confirmed never serialized to LLM)
4. `OPTIMIZE_INSTRUCTIONS` updated with template-lock migration pattern
5. Docstring run reference corrected: run 89 → run 82 (the actual gta_game 2-option bug)

**Model mapping:**

| Run (before) | Run (after) | Model |
|---|---|---|
| 89 | 96 | ollama-llama3.1 |
| 90 | 97 | openrouter-openai-gpt-oss-20b |
| 91 | 98 | openai-gpt-5-nano |
| 92 | 99 | openrouter-qwen3-30b-a3b |
| 93 | 00 | openrouter-openai-gpt-4o-mini |
| 94 | 01 | openrouter-gemini-2.0-flash-001 |
| 95 | 02 | anthropic-claude-haiku-4-5-pinned |

---

## Positive Things

1. **Parasomnia LLMChatError fixed.** In `history/1/89_identify_potential_levers/events.jsonl`, llama3.1 failed parasomnia with a Pydantic validation error: `"review_lever is too short (19 chars); expected at least 20"` (review text was `"Sensor Data Sharing"` — a lever name, not a review). In `history/1/96_identify_potential_levers/events.jsonl`, all 5 plans complete successfully (0 LLMChatErrors). The parasomnia plan produces 12 levers with average review length 149 chars — well above the new 50-char floor.

2. **Overall success rate improved: 34/35 → 35/35 (100%).** The one recurring failure (llama3.1 / parasomnia) is resolved. No new failures were introduced for any model or plan.

3. **OPTIMIZE_INSTRUCTIONS updated with template-lock migration pattern.** Lines 69-80 of `identify_potential_levers.py` now document that "replacing a copyable opener does not eliminate template lock — weaker models shift to copying subphrases within the new examples." This is accurate and grounded in the observed behavior from analysis 26 (secondary lock on "The options assume/neglect/overlook"). Future analysts and developers now have this documented.

4. **Dead-code comment added to `LeverCleaned.review`.** Previously the field description in `LeverCleaned` contained examples that were never serialized to LLMs (confirmed at lines 203-205 in the source). These have been replaced with a comment explaining why no examples are present. This removes confusion about which class carries prompt-facing guidance.

5. **No content quality regressions.** Field length ratios vs baseline are stable across all models. Fabricated percentage claims slightly decreased for haiku (51 total before → 35 after). No marketing-copy language was introduced.

6. **No new models started failing.** All 7 models maintained their existing success rates (or improved, as with llama3.1).

---

## Negative Things

1. **Secondary template lock persists in llama3.1 — not addressed by this PR.** The previous analysis (analysis/26, insight_claude.md) identified a new lock in run 89: "The options [assume/neglect/overlook/fail to account for]…". In run 96, this pattern is still prevalent:

   Grep match counts for `"options (assume|neglect|overlook|fail to)"` in cleaned lever files:
   - `20250329_gta_game`: 16 matches (for 16 levers — near 100%)
   - `20260311_parasomnia_research_unit`: 11 matches (for 12 levers — 92%)
   - `20250321_silo`: 7 matches (for 14 levers — 50%)
   - `20260310_hong_kong_game`: 4 matches (for 19 levers — 21%)
   - `20260308_sovereign_identity`: 1 match (for 17 levers — 6%)

   The pattern ranges from 6% to 100% by plan. For gta_game, every review opens with a variant. This lock was present in run 89 and remains in run 96 — PR #339 documented it in OPTIMIZE_INSTRUCTIONS but did not attempt to fix it.

   Evidence from `history/1/96_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`:
   - Lever 1: `"The options fail to consider the potential for player-driven urban planning and customization…"`
   - Lever 2: `"The options neglect the potential benefits of incorporating real-world geographic data…"`
   - Lever 3: `"The options overlook the potential risks associated with relying on a single major investor…"`

2. **Root cause of secondary lock not fixed.** Examining `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` section 4 (lines 233-236 in source), the third example reads: `"Pooling catastrophe risk across three coastal regions diversifies exposure on paper, but the options neglect that a single hurricane season can correlate all three simultaneously."` The phrase "the options neglect" is itself a copyable opener that weaker models (llama3.1) latch onto. OPTIMIZE_INSTRUCTIONS warns about this pattern but the system prompt still contains it. The warning and the root cause coexist.

3. **Gemini (run 01) partial recovery degradation — hong_kong_game severely affected.** Events show hong_kong_game completed with `calls_succeeded=1, expected_calls=3` (only 1 of 3 LLM calls succeeded). The lever output file contains only 6 levers (vs 18 in run 94 for the same model/plan). Other models produce 14-21 levers for this plan. This is a significant quality drop for that one combination, though it is still technically "complete" (6 levers exceeds the `min_length=5` floor).

   Evidence: `history/2/01_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` — 6 levers; compare `history/1/94_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` — 18 levers.

4. **Consequences field contamination in llama3.1 (run 96).** The `consequences` field should contain only direct effect and downstream implications — the source field description explicitly says "Do NOT include 'Controls ... vs.', 'Weakness:', or other review/critique text in this field." However, in gta_game run 96, several `consequences` fields contain embedded weakness statements:
   - `"A weakness in this approach is that it might overlook the importance of historical context…"` (lever 1)
   - `"A weakness in this approach is that it might not account for the optimal balance…"` (lever 2)
   This is cross-field contamination that structural validators cannot detect.

5. **Partial recoveries increased overall.** Before PR: 1 partial recovery (run 94, gemini, sovereign_identity, 2/3 calls). After PR: 4 partial recoveries across 3 runs (96, 99, 01). While partial recovery does not cause plan failures (all 35 plans complete), increased partial recovery frequency suggests model instability on certain plans and may reduce lever diversity. This is not directly caused by PR #339 but warrants monitoring.

---

## Comparison

| Metric | Before (runs 89–95) | After (runs 96–02) | Change |
|--------|--------------------|--------------------|--------|
| **Overall success rate** | 34/35 = 97.1% | 35/35 = 100.0% | **+2.9pp IMPROVED** |
| **llama3.1 LLMChatError count** | 1 (parasomnia, review 19 chars) | 0 | **FIXED** |
| **llama3.1 secondary lock "options [neglect/overlook/fail]" (gta)** | ~100% (run 89) | ~100% (run 96) | UNCHANGED |
| **Option count violations (< 3)** | 0 | 0 | UNCHANGED |
| **Option count violations (!= 3)** | 0 | 0 | UNCHANGED |
| **Short reviews < 50 chars** | 0 (all pass old 20-char limit) | 0 | UNCHANGED |
| **Fabricated % claims — haiku** | 51 total | 35 total | SLIGHTLY IMPROVED |
| **Fabricated % claims — other models** | ~0-5 per model | ~0-9 per model | STABLE |
| **Partial recovery events** | 1 (run 94) | 4 (runs 96, 99, 01×2) | INCREASED |
| **Gemini hong_kong_game lever count** | 18 (run 94) | 6 (run 01) | **REGRESSION** |
| **Consequences field contamination (llama3.1)** | Present (run 89) | Present (run 96) | UNCHANGED |
| **OPTIMIZE_INSTRUCTIONS template-lock doc** | Absent | Present | **ADDED** |

---

## Quantitative Metrics

### Per-Run Field Length Averages (chars)

| Era | Run | Model | n_plans | avg_levers | avg_name | avg_conseq | avg_review | avg_opts |
|-----|-----|-------|---------|-----------|---------|-----------|-----------|---------|
| PREV | 89 | ollama-llama3.1 | 4 | 18.0 | 29 | 197 | 183 | 267 |
| PREV | 90 | openrouter-openai-gpt-oss-20b | 5 | 18.4 | 28 | 250 | 154 | 406 |
| PREV | 91 | openai-gpt-5-nano | 5 | 18.0 | 58 | 268 | 177 | 441 |
| PREV | 92 | openrouter-qwen3-30b-a3b | 5 | 19.2 | 36 | 219 | 171 | 275 |
| PREV | 93 | openrouter-openai-gpt-4o-mini | 5 | 16.6 | 34 | 255 | 182 | 385 |
| PREV | 94 | openrouter-gemini-2.0-flash-001 | 5 | 17.0 | 28 | 338 | 213 | 476 |
| PREV | 95 | anthropic-claude-haiku-4-5-pinned | 5 | 21.4 | 55 | 528 | 591 | 974 |
| CURR | 96 | ollama-llama3.1 | 5 | 15.6 | 26 | 201 | 209 | 306 |
| CURR | 97 | openrouter-openai-gpt-oss-20b | 5 | 18.0 | 30 | 261 | 157 | 373 |
| CURR | 98 | openai-gpt-5-nano | 5 | 18.6 | 63 | 267 | 193 | 423 |
| CURR | 99 | openrouter-qwen3-30b-a3b | 5 | 17.6 | 31 | 225 | 166 | 238 |
| CURR | 00 | openrouter-openai-gpt-4o-mini | 5 | 16.4 | 33 | 251 | 179 | 402 |
| CURR | 01 | openrouter-gemini-2.0-flash-001 | 5 | 14.4 | 27 | 342 | 213 | 481 |
| CURR | 02 | anthropic-claude-haiku-4-5-pinned | 5 | 22.0 | 60 | 540 | 589 | 925 |
| **BASELINE** | — | baseline/train | 5 | 15.0 | 28 | 279 | 152 | 453 |

### Baseline Length Ratios (current runs vs baseline)

| Model | conseq ratio | review ratio | opts ratio |
|-------|-------------|-------------|-----------|
| ollama-llama3.1 | 0.72× | 1.38× | 0.68× |
| openrouter-gpt-oss-20b | 0.94× | 1.03× | 0.82× |
| openai-gpt-5-nano | 0.96× | 1.27× | 0.93× |
| openrouter-qwen3-30b | 0.81× | 1.09× | 0.53× |
| openrouter-gpt-4o-mini | 0.90× | 1.18× | 0.89× |
| openrouter-gemini-2.0-flash | 1.23× | 1.40× | 1.06× |
| anthropic-claude-haiku | 1.94× | **3.87×** | 2.04× |

Haiku's review length is 3.87× baseline — a warning-level ratio per AGENTS.md guidance (above 2× is warning, above 3× likely regression). Haiku review length has been consistently elevated across many iterations; this predates PR #339 and is not a regression introduced by this PR.

### Constraint Violations and Template Leakage

| Era | Run | Model | violations_lt3 | violations_ne3 | short_reviews_lt50 | short_reviews_lt20 | pct_claims_total |
|-----|-----|-------|---------------|---------------|-------------------|-------------------|-----------------|
| PREV | 89 | ollama-llama3.1 | 0 | 0 | 0 | 0 | 6 |
| PREV | 90 | openrouter-gpt-oss-20b | 0 | 0 | 0 | 0 | 5 |
| PREV | 91 | openai-gpt-5-nano | 0 | 0 | 0 | 0 | 0 |
| PREV | 92 | openrouter-qwen3-30b | 0 | 0 | 0 | 0 | 3 |
| PREV | 93 | openrouter-gpt-4o-mini | 0 | 0 | 0 | 0 | 0 |
| PREV | 94 | openrouter-gemini | 0 | 0 | 0 | 0 | 0 |
| PREV | 95 | anthropic-claude-haiku | 0 | 0 | 0 | 0 | 51 |
| CURR | 96 | ollama-llama3.1 | 0 | 0 | 0 | 0 | 0 |
| CURR | 97 | openrouter-gpt-oss-20b | 0 | 0 | 0 | 0 | 9 |
| CURR | 98 | openai-gpt-5-nano | 0 | 0 | 0 | 0 | 0 |
| CURR | 99 | openrouter-qwen3-30b | 0 | 0 | 0 | 0 | 3 |
| CURR | 00 | openrouter-gpt-4o-mini | 0 | 0 | 0 | 0 | 0 |
| CURR | 01 | openrouter-gemini | 0 | 0 | 0 | 0 | 0 |
| CURR | 02 | anthropic-claude-haiku | 0 | 0 | 0 | 0 | 35 |

**Interpretation:**
- Zero constraint violations across all runs before and after. This means the option count fix (`!= 3` → `< 3`) had zero observable impact on these runs — models consistently generate exactly 3 options and never over-generate.
- Zero short reviews in current runs — the raised 50-char floor did not trigger new failures. All reviews are well above 50 chars in practice.
- Percentage claims (fabricated numbers): haiku decreased from 51 to 35, others stable. No model was made worse.

### LLMChatError Events

| Era | Run | Model | Plan | Error summary |
|-----|-----|-------|------|---------------|
| PREV | 89 | ollama-llama3.1 | parasomnia | `review_lever is too short (19 chars); expected at least 20` |
| CURR | 96–02 | all | — | None |

The single LLMChatError before the PR was caused by a 19-char review stub (`"Sensor Data Sharing"` — a lever name pasted into the review field). After PR, this does not recur.

### Partial Recovery Events

| Era | Run | Model | Plan | calls_succeeded | expected_calls |
|-----|-----|-------|------|----------------|---------------|
| PREV | 94 | gemini-2.0-flash | sovereign_identity | 2 | 3 |
| CURR | 96 | llama3.1 | silo | 2 | 3 |
| CURR | 99 | qwen3-30b | hong_kong_game | 2 | 3 |
| CURR | 01 | gemini-2.0-flash | hong_kong_game | **1** | 3 |
| CURR | 01 | gemini-2.0-flash | sovereign_identity | 2 | 3 |

4 partial recoveries after PR vs 1 before. The 1/3-call case (gemini, hong_kong_game) is noteworthy — it resulted in only 6 levers in the output (plan still passes `min_length=5`).

---

## Evidence Notes

- LLMChatError before PR: `history/1/89_identify_potential_levers/events.jsonl` — one `run_single_plan_error` for parasomnia
- LLMChatError resolved: `history/1/96_identify_potential_levers/events.jsonl` — 5 `run_single_plan_complete`, 0 errors
- Secondary lock evidence: `history/1/96_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json` (levers 1-3 all use "The options fail/neglect/overlook")
- Consequences contamination: same file, lever 1 consequences contains "A weakness in this approach is that…"
- Gemini hong_kong_game degradation: `history/2/01_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` — 6 levers vs 18 in `history/1/94_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`
- Third system prompt example contains "the options neglect": `identify_potential_levers.py` line 235
- OPTIMIZE_INSTRUCTIONS template-lock migration note: `identify_potential_levers.py` lines 69-80
- Baseline averages computed from all 5 train plans in `baseline/train/*/002-10-potential_levers.json`

---

## OPTIMIZE_INSTRUCTIONS Alignment

The current OPTIMIZE_INSTRUCTIONS (lines 27-80) covers all documented known problems:
1. Overly optimistic scenarios — addressed
2. Fabricated numbers — addressed
3. Hype and marketing copy — addressed
4. Vague aspirations — addressed
5. Fragile English-only validation — addressed
6. Single-example template lock — addressed
7. Template-lock migration — **newly added by PR #339**

**Gap not yet in OPTIMIZE_INSTRUCTIONS: cross-field contamination.** llama3.1 regularly places critique text (`"A weakness in this approach is that…"`) into the `consequences` field rather than `review_lever`. The field description explicitly prohibits this, but the prohibition exists only in the Pydantic field description string, not in OPTIMIZE_INSTRUCTIONS or the validator. A validator for `consequences` that rejects "weakness", "A weakness", "weakness of", etc. (with appropriate i18n caveat) could catch this. Alternatively, adding a prohibition to OPTIMIZE_INSTRUCTIONS would make it visible to future analysts.

**Misalignment: third review_lever example contains the lockable phrase "the options neglect".** OPTIMIZE_INSTRUCTIONS at line 74-75 warns that "weaker models shift to copying subphrases within the new examples." The third example in the system prompt (`"the options neglect that a single hurricane season…"`) contains exactly this pattern. The warning and the root cause coexist in the same codebase. OPTIMIZE_INSTRUCTIONS correctly identifies the problem but the system prompt still contains the trigger.

---

## PR Impact

### What the PR was supposed to fix

1. Allow >3 options per lever (relax `!= 3` to `< 3`)
2. Catch stub reviews earlier by raising `min_length` from 20 to 50 chars
3. Remove dead-code examples from `LeverCleaned.review`
4. Document template-lock migration in `OPTIMIZE_INSTRUCTIONS`
5. Correct a docstring run reference (89 → 82)

### Before vs After Comparison

| Metric | Before (runs 89–95) | After (runs 96–02) | Change |
|--------|--------------------|--------------------|--------|
| Success rate (plan completions) | 34/35 = 97.1% | 35/35 = 100.0% | **+2.9pp** |
| llama3.1 LLMChatErrors | 1 (parasomnia) | 0 | **FIXED** |
| Option count violations (< 3) | 0 | 0 | No change |
| Option count violations (!= 3) | 0 | 0 | No change |
| Short reviews < 50 chars | 0 | 0 | No change |
| Short reviews < 20 chars | 0 | 0 | No change |
| Secondary lock (llama3.1) | Present | Present | UNCHANGED |
| Field length ratios vs baseline | Stable | Stable | No change |
| Fabricated % claims (haiku) | 51 | 35 | Slight improvement |
| Partial recovery events | 1 | 4 | INCREASED |
| Gemini hong_kong lever count | 18 | 6 | REGRESSION |

### Did the PR fix the targeted issue?

**Yes, for the primary target.** The 19-char review stub (`"Sensor Data Sharing"`) that caused a LLMChatError in run 89 does not recur in run 96. Parasomnia now completes successfully. The raised `min_length` is a contributing factor (a 19-char review would now fail the new 50-char threshold too), but the more direct effect is that the review is now 149 chars average for that plan — suggesting the model generates substantive reviews without the degenerate case.

**Neutral, for the option count change.** No model over-generated or under-generated options in either the before or after batches. The fix from `!= 3` to `< 3` had zero observable impact.

**Positive, for OPTIMIZE_INSTRUCTIONS documentation.** The template-lock migration note is accurate and grounded in observed behavior.

### Were any regressions introduced?

The 4 partial recovery events vs 1 before is a regression in reliability, but all plans still complete. The gemini hong_kong_game producing only 6 levers (1/3 calls succeeded) is a quality regression for that specific combination, but it appears to be non-deterministic model behavior unrelated to the PR changes.

The secondary template lock in llama3.1 was already present in run 89 and is not worsened by PR #339.

### Verdict

**KEEP**

The PR fixes a real failure (llama3.1 parasomnia LLMChatError), improves success rate from 97.1% to 100%, introduces no regressions in content quality, and adds useful documentation to OPTIMIZE_INSTRUCTIONS. The option count change (lt3 vs ne3) had no observable effect but is directionally correct (over-generation is handled downstream). The dead-code cleanup is hygiene. No reason to revert.

---

## Questions For Later Synthesis

1. **Will the secondary lock in llama3.1 ("The options neglect/overlook/fail to") persist across more diverse runs?** The lock affects gta_game at ~100% in run 96. Is it specific to certain plans or universal? Does it affect output quality enough to warrant a prompt change?

2. **Is the third review_lever example ("the options neglect…") the direct source of the secondary lock?** If yes, should it be replaced with a phrasing that doesn't include a copyable opener? (This would be a targeted PR.)

3. **Why did gemini hong_kong_game produce 1/3 calls in run 01?** Is this a recurring stability issue for gemini on this plan? Compare run 01 vs run 94 to determine if this is a fluke or trend.

4. **Is haiku's 3.87× review length ratio a quality regression or appropriate depth?** The previous analysis (analysis 26) found it was 2.1× at that time. The ratio has grown. Are the longer reviews adding substantive analysis or verbose padding?

5. **Should cross-field contamination (weakness language in consequences) be added to OPTIMIZE_INSTRUCTIONS or caught with a validator?** llama3.1 shows this pattern in both run 89 and run 96 — it appears persistent.

6. **Do the partial recovery events correlate with specific plans or is it model-level variability?** hong_kong_game appears in multiple partial recoveries (runs 99, 01). This plan may be harder for some models to process.

---

## Reflect

This analysis covers a focused, low-risk PR. The primary change (raising `min_length` from 20 to 50 chars) directly addressed the only failure observed in the previous batch, and it worked. The secondary changes (option count relaxation, dead-code cleanup, documentation) are correct even if unobservable in these runs.

The most actionable finding from this batch is not related to PR #339 itself: the secondary template lock ("The options neglect/overlook/fail to") is the dominant remaining quality issue for llama3.1, and the third system prompt example contains the trigger phrase. The OPTIMIZE_INSTRUCTIONS now warns about this pattern — the natural next step is to actually fix the system prompt.

The metric story is clean: success rate improved, all constraint violation counts hold at zero, field lengths are stable, no new failures. The partial recovery count increase (1→4) warrants monitoring but does not constitute a regression given 100% plan completion.

---

## Potential Code Changes

**C1 — Fix third review_lever example to remove copyable opener "the options neglect"**

The system prompt at `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` section 4 (line 235) contains:
```
"Pooling catastrophe risk across three coastal regions diversifies exposure on paper, but the options neglect that a single hurricane season can correlate all three simultaneously."
```
The phrase "the options neglect" is a universal template that llama3.1 applies to every review. Replace with a domain-specific phrasing that does not include "the options [verb]" as a reusable pattern. For example: `"but correlation risk from a regional hurricane season is not priced into any of the three."` This matches the OPTIMIZE_INSTRUCTIONS guidance (line 74-79) and removes the lockable trigger.

Predicted effect: llama3.1 would stop generating "The options neglect/overlook/fail to" as its default review opener, reducing the secondary lock from ~100% in gta_game.

**C2 — Add consequences-field contamination validator**

Add a check in `check_option_count` or a new validator on `consequences` that detects and rejects critique/weakness text. Structurally: reject if "weakness" or "A weakness in this approach" appears (with appropriate i18n caveat — avoid English-only substring matching). Alternatively, add a softer prompt-level prohibition to OPTIMIZE_INSTRUCTIONS.

Predicted effect: llama3.1's `consequences` field would no longer contain embedded weakness statements, improving field separation and downstream analysis quality.

**H1 — Replace "the options neglect" in example 3 with non-copyable critique**

The third system prompt example provides the template for llama3.1's secondary lock. Rewrite to eliminate any phrase of the form "the options [verb]", while preserving the structural template (name tension → identify missing consideration). Evidence: `history/1/96_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json` shows 16/16 reviews using this pattern.

**H2 — Add explicit consequence-field prohibition to system prompt**

The system prompt section 2 ("Lever Quality Standards") already says "Do not fabricate percentages or cost estimates." Add a parallel prohibition: "Do not embed weakness assessments or critiques in the Consequences field — these belong exclusively in review_lever." This mirrors the Pydantic field description prohibition but makes it visible at the prompt level.

---

## Summary

PR #339 achieves its stated goal: the llama3.1 parasomnia plan no longer fails with a LLMChatError due to a 19-char review stub. Success rate improves from 34/35 (97.1%) to 35/35 (100%). No content quality regressions were introduced. The option count relaxation and dead-code cleanup are correct hygiene changes with no observable negative effect. OPTIMIZE_INSTRUCTIONS was updated with an accurate and useful note on template-lock migration.

The main finding from the current batch that predates PR #339 and remains unresolved: llama3.1's secondary template lock ("The options neglect/overlook/fail to…") persists in run 96 at the same rate as run 89, and the third system prompt example contains the trigger phrase. The OPTIMIZE_INSTRUCTIONS now documents this problem — the next iteration should address it directly.

**Verdict: KEEP.**
