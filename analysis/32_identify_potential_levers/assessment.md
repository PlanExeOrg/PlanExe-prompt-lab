# Assessment: Add lever_type and decision_axis to lever schema

**PR**: #346
**Before analysis**: `analysis/31_identify_potential_levers/` — runs 2/24–2/30 (PR branch, WITH lever_type + decision_axis)
**After analysis**: `analysis/32_identify_potential_levers/` — runs 2/31–2/37 (main branch, WITHOUT PR, lever_classification only)

---

## Issue Resolution

**What the PR was supposed to fix**: PR #346 adds two new structured fields to the lever schema:
1. `lever_type` — enum of 6 values (methodology / execution / governance / dissemination / product / operations) for machine-queryable classification
2. `decision_axis` — a single sentence "This lever controls X by choosing between A, B, and C" that forces explicit decision framing

Both fields propagate through `Lever → LeverCleaned → JSON` output. A new system prompt section 2 ("Lever Classification") guides the LLM. Validators enforce enum membership (`lever_type`) and minimum length of 20 chars (`decision_axis`).

**Is the issue resolved?** Partially. In runs where validation passes, the fields are correctly populated:
- `lever_type`: 97% valid across 5 of 7 models (only llama3.1 produced an invalid type in one plan)
- `decision_axis`: 97% conformant to "This lever controls X by choosing between A, B, C" format across all successful runs
- Content is informative and actionable (e.g., "This lever controls the film's tone and authenticity by choosing between a Hong Kong auteur, an Asian genre specialist, or an international director.")

**Residual symptoms**: Three direct regressions remain unresolved:
1. Haiku JSON truncation — 2 plans (gta_game at EOF col 29,300; silo at EOF col 43,016) failed due to the new fields pushing responses over haiku's ~8,192-token API ceiling. Confirmed via `history/2/30_identify_potential_levers/events.jsonl`.
2. llama3.1 lever_type rejection — `sovereign_identity` failed with `lever_type='coalition_building'`, a semantically valid but non-enumerated string. Confirmed via `history/2/24_identify_potential_levers/events.jsonl`.
3. Lever count regression (35–67%) — the batch-rejection architecture discards entire 5–7 lever batches when any single lever fails validation. For gemini, 2 of 3 LLM calls were dropped on hong_kong_game, leaving only 6 levers vs 18 without the PR. Confirmed by reading `002-10-potential_levers.json` directly: run 29 (gemini, with PR) = 6 levers; run 36 (gemini, without PR) = 18 levers.

---

## Quality Comparison

**Key**: Before = runs 24–30 WITH PR applied; After = runs 31–37 on main branch WITHOUT PR.

| Metric | Before (with PR, runs 24–30) | After (without PR, runs 31–37) | Verdict |
|--------|------------------------------|-------------------------------|---------|
| **Success rate** | 30/35 = 85.7% | 33/35 = 94.3% | IMPROVED |
| **Haiku success rate** | 3/5 = 60% (2 JSON-EOF failures) | 5/5 = 100% | IMPROVED |
| **llama3.1 success rate** | 2/5 = 40% (lever_type + pre-existing) | 3/5 = 60% (pre-existing only) | IMPROVED |
| **lever_type field** | Present, valid in 97% of levers | Absent (lever_classification used) | REGRESSED* |
| **decision_axis field** | Present, 97% conformant | Absent | REGRESSED* |
| **lever_classification field** | Absent | Present (~55 chars, combined format) | N/A |
| **Gemini lever count (hong_kong_game)** | 6 (runs 24–30 avg) | 18 (run 36) | IMPROVED |
| **gpt-4o-mini lever count (hong_kong_game)** | 11 (run 28) | 17 (run 35) | IMPROVED |
| **Haiku lever count (silo, run 37)** | 22–25 (run 30 surviving plans) | 21 (run 37) | UNCHANGED |
| **Bracket placeholder leakage** | 0 in all runs | 0 in all runs | UNCHANGED |
| **Option count violations** | 0 for non-llama models; pre-existing llama failures | 0 for non-llama models; pre-existing llama failures | UNCHANGED |
| **Lever name uniqueness** | High across all runs | High across all runs | UNCHANGED |
| **Template leakage (review "The options [verb]")** | 47–100% by model | 50–100% by model | UNCHANGED |
| **Review format compliance ("Controls X vs Y")** | Low (replaced by non-formulaic reviews) | Low (same non-formulaic pattern) | UNCHANGED |
| **Consequence chain format (Immediate → Systemic → Strategic)** | Present in 80–90% of consequences | Present in 80–90% of consequences | UNCHANGED |
| **Content depth (avg options length)** | Non-haiku: 280–534 chars; haiku: 944 chars | Non-haiku: ~280–534 chars | UNCHANGED |
| **Field length vs baseline (consequences)** | Non-haiku: 1.13×; haiku: 2.44× (warning) | ~1.2–1.4× baseline | UNCHANGED |
| **Field length vs baseline (review)** | Non-haiku: 1.15×; haiku: 3.71× (above 3× threshold) | ~2.5–3× baseline | UNCHANGED |
| **Cross-call duplication** | Low (seen_names dedup active) | Low (seen_names dedup active) | UNCHANGED |
| **Over-generation count** | 17–25 levers/plan for capable models | 17–21 levers/plan for capable models | UNCHANGED |
| **Fabricated quantification** | 0 for 5/7 models; haiku: 7/70 (10%); gpt-oss-20b: 3 | 0 across all models | IMPROVED |
| **Marketing-copy language** | gpt-4o-mini: 7 instances; others low | Near-zero across all models | IMPROVED |

\* Regression in field richness: the PR's lever_type + decision_axis provide more downstream value than lever_classification, but the regressions make the PR unmergeable as-is.

**OPTIMIZE_INSTRUCTIONS check**: The PR contradicts the documented principle "over-generation is fine; step 2 handles extras." The batch-rejection architecture causes under-generation (35–67% lever count reduction), the opposite of the intended behavior. The new `decision_axis` template is English-only ("This lever controls X by choosing between A, B, and C"), which OPTIMIZE_INSTRUCTIONS explicitly warns against. Neither finding is addressed in the PR.

---

## New Issues

**New issues introduced by the PR (runs 24–30):**

1. **Batch-rejection architecture is exposed as a fragility**: The PR added two new hard validators (`lever_type` enum, `decision_axis` min 20 chars). Each new constraint multiplicatively increases the probability of batch rejection. For gemini on hong_kong_game, 2 of 3 calls were silently discarded, leaving only 6 levers. This is the dominant regression (−35% to −67% lever count) and contradicts OPTIMIZE_INSTRUCTIONS. The underlying architecture (any single failing lever causes the entire DocumentDetails to fail) was pre-existing but benign with fewer constraints.

2. **haiku JSON truncation on large plans**: PR #346 added ~300–400 chars per lever (lever_type + decision_axis). With 3 calls × 7–9 levers each, haiku's per-plan output grew ~6,000–8,000 chars. The `anthropic_claude.json` sets `max_tokens: 16000`, but haiku's actual API ceiling is ~8,192 tokens. Two plans (gta_game, silo) exceeded this ceiling, producing truncated JSON that failed parsing. This risk was not documented and no pre-call size guard exists.

3. **lever_type enum rejection with no recovery**: The `normalize_lever_type` validator does `strip().lower()` then immediately hard-rejects unrecognized strings. `IdentifyPotentialLevers.execute()` sets `max_validation_retries=0` (the default), so there is no retry opportunity. One plan failure resulted (llama3.1, `sovereign_identity`). The `LLMExecutor` infrastructure supports retries — they are just not enabled at the call site.

**Latent issue surfaced by the PR:**

4. **review_lever docstring/implementation mismatch (B1 in analysis 32)**: The current main-branch code (runs 31–37) has `check_review_format` with docstring "at least 50 characters" but code `if len(v) < 10`. This pre-existing mismatch is now clearly documented and needs a one-line fix. Run 24's silo failure ("review_lever is too short, expected at least 50") used the PR's 50-char enforcement and correctly caught 7 empty review fields from llama3.1 — demonstrating that the stricter threshold does catch real quality issues.

**No change in:**
- Template lock in review fields ("The tension between X and Y is unresolved. None of the options...") — persists at moderate-severe across all runs, both batches
- llama3.1 options < 3 failures — pre-existing, same failure mode in both batches

---

## Verdict

**CONDITIONAL**: The schema design is sound and delivers genuine downstream value — typed `lever_type` enables categorization queries, and `decision_axis` makes controllable choices explicit — but two engineering gaps prevent merging as-is.

**The two blockers are:**

1. **Batch-rejection causes 35–67% lever count reduction** (dominant regression). Every new hard Pydantic constraint on `Lever` multiplies batch-failure probability. The fix is to convert the `lever_type` and `decision_axis` validators from hard `ValueError` raises to soft normalization-and-log. A short or slightly-wrong `lever_type` is vastly preferable to losing 5–7 valid levers from the same call. Evidence: run 29 (gemini, with PR) = 6 levers vs run 36 (gemini, without PR) = 18 levers on hong_kong_game.

2. **haiku max_tokens misconfiguration** causes JSON truncation on large plans. The config value 16000 exceeds haiku's real API cap of ~8,192 tokens. PR #346's additional per-lever payload pushed two plans over the ceiling. Fix: document the discrepancy in `anthropic_claude.json` and reduce per-call lever count for verbose models, or add a prompt-level cap ("Propose exactly 5 levers" instead of "5 to 7").

Once both blockers are fixed and lever counts for gemini and gpt-4o-mini recover to 15+ on hong_kong_game, the PR should be merged.

---

## Recommended Next Change

**Proposal**: Soften the PR's hard Pydantic validators to per-lever normalization-and-log instead of batch-killing ValueError raises. Specifically: (a) add a `mode='before'` `lever_type` validator that maps common synonyms to valid enum values before the enum check, and only raises if the value is truly unmappable; (b) convert the `decision_axis` minimum-length validator from a hard reject to a logged warning, accepting short values rather than discarding the entire batch.

**Evidence**: Highly convincing. Both agents in analysis 32 independently identify the batch-rejection architecture (`identify_potential_levers.py:329`, the `except Exception` that discards a full call on any single lever validation failure) as the root cause. The lever count data is direct and verifiable: run 29 (gemini, with PR) = 6 levers; run 36 (gemini, no PR) = 18 levers on the same plan. The difference (−67%) is too large to be stochastic. Analysis 32 synthesis provides concrete code for both fixes (alias dict + `mode='before'` validator for lever_type; log-and-continue for decision_axis).

Additionally: fix the `anthropic_claude.json` `max_tokens: 16000` documentation (add a comment explaining the haiku API cap is ~8,192 tokens) and reduce per-call lever guidance from "5 to 7" to "5" to reduce payload size for verbose models.

**Verify in the next iteration**:
- Gemini (run ~38 equivalent) on hong_kong_game: lever count should recover to 15+ (was 6 with PR, 18 without). If still below 12, the synonym aliases are insufficient and the validator is still causing batch rejection.
- gpt-4o-mini on hong_kong_game: lever count should recover to 15+ (was 11 with PR, 17 without).
- llama3.1 on sovereign_identity: should no longer fail on lever_type='coalition_building'. Check events.jsonl for any remaining `lever_type must be one of` errors.
- haiku on gta_game and silo: should no longer produce JSON-EOF truncation errors. Verify `run_single_plan_complete` (not `run_single_plan_error`) for both plans.
- Check all models for lever_type distribution — confirm no single type exceeds 35% of total levers per model.
- Confirm decision_axis field is still present and the "This lever controls X by choosing between" format still achieved in 90%+ of levers after softening the validator.

**Risks**:
- Softening `lever_type` validator may allow low-quality or incorrect classifications into the output. Mitigate by logging every normalization so analysts can audit the alias table coverage. If the alias table is too aggressive (over-mapping), spurious classifications could pollute downstream filtering.
- Softening `decision_axis` validator may allow very short or degenerate values (e.g., a single word). The 20-char soft threshold should still generate a warning log entry so stochastic model failures are visible in events.jsonl.
- Reducing levers per call from "5–7" to "5" may slightly reduce diversity for non-haiku models that are well within token limits. For those models, 5 levers per call × 3 calls = 15 before deduplication, which is still sufficient. Watch for models that previously generated 18–21 levers dropping to 13–15.
- The template lock problem (review field "The tension between X and Y") is not addressed by this PR. It remains at moderate-severe for 5 of 7 models and should be the next prompt change after the validator fixes are confirmed working.

**Prerequisite issues**: None. The validator softening is self-contained and does not depend on any other fix. The max_tokens documentation fix is independent. Both can be done in the same PR.

---

## Backlog

**Resolved and removable:**
- Analysis 31 item "haiku max_tokens B2: 16000 configured but real cap is ~8192" — diagnosed and root-caused. Fix is to document the discrepancy; the actual resolution comes from reducing payload size, not from changing the config number. Remains in backlog as a documentation task.

**New items from this assessment:**

1. **Batch-rejection architecture** (high priority): Any new hard Pydantic constraint on `Lever` silently discards entire 5–7 lever batches. The current `except Exception` at `identify_potential_levers.py:329` provides no per-lever fallback. Long-term fix requires either per-lever validation (not DocumentDetails-level) or a pre-validation filtering pass. Short-term fix: soften validators to warnings instead of raises.

2. **review_lever docstring/code mismatch B1** (medium priority): `check_review_format` at `identify_potential_levers.py:157` checks `< 10` but docstring says "at least 50". One-line fix: `if len(v) < 50:`. All observed reviews are above 50 chars; no runs would be newly broken. Run 24 (llama3.1, silo) demonstrated the 50-char threshold correctly catches quality failures — the current 10-char threshold is too permissive.

3. **Template lock in review fields** (high priority, prompt fix): "The tension between X and Y is unresolved. None of the options [explicitly/fully] [verb]..." pattern appears in 50–100% of reviews across 5 of 7 models. All three review examples in system prompt section 5 end with "none of the options [verb]" phrasing. Fix: replace examples with three structurally distinct critique styles (excluded stakeholder, compounding cost, prerequisite condition) with no shared sentence-ending template. Add anti-template instruction: "Do not begin every review with 'The tension between'. Name a concrete, domain-specific failure the options share."

4. **options field description vs validator mismatch B2** (low priority): Field description says "Exactly 3 options. No more, no fewer." but validator only enforces `len >= 3`. Fix: change to "At least 3 options; extras are fine and will be trimmed downstream." Aligns with OPTIMIZE_INSTRUCTIONS.

5. **Plan timeout not enforced B3** (medium priority): `runner.py:491–503` — `with _TPE()` exits after `TimeoutError` by calling `shutdown(wait=True)`, blocking until the inner thread completes. Hung llama3.1 calls block the runner indefinitely. Fix: `executor.shutdown(wait=False, cancel_futures=True)` after catching `TimeoutError`.

6. **English-only decision_axis template** (low priority): System prompt section 2 specifies "This lever controls X by choosing between A, B, and C" — an English-only format. For non-English plan prompts, models may produce valid decision_axis entries in the source language that pass the 20-char validator but break downstream "by choosing between" parsers. Document as an English-only field or make the minimum-length check language-agnostic.

7. **OPTIMIZE_INSTRUCTIONS update needed**: Add a warning that (a) any new hard Pydantic constraint on the `Lever` model increases batch-rejection probability and may cause severe lever count regression; (b) adding new fields to per-lever output increases response size and can push verbose models (especially haiku) past their effective API output ceiling. These risks should be checked for every schema-extension PR.
