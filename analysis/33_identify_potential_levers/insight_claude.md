# Insight Claude

## Scope

Analyzing runs `2/38–2/44` (after PR #349) against `2/03–2/09` (before, from
analysis 28) for the `identify_potential_levers` step.

**PR under evaluation:** PR #349 "Add lever_classification field, fix haiku config, adaptive retry loop"

Four changes in this PR:
1. **lever_classification**: New required `Lever` schema field — `"category — what this lever decides"` format. Placed last in schema.
2. **haiku max_tokens fix**: Changed from 16000 to 8192 (actual API cap).
3. **review_lever minimum relaxed**: Validator minimum reduced from 50 to 10 chars.
4. **Adaptive retry loop**: Replace fixed 3-call loop; keep calling until 15 unique levers are accumulated (max 5 calls).

**Model mapping:**

| Run (before) | Run (after) | Model |
|---|---|---|
| 2/03 | 2/38 | ollama-llama3.1 |
| 2/04 | 2/39 | openrouter-openai-gpt-oss-20b |
| 2/05 | 2/40 | openai-gpt-5-nano |
| 2/06 | 2/41 | openrouter-qwen3-30b-a3b |
| 2/07 | 2/42 | openrouter-openai-gpt-4o-mini |
| 2/08 | 2/43 | openrouter-gemini-2.0-flash-001 |
| 2/09 | 2/44 | anthropic-claude-haiku-4-5-pinned |

---

## Negative Things

1. **qwen3 regression: 5/5 → 2/5 success.** After the PR, qwen3-30b-a3b fails on 3/5 plans (silo, sovereign_identity, hong_kong_game) with `lever_classification: Field required [type=missing]`. The model generates valid lever content including all other fields, but omits `lever_classification` entirely in its first call batch. Because the adaptive retry raises immediately when `len(responses) == 0` (line 338 of `identify_potential_levers.py`), there is no retry — the plan fails completely. Before the PR, qwen3 succeeded on all 5 plans. This is a direct regression caused by adding a required field that qwen3 doesn't reliably generate.
   Evidence: `history/2/41_identify_potential_levers/events.jsonl` — 3 `run_single_plan_error` events; `history/2/41_identify_potential_levers/outputs.jsonl` — shows 2/5 ok, 3 errors with `Field required: lever_classification`.

2. **llama3.1 silo regression: silo now fails (options <3).** Run 38 (llama3.1) fails silo with `options must have at least 3 items, got 2/1/1/1/1`. Before the PR (run 03), llama3.1 succeeded on silo (19 levers, all with 3+ options). The added `lever_classification` field increases output complexity; llama3.1 appears to fill the new field while cutting corners on the `options` list. The adaptive retry does not help because the first call fails validation and `len(responses) == 0` → immediate raise.
   Evidence: `history/2/38_identify_potential_levers/events.jsonl` line 2 — `run_single_plan_error` for silo.

3. **lever_classification template lock in llama3.1.** For the plans that do succeed, llama3.1 copies the system prompt Section 2 examples almost verbatim. The phrase "how to sequence the rollout phases" (from the example "execution — how to sequence the rollout phases") appears 4 times across 16 levers in hong_kong_game run 38, applied to completely unrelated levers ("product — how to sequence the rollout phases", "operations — how to sequence the rollout phases"). Additionally, "governance — who oversees the review process" is applied to a `protagonist_background` lever, and "methodology — which data collection approach to use" is applied to an architectural lever. The Section 2 examples are being copied as templates — the same pattern as the `review_lever` template lock documented in OPTIMIZE_INSTRUCTIONS.
   Evidence: `history/2/38_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` — `lever_classification` values for `protagonist_background`, `hong_kong_as_paranoia_machine`, `protagonist_transformation`, `protagonist_motivation`, `music_and_score`.

4. **Fabricated % claims slightly worsened in haiku.** Comparing before vs after for haiku:
   - silo: 4 → 9 fabricated % patterns
   - parasomnia: 17 → 25 fabricated % patterns
   The new `lever_classification` field may be increasing output length, which correlates with more fabricated quantification. The system prompt explicitly prohibits fabricated statistics (Section 6), but the prohibition is not being honored.
   Evidence: `history/2/44_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json` vs `history/2/09_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json`.

5. **review_lever docstring/code mismatch.** The `check_review_format` validator docstring (lines 152–156, `identify_potential_levers.py`) says "minimum length (at least 50 characters)" but the actual check is `if len(v) < 10`. The PR changed the threshold from 50 to 10 but did not update the docstring.
   Evidence: `identify_potential_levers.py` lines 146–161 — docstring says 50, implementation checks `< 10`.

6. **Net success rate regression: 97.1% → 88.6%.** Four plans across two models now fail that previously succeeded (3 qwen3, 1 llama3.1). One plan that previously failed now succeeds (gpt-oss-20b sovereign_identity), for a net loss of 3 plans.

---

## Positive Things

1. **Adaptive retry improves llama3.1 lever counts for under-generating plans.** Before PR (run 03), llama3.1 produced only 12 levers for sovereign_identity (`calls_succeeded=2`) and 13 for hong_kong (`calls_succeeded=2`). After PR (run 38), both reach 3 calls: sovereign_identity grows from 12 to 18 levers, hong_kong grows from 13 to 16. The adaptive "keep calling until 15 unique" logic works as intended for plans where the first call delivers fewer than 15 levers.
   Evidence: `history/2/03_identify_potential_levers/outputs.jsonl` (calls_succeeded=2 for sovereign_identity, hong_kong) vs `history/2/38_identify_potential_levers/outputs.jsonl` (calls_succeeded=3 for both).

2. **gpt-oss-20b sovereign_identity: previously failing plan now succeeds.** Run 04 (before PR) failed sovereign_identity with `EOF while parsing a list at line 58` (JSON truncation). Run 39 (after PR) succeeds with 18 levers. This could be adaptive retry benefit (re-call after JSON failure) or non-deterministic recovery; either way it is a positive outcome.
   Evidence: `history/2/04_identify_potential_levers/outputs.jsonl` vs `history/2/39_identify_potential_levers/outputs.jsonl`.

3. **lever_classification quality is excellent for strong models.** Haiku (run 44) produces highly specific, domain-grounded classifications: "execution — which filmmaker steers the visual and tonal realization of Hong Kong as paranoia machine", "governance — which financing entities control the budget and creative decisions". Gemini (run 43) produces concise, accurate classifications: "execution — who will direct the film", "governance — how to handle potential problems". These provide genuinely useful categorization for downstream lever selection.
   Evidence: `history/2/44_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` and `history/2/43_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`.

4. **haiku max_tokens fix is preventative.** Before the PR, haiku's max_tokens was set to 16000 (exceeding the actual API cap of 8192). In the 5 test plans, no truncation occurred before or after the fix — haiku succeeded on all 5/5 plans both times. The fix prevents potential truncation failures on larger-context plans outside the test set. Total output tokens per plan (3 calls combined) are 9380–10301, well below a hypothetical 3×8192=24576 cap.
   Evidence: `history/2/44_identify_potential_levers/outputs/20260310_hong_kong_game/activity_overview.json` (output_tokens: 9380, 3 calls).

5. **review_lever minimum relaxation resolves overly strict validation.** The minimum of 50 chars was causing valid short reviews (10–49 chars) to be rejected. The PR reduces this to 10 chars. No evidence of excessively short reviews in the current outputs — all reviewed review fields are substantive.

6. **Field lengths broadly reasonable for most models.** gpt-5-nano, gpt-4o-mini, and gemini maintain field lengths within 1.0–1.5× baseline for most plans, even with the added lever_classification field. The field addition did not cause systematic verbosity inflation in these models.

---

## Comparison

| Metric | Before (runs 03–09) | After (runs 38–44) | Change |
|--------|--------------------|--------------------|--------|
| **Overall success rate** | 34/35 = 97.1% | 31/35 = 88.6% | **-8.5pp REGRESSION** |
| **LLMChatErrors — qwen3** | 0 | 3 (lever_classification missing) | **NEW REGRESSION** |
| **LLMChatErrors — llama3.1** | 0 | 1 (options < 3, silo) | **NEW REGRESSION** |
| **gpt-oss-20b JSON EOF** | 1 (sovereign_identity) | 0 | **IMPROVED** |
| **lever_classification presence** | 0 (field didn't exist) | 100% in all successful runs | **NEW FEATURE** |
| **lever_classification quality (haiku, gemini)** | N/A | High — domain-specific phrases | **NEW POSITIVE** |
| **lever_classification quality (llama3.1)** | N/A | Poor — template-copied phrases | **NEW ISSUE** |
| **Adaptive retry — llama3.1 lever counts** | 12 (sovereign_identity), 13 (hong_kong) | 18, 16 | **IMPROVED** |
| **Haiku fabricated % claims** | 4+8+1+1+17 = 31 across 5 plans | 9+7+1+2+25 = 44 across 5 plans | **SLIGHT REGRESSION** |
| **Template lock "The options [verb]"** | Present (run 03, parasomnia 100%) | Still present (not addressed) | UNCHANGED |
| **review_lever docstring vs code** | Consistent (50 chars) | Stale docstring (says 50, code is 10) | **NEW DOC BUG** |

---

## Quantitative Metrics

### Success Rate by Model

| Model | Run (before) | Before | Run (after) | After | Delta |
|-------|-------------|--------|-------------|-------|-------|
| ollama-llama3.1 | 03 | 5/5 | 38 | 4/5 | -1 |
| openrouter-openai-gpt-oss-20b | 04 | 4/5 | 39 | 5/5 | +1 |
| openai-gpt-5-nano | 05 | 5/5 | 40 | 5/5 | 0 |
| openrouter-qwen3-30b-a3b | 06 | 5/5 | 41 | 2/5 | **-3** |
| openrouter-openai-gpt-4o-mini | 07 | 5/5 | 42 | 5/5 | 0 |
| openrouter-gemini-2.0-flash-001 | 08 | 5/5 | 43 | 5/5 | 0 |
| anthropic-claude-haiku-4-5-pinned | 09 | 5/5 | 44 | 5/5 | 0 |
| **Total** | | **34/35 = 97.1%** | | **31/35 = 88.6%** | **-8.5pp** |

### Lever Counts (adaptive retry benefit)

| Plan | Baseline | llama3.1 before (run 03) | calls | llama3.1 after (run 38) | calls | Change |
|------|---------|--------------------------|-------|-------------------------|-------|--------|
| silo | 15 | 19 | 3 | FAILED | — | — |
| gta_game | 15 | 16 | 3 | 18 | 3 | +2 |
| sovereign_identity | 15 | 12 | **2** | 18 | 3 | +6 |
| hong_kong_game | 15 | 13 | **2** | 16 | 3 | +3 |
| parasomnia | 15 | 18 | 3 | 19 | 3 | +1 |

The adaptive retry demonstrably helps: sovereign_identity and hong_kong went from 2-call (12–13 levers, below target) to 3-call (16–18 levers, at or above target). The benefit is real but partially offset by the new silo failure.

### Field Length vs Baseline (hong_kong_game)

| Model | Field | Baseline avg | Before avg | Before ratio | After avg | After ratio |
|-------|-------|-------------|-----------|-------------|----------|-------------|
| haiku | consequences | 269 | 664 | 2.5× | 556 | **2.1×** |
| haiku | options_total | 485 | 972 | 2.0× | 828 | 1.7× |
| haiku | review | 153 | 630 | **4.1×** | 459 | **3.0×** |
| gemini | consequences | 269 | 294 | 1.1× | 368 | 1.4× |
| gemini | review | 153 | 199 | 1.3× | 227 | 1.5× |
| gpt-5-nano | consequences | 269 | 202 | 0.8× | 247 | 0.9× |
| gpt-5-nano | review | 153 | 186 | 1.2× | 178 | 1.2× |
| llama3.1 | consequences | 269 | 170 | 0.6× | 191 | 0.7× |
| llama3.1 | review | 153 | 224 | 1.5× | 202 | 1.3× |

Haiku's `review` field is persistently 3–4× baseline, a known warning sign for verbosity-over-substance. This predates the PR and is not PR-specific. Gemini and gpt-5-nano are within acceptable range. llama3.1 is actually SHORT on consequences (0.6–0.7×), suggesting it is under-explaining trade-offs.

### lever_classification Template Lock (llama3.1, hong_kong_game, run 38)

| Count | Phrase | Levers using it |
|-------|--------|----------------|
| 4 | "how to sequence the rollout phases" | protagonist_transformation, protagonist_motivation, hong_kong_supporting_cast, music_and_score |
| 2 | "which data collection approach to use" | hong_kong_as_paranoia_machine, hong_kong_as_character |
| 1 | "who oversees the review process" | protagonist_background (wrong category) |

The system prompt Section 2 examples ("execution — how to sequence the rollout phases", "methodology — which data collection approach to use") are being copied verbatim, then applied regardless of actual lever content. 7/16 levers in hong_kong carry stale/wrong classifications.

Evidence: `history/2/38_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`.

### Fabricated % Claims (haiku)

| Plan | Before (run 09) | After (run 44) | Delta |
|------|-----------------|----------------|-------|
| silo | 4 | 9 | +5 |
| gta_game | 8 | 7 | -1 |
| sovereign_identity | 1 | 1 | 0 |
| hong_kong_game | 1 | 2 | +1 |
| parasomnia | 17 | 25 | +8 |
| **Total** | **31** | **44** | **+13** |

The PR slightly worsened fabricated % claims for haiku. This is likely not directly caused by the PR changes but may reflect natural variation. It remains a known issue from prior analyses.

---

## Evidence Notes

- qwen3 failure pattern: error always on `Attempt 0`, all 6 levers in first batch missing `lever_classification`. Plans that succeed (gta_game, parasomnia) show qwen3 does generate the field when it does — the issue is inconsistent compliance, not universal ignorance. (`history/2/41_identify_potential_levers/events.jsonl`)
- Adaptive retry loop logic (`identify_potential_levers.py` lines 286–352): when `call_index == 1` and the call fails, `len(responses) == 0` → `raise llm_error` immediately. The loop never reaches `call_index == 2` for a schema validation failure on the first call. The adaptive retry only benefits models whose first call succeeds but yields fewer than 15 levers.
- haiku activity_overview for parasomnia after PR shows `output_tokens: 10301` across 3 calls — no signs of truncation at 8192 per call.
- gpt-oss-20b before-PR failure (`history/2/04_identify_potential_levers/outputs.jsonl`): `"Invalid JSON: EOF while parsing a list at line 58"` — truncation caused by long response, not schema validation.

---

## OPTIMIZE_INSTRUCTIONS Alignment

The current `OPTIMIZE_INSTRUCTIONS` (lines 27–80) does not yet document:

1. **New required field schema failures.** When a required field is added to `Lever` without adequate examples in the system prompt that demonstrate the field for all plan types, weaker models may omit the field in their first call, causing the entire batch to fail validation and triggering an immediate raise (not a retry). This is structurally equivalent to the `max_length` constraint issue documented in AGENTS.md §Pydantic hard constraints vs soft prompt guidance — a hard required constraint discards otherwise-valid levers.

2. **Classification example template lock.** The `lever_classification` system prompt examples ("governance — who oversees the review process", "methodology — which data collection approach to use", "execution — how to sequence the rollout phases") are being copied by llama3.1 across unrelated levers. This is the same pattern as the `review_lever` template lock. The OPTIMIZE_INSTRUCTIONS note on single-example template lock (lines 69–72) should be extended to cover new fields with example-driven format constraints.

3. **Adaptive retry first-call failure gap.** The adaptive retry description in `OPTIMIZE_INSTRUCTIONS` says it fixes cases where "validation failures discard entire batches." This is accurate for later calls (where prior successes exist in `responses`), but the code raises immediately if the first call fails. Any model that consistently fails schema validation on its first call will never benefit from the retry logic.

**Note on OPTIMIZE_INSTRUCTIONS integrity:** The existing entries (fabricated numbers, hype language, vague aspirations, fragile English-only validation, template lock) remain accurate. The agriculture example ("none of the options price in the idle-wage burden") is still cited as the correct structural template.

---

## PR Impact

### What the PR was supposed to fix

1. Add `lever_classification` — a useful categorization field placed last in schema so sequential models (llama3.1) fill important fields first.
2. Fix haiku `max_tokens` (16000 → 8192) to prevent JSON truncation on large plans.
3. Relax `review_lever` minimum from 50 to 10 chars.
4. Replace fixed 3-call loop with adaptive retry: call until 15 unique levers are accumulated, max 5 calls.

### Before vs After Comparison

| Metric | Before (runs 03–09) | After (runs 38–44) | Change |
|--------|--------------------|--------------------|--------|
| Success rate | 34/35 = 97.1% | 31/35 = 88.6% | **-8.5pp** |
| qwen3 failures | 0 | 3 (lever_classification missing) | **-3 plans** |
| llama3.1 failures | 0 | 1 (options < 3, silo) | **-1 plan** |
| gpt-oss-20b failures | 1 (JSON EOF) | 0 | **+1 plan** |
| llama3.1 lever count — sovereign_identity | 12 (2 calls) | 18 (3 calls) | **+6 levers** |
| llama3.1 lever count — hong_kong | 13 (2 calls) | 16 (3 calls) | **+3 levers** |
| lever_classification present | 0 (field absent) | 100% in successful runs | **New field** |
| haiku truncation errors | 0 | 0 | No observable change |
| Fabricated % claims (haiku) | ~31 | ~44 | Slight regression |

### Did the PR fix the targeted issues?

**Adaptive retry (C4 in PR):** YES — partially. Clearly improves llama3.1's lever count for plans that needed a 3rd call (sovereign_identity: +6, hong_kong: +3). Does NOT help models whose first call fails schema validation (qwen3, llama3.1/silo), because the retry exits on first-call failure.

**lever_classification field:** YES for strong models (haiku, gemini, gpt-5-nano, gpt-4o-mini), whose classifications are high-quality and present. NO for qwen3 (3/5 plans fail because the field is required but not generated). PARTIAL for llama3.1 (field is generated but with template-lock copies of the system prompt examples).

**haiku max_tokens fix:** UNOBSERVABLE in test data (no truncation before or after). The fix is correctness-oriented and valid, but no test plan was large enough to trigger the old limit.

**review_lever minimum relaxation:** Non-observable in success metrics. Valid and low-risk change. No evidence of excessively short reviews passing through.

### Check for regressions

The PR introduced two significant regressions:
1. **qwen3: 5/5 → 2/5.** Adding `lever_classification` as a required field causes qwen3 to fail 3 out of 5 plans. This is a direct schema-mismatch regression.
2. **llama3.1/silo: 5/5 → 4/5.** The added output complexity causes llama3.1 to under-generate options for the silo plan.

### Verdict

**CONDITIONAL**

The adaptive retry and haiku max_tokens fix are clean improvements worth keeping. The `lever_classification` field adds genuine value for capable models (haiku, gemini). However, the PR causes a net regression in success rate (97.1% → 88.6%) by adding a required field that qwen3 doesn't reliably generate. The field should be changed to `Optional[str] = None` or a prompt change should ensure qwen3 reliably generates it before making it required. Additionally, the lever_classification system prompt examples create a new template-lock vector for llama3.1 that parallels the existing `review_lever` lock issue. These issues must be addressed before considering the feature complete.

---

## Questions For Later Synthesis

1. Is qwen3's `lever_classification` failure consistent across ALL first-call batches for these 3 plans, or does it sometimes generate the field and sometimes not? (Would a retry on failed first-call batches — rather than immediate raise — recover qwen3 for these plans?)

2. The system prompt Section 2 examples for `lever_classification` use reusable phrases like "how to sequence the rollout phases". Should the examples be plan-specific (like the agriculture example for `review_lever`) to prevent template lock for llama3.1?

3. Is the llama3.1/silo `options < 3` failure a new issue introduced by the PR (more complex output schema causing llama3.1 to cut corners) or a pre-existing intermittent problem? A re-run of llama3.1 on silo before the PR should clarify.

4. The `review` field in haiku is 3–4× longer than baseline. Is this causing downstream quality problems in scenario generation, or does the enrich step truncate/ignore excess? What is the ideal length target for `review_lever`?

5. Can the adaptive retry loop be modified to retry on schema validation failures from the first call, rather than immediately raising? This would give qwen3 a second chance to generate `lever_classification` when the first batch omits it.

---

## Reflect

The PR made three distinct changes with different risk profiles:
- Adaptive retry: clean, verifiable benefit (more levers for under-generating models), low risk.
- haiku max_tokens fix: preventative, correct, zero observable impact in test data.
- review_lever minimum relaxation: small, valid, non-controversial.
- lever_classification: the riskiest change — adds a required field to the schema. Required fields break models that don't generate them, and the field's system prompt examples create a new template-lock source for weaker models.

The core tension: `lever_classification` is genuinely useful for capable models (haiku, gemini) but is a regression risk for weaker/non-instruction-following models (qwen3, llama3.1). Making a new field `Optional` initially, then making it required after validating compliance across all models, would have avoided the qwen3 failure.

The adaptive retry's first-call-failure limitation is a design gap: the retry logic only helps when ≥1 call has succeeded. The most common real-world failure (first call fails validation) is not handled by the current retry design.

---

## Potential Code Changes

**C1 — Make `lever_classification` Optional during rollout (or add retry on first-call failure).**
*Motivation:* 3/5 qwen3 plans fail because `lever_classification` is required but qwen3 omits it. The retry logic (`identify_potential_levers.py` line 338) raises immediately on first-call failure. Either: (a) change `lever_classification: str` to `lever_classification: Optional[str] = None` so missing values don't fail validation, then add a post-hoc check; or (b) modify the retry loop to continue instead of raising when `call_index == 1` and the error is a schema validation failure.
*Evidence:* `history/2/41_identify_potential_levers/events.jsonl` — 3 plan failures. `identify_potential_levers.py` lines 338–339.
*Expected effect:* qwen3 success rate returns to 5/5.

**C2 — Fix `check_review_format` docstring to match implementation.**
*Motivation:* The docstring says "minimum length (at least 50 characters)" but the check is `< 10`. Any developer reading the docstring will have incorrect expectations.
*Evidence:* `identify_potential_levers.py` lines 152–161.
*Expected effect:* Documentation accuracy only; no behavioral change.

**C3 — Add plan-specific (non-portable) examples for `lever_classification` in system prompt Section 2.**
*Motivation:* The current examples ("governance — who oversees the review process", "execution — how to sequence the rollout phases") are generic and reusable, exactly the pattern that caused the `review_lever` template lock. llama3.1 copies "how to sequence the rollout phases" 4 times in hong_kong_game levers. Replace with domain-anchored examples (different domains per example) so the format is clear but the phrases are non-portable.
*Evidence:* `history/2/38_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` — 7/16 levers carry template-copied classification phrases.
*Expected effect:* Reduced template lock for llama3.1 lever_classification.

**C4 — Document new required-field failure pattern in OPTIMIZE_INSTRUCTIONS.**
*Motivation:* The PR introduced a new class of failure (required field omitted by weaker model, causing entire batch to fail) not yet documented in OPTIMIZE_INSTRUCTIONS. Future analysis agents and developers need this warning.
*Evidence:* This analysis; `identify_potential_levers.py` lines 338–339.
*Expected effect:* Future PRs adding required fields will be aware of the risk.

---

## Summary

PR #349 introduced four changes with mixed results. The adaptive retry loop is a genuine improvement for llama3.1 on under-generating plans (sovereign_identity: 12→18 levers, hong_kong: 13→16). The haiku max_tokens fix is a valid correctness improvement with no observable test-set impact. The review_lever minimum relaxation is clean and low-risk.

However, the addition of `lever_classification` as a required field caused a net regression: success rate dropped from 97.1% to 88.6% (34→31/35). qwen3 fails on 3/5 plans because it doesn't generate the new field in its first call, and the adaptive retry's immediate-raise-on-first-failure design offers no recovery. llama3.1 fails on one additional plan (silo). Additionally, llama3.1's successful plans show a new template-lock pattern where the system prompt Section 2 classification examples are being copied verbatim across unrelated levers.

The `lever_classification` field content is high-quality for capable models (haiku, gemini) and represents a useful addition to the schema once the compliance issue is resolved. The recommended path is: (a) make the field `Optional` or add retry-on-first-call-failure to recover qwen3; (b) replace the Section 2 generic examples with domain-anchored non-portable examples to prevent llama3.1 template lock; (c) fix the `check_review_format` docstring.

**Verdict: CONDITIONAL.** Keep the adaptive retry, haiku fix, and review_lever minimum change unconditionally. The `lever_classification` field is worth keeping but needs the field-optional or retry fix before it can be considered production-ready across all models.
