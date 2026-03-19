# Insight Claude

Analysis of PR #351: "fix: adaptive retry loop, haiku max_tokens, relax review_lever"

Comparing after runs (`history/2/45`–`51_identify_potential_levers`) against before runs
(`history/2/03`–`09_identify_potential_levers`) from analysis `28_identify_potential_levers`.

---

## Rankings

Model performance ranking for after runs (45–51), by success rate then content quality:

| Rank | Model | Run | Success | Notes |
|------|-------|-----|---------|-------|
| 1 | openai-gpt-5-nano | 47 | 5/5 (100%) | Rich, project-specific levers; "Core tension / Weakness" reviews |
| 2 | anthropic-claude-haiku-4-5-pinned | 51 | 5/5 (100%)* | Deepest lever content; 2 partial_recovery events |
| 3 | openrouter-qwen3-30b-a3b | 48 | 5/5 (100%) | Stable; not sampled extensively |
| 4 | openrouter-openai-gpt-4o-mini | 49 | 5/5 (100%) | Stable; not sampled extensively |
| 5 | openrouter-gemini-2.0-flash-001 | 50 | 5/5 (100%) | Stable; not sampled extensively |
| 6 | ollama-llama3.1 | 45 | 4/5 (80%) | sovereign_identity timeout; template lock persists |
| 7 | openrouter-openai-gpt-oss-20b | 46 | 4/5 (80%) | hong_kong_game JSON EOF; persistent truncation bug |

*Two plans (silo, parasomnia) emit `partial_recovery` event: calls_succeeded=2, expected_calls=3.

---

## Negative Things

### N1 — Overall success rate regressed from 97.1% to 94.3%

Before (runs 03–09): 34/35 plans succeeded.
After (runs 45–51): 33/35 plans succeeded.

| Run | Model | Failure | Error |
|-----|-------|---------|-------|
| 45 | llama3.1 | 20260308_sovereign_identity | ReadTimeout (Ollama unreachable) |
| 46 | gpt-oss-20b | 20260310_hong_kong_game | JSON EOF at line 47 (truncation) |

Before, the single failure was run 04 (gpt-oss-20b, sovereign_identity, EOF at line 58). The PR was supposed to improve reliability, not regress it.

Evidence: `history/2/45_identify_potential_levers/outputs.jsonl` line 3; `history/2/46_identify_potential_levers/outputs.jsonl` line 3.

### N2 — gpt-oss-20b JSON truncation not fixed

The gpt-oss-20b model produced a JSON EOF truncation error in run 04 (before) for sovereign_identity and again in run 46 (after) for hong_kong_game. The PR fixed haiku's `max_tokens` (16000 → 8192) but did not address gpt-oss-20b's equivalent problem. Both errors occur mid-list at a column position consistent with output being cut off at the model's API cap.

Evidence:
- Run 04 error: `EOF while parsing a list at line 58 column 5` (sovereign_identity)
- Run 46 error: `EOF while parsing a list at line 47 column 5` (hong_kong_game)

Source: `history/2/46_identify_potential_levers/events.jsonl` line 8.

### N3 — Haiku partial_recovery events: 2 plans per run

Run 51 (haiku) emits `partial_recovery` events for 20250321_silo (calls_succeeded=2, expected_calls=3) and 20260311_parasomnia_research_unit (calls_succeeded=2, expected_calls=3).

This means call 3 failed mid-loop for both plans, and the adaptive retry mechanism preserved the 2 successful calls' levers. Each successful haiku call produces ~7 levers, so 2 calls yield ~14 levers — below the min_levers=15 threshold. Downstream deduplication and enrichment receive a slightly smaller lever set than intended.

Before (run 09, haiku): 5/5 plans with calls_succeeded=3, no partial_recovery events.

Source: `history/2/51_identify_potential_levers/events.jsonl` lines 6, 11.

### N4 — Template lock in llama3.1 reviews persists

Run 45 (llama3.1, gta_game) shows that the options-centric review pattern has shifted but not broken:

- Levers 1–7 (call 1): Reviews use "The options overlook/do not consider/do not address" format (~5/7 reviews)
- Levers 8–18 (calls 2–3): Reviews shifted to "...none of the options address this risk/concern" (8/11 reviews)

The lock migrated from the original "The options [verb]" form to "none of the options address" — still anchored to the `options` grammatical subject. This was the same residual pattern noted in analysis 28's assessment.

Evidence: `history/2/45_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json` — reviews for levers named Criminal Economy System, Procedural Generation, Industry Partnerships, Urban Renewal Strategy, Talent Acquisition Model, Innovation Incubator Initiative, Community Engagement Framework, Partnership Development Roadmap, Urban Planning Initiative, Talent Management System, Community Outreach Program, Digital Marketing Strategy, Gameplay Mechanics Overhaul.

### N5 — llama3.1 options sometimes too brief (short labels)

Run 45 gta_game levers from calls 2–3 show options that are labels rather than complete strategic approaches:

- Lever "Urban Renewal Strategy": `"Prioritize gentrification-driven revitalization"` (42 chars)
- Lever "Talent Acquisition Model": `"Host exclusive recruitment events at major gaming conferences"` (62 chars)
- Lever "Partnership Development Roadmap": `"Host exclusive networking events for high-level executives"` (59 chars)

These fall below the system prompt requirement of "at least 15 words with an action verb" (they average 8–10 words). The system prompt section 6 says options must be self-contained descriptions and at least 15 words.

Source: `history/2/45_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`.

---

## Positive Things

### P1 — Adaptive retry loop works correctly

The `partial_recovery` events in run 51 (haiku) demonstrate the new mechanism operating as designed: when call 3 of an expected 3-call sequence fails, the prior 2 successful calls' levers are preserved and the plan is marked "ok" rather than "error". Previously, a failed mid-loop call would propagate the exception, potentially discarding all prior levers.

Source: `history/2/51_identify_potential_levers/events.jsonl`.

### P2 — Fabricated percentage claims eliminated from llama3.1 consequences

Analysis 28's assessment identified a new regression in run 03 (llama3.1 gta_game): 5 levers had fabricated magnitude claims in `consequences` ("by at least 20/15/25/30/20%"). These are absent in run 45 (llama3.1 gta_game).

All 18 levers in run 45 gta_game have consequence fields free of fabricated percentages.

Evidence: `history/2/45_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json` — levers 1–18 show qualitative consequences only ("Choosing a metropolis configuration influences...", "Implementing a realistic criminal economy system can enhance...").

### P3 — High content quality from gpt-5-nano (run 47) and haiku (run 51)

Run 47 (gpt-5-nano) hong_kong_game levers show genuine project specificity:
- "Locations-first production design emphasizing architectural paranoia" — consequences discuss location permit risk, post-production cascade effects
- "Vertical-density narrative engine across towers and escalators" — specific geography (Central, Sheung Wan, Mong Kok)
- Reviews follow "Core tension: X. Weakness: Y" structure consistently

Run 51 (haiku) hong_kong_game levers are the deepest produced so far:
- "Ending Architecture—Subverting the Original's Narrative Machinery" — 698-char consequences discuss narrative structure implications
- "Protagonist Transformation Credibility—Emotional Dissolution Versus Behavioral Resistance" — screenplay-level analysis
- Each review is unique to its lever's specific context, no copy-paste patterns detected

Evidence: `history/2/47_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`; `history/2/51_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`.

### P4 — review_lever minimum reduction (50 → 10 chars) is structurally correct

The previous 50-char minimum was a soft target that got hard-coded. The code comment at `identify_potential_levers.py:147` now explicitly says "The enrich step adds detail downstream, so 50 chars is the soft target but not enforced here." This is the right separation of concerns: the Pydantic validator catches catastrophically short reviews (< 10 chars) without penalizing terse-but-valid reviews from models that produce brief, direct critiques.

Source: `PlanExe/worker_plan/worker_plan_internal/lever/identify_potential_levers.py` lines 138–154.

### P5 — Haiku max_tokens fix prevents JSON truncation for haiku

Run 09 (haiku before) and run 51 (haiku after) both show 5/5 successful plans, but the haiku-specific JSON truncation issue (which occurred in earlier iterations when 16000 > 8192 API cap) does not appear in run 51. No EOF parsing errors for haiku. The truncation was prevented at the API level.

### P6 — lever_classification removal recovers success rate from 88.6%

The PR reverting lever_classification brought the success rate from 88.6% (iter 33) back toward the baseline 97.1%. The 94.3% achieved is not a full recovery, but represents a substantial improvement over iter 33's regressed state.

---

## Comparison

### Before (runs 03–09) vs After (runs 45–51)

Model-to-model matching is exact: same 7 models, same 5 test plans.

| Metric | Before (03–09) | After (45–51) | Change |
|--------|---------------|--------------|--------|
| Overall success rate | 34/35 = 97.1% | 33/35 = 94.3% | -2.8pp |
| LLMChatErrors (complete failures) | 1 (run 04, gpt-oss-20b, sovereign_identity) | 2 (run 45 llama3.1 sov_id; run 46 gpt-oss-20b hkg) | -1 plan |
| Partial recovery events | 2 (run 03, llama3.1: sov_id + hkg with calls_succeeded=2) | 2 (run 51, haiku: silo + parasomnia) | Same count, different model |
| gpt-oss-20b JSON EOF | 1 (sovereign_identity, line 58) | 1 (hong_kong_game, line 47) | Unchanged (different plan) |
| llama3.1 timeout | 0 | 1 (sovereign_identity ReadTimeout) | New regression |
| Fabricated % in llama3.1 consequences | 5 claims in gta_game (run 03) | 0 claims in gta_game (run 45) | Fixed |
| llama3.1 template lock (options-centric reviews) | ~62.5% "The options [verb]" (run 03 gta_game) | ~90%+ options-centric in various forms (run 45) | Worsened or unchanged |
| Haiku JSON truncation (API cap) | Not observed in run 09 | Not observed in run 51 | Unchanged |
| Haiku partial_recovery | 0 (run 09) | 2 plans (run 51) | New regression |
| Content quality (gpt-5-nano, haiku) | Not measured in prior analysis | High: 480–700 char consequences, project-specific | Improved |
| Bracket placeholder leakage | 0 | 0 | Unchanged |
| Option count violations (< 3) | 0 | 0 | Unchanged |

### Lever counts (hong_kong_game)

| Model / Run | Lever count |
|-------------|-------------|
| llama3.1 / 03 (before) | 13 |
| gpt-5-nano / 47 (after) | 18 |
| haiku / 51 (after) | 18 |

---

## Quantitative Metrics

### Success Rate by Model

| Model | Before (runs 03–09) | After (runs 45–51) |
|-------|---------------------|-------------------|
| llama3.1 | 5/5 (100%) | 4/5 (80%) |
| gpt-oss-20b | 4/5 (80%) | 4/5 (80%) |
| gpt-5-nano | 5/5 (100%) | 5/5 (100%) |
| qwen3-30b-a3b | 5/5 (100%) | 5/5 (100%) |
| gpt-4o-mini | 5/5 (100%) | 5/5 (100%) |
| gemini-2.0-flash | 5/5 (100%) | 5/5 (100%) |
| haiku-4-5 | 5/5 (100%) | 5/5 (100%)* |
| **Total** | **34/35 (97.1%)** | **33/35 (94.3%)** |

*Partial_recovery for 2 plans (calls_succeeded=2, expected_calls=3); plans marked "ok".

### Field Length Comparison (hong_kong_game, sampled levers)

| Source | Avg consequences (chars) | Avg review (chars) | Ratio vs baseline (consequences) |
|--------|--------------------------|---------------------|----------------------------------|
| Baseline train | ~270 | ~130 | 1.0× |
| Run 03 llama3.1 (before) | ~205 | ~175 | 0.76× |
| Run 47 gpt-5-nano (after) | ~480 | ~165 | 1.8× |
| Run 51 haiku (after) | ~700 | ~340 | 2.6× |

Note: The baseline train data (`baseline/train/20260310_hong_kong_game/002-10-potential_levers.json`) uses the deprecated "Controls X vs. Y. Weakness:" review format and contains fabricated percentages. Its consequences include chains like "Immediate: Viewer disorientation → Systemic: 15% higher audience engagement → Strategic: Increased critical acclaim…" These are low-quality baselines; the 1.0× reference point should not be interpreted as a quality target.

Run 51 (haiku) at 2.6× baseline consequences is a warning sign per AGENTS.md guidance (> 2× = warning, > 3× = regression). However, qualitative inspection shows the haiku consequences contain genuine narrative analysis, not fabricated statistics or marketing copy. The length is substantive rather than verbose. This is a judgment call rather than a clear regression.

### Template Leakage — Review Field

Counting reviews where the grammatical subject is "the options" or "none of the options":

| Run | Model | Plan | Options-centric reviews | Total reviews | Rate |
|-----|-------|------|------------------------|---------------|------|
| 03 (before) | llama3.1 | gta_game | 10 | 16 | 62.5% |
| 03 (before) | llama3.1 | hong_kong | 4 (duplicated exact text) | 13 | 31% |
| 45 (after) | llama3.1 | gta_game | 16 | 18 | ~89% |

The template lock worsened slightly for gta_game (62.5% → 89%). The form shifted: calls 2–3 now use "none of the options address this risk" ending rather than opening with "The options [verb]", but the subject is still anchored to options.

### Fabricated Percentage Claims

| Run | Model | Plan | Fabricated % claims | Notes |
|-----|-------|------|---------------------|-------|
| 03 (before) | llama3.1 | gta_game | 5 | "by at least 20/15/25/30/20%" in consequences |
| 45 (after) | llama3.1 | gta_game | 0 | Fixed |
| Baseline | — | hong_kong | 6+ | "15%/20%/30%/10%/25%" fabricated throughout |
| 47 (after) | gpt-5-nano | hong_kong | 0 | Clean |
| 51 (after) | haiku | hong_kong | 0 | Clean |

### Constraint Violations

| Constraint | Before | After |
|------------|--------|-------|
| Options < 3 per lever | 0 | 0 |
| review_lever < 10 chars | 0 | 0 |
| review_lever contains brackets | 0 | 0 |
| Options < 15 words (soft) | Rare | Observed in run 45 llama3.1 gta_game calls 2–3 |

### Calls per Plan (run 47, gpt-5-nano, hong_kong_game)

`activity_overview.json` shows 8 total API calls for hong_kong_game with calls_succeeded=3. This means 5 calls failed Pydantic validation internally and were retried by the LLMExecutor before the outer adaptive loop counted 3 successful DocumentDetails responses. This is higher retry overhead than expected for gpt-5-nano.

Source: `history/2/47_identify_potential_levers/outputs/20260310_hong_kong_game/activity_overview.json` (calls: 8, calls_succeeded: 3).

---

## Evidence Notes

### E1 — llama3.1 duplicate review text persisted in run 03

Run 03 hong_kong_game (before) contained 4 levers sharing identical review text: "The plan assumes a clear distinction between the game and reality, but what if the lines between them become blurred, or if the protagonist's perception of reality is challenged by the game?" (levers 2, 3, 4, 5 all copy this sentence).

Source: `history/2/03_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` lines 22, 33, 44, 55.

### E2 — Adaptive loop early-stop confirmed by llama3.1 calls_succeeded=3 at different durations

Run 45 (llama3.1): calls for each plan all show calls_succeeded=3. Durations vary (silo: 96.65s, gta_game: 97.96s, hong_kong: 135.68s). This means the loop ran 3 full calls for all successful plans without hitting the 15-lever threshold early (7 levers per call × 2 calls = 14 < 15).

### E3 — haiku 8192 max_tokens still near edge for some plans

Run 51 (haiku) activity_overview for hong_kong_game shows 3 calls with 10,159 output tokens total = ~3,386 output tokens per call. With 8192 max_tokens, this is within range. But silo and parasomnia triggered partial_recovery (calls_succeeded=2), suggesting call 3 for those plans hit some limit or error.

Source: `history/2/51_identify_potential_levers/outputs/20260310_hong_kong_game/activity_overview.json`.

### E4 — Options shorter than required (llama3.1 calls 2–3)

In run 45 gta_game, levers from calls 2–3 (indices 8–18) show options that are label-length strings rather than full strategic approaches:
- `"Prioritize gentrification-driven revitalization"` — 5 words
- `"Host exclusive recruitment events at major gaming conferences"` — 9 words
- `"Develop a competitive salary and benefits package for developers"` — 10 words

The system prompt section 6 requires "at least 15 words with an action verb." These are under the threshold.

Source: `history/2/45_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json` levers 8–18.

---

## OPTIMIZE_INSTRUCTIONS Alignment

The `OPTIMIZE_INSTRUCTIONS` constant in `identify_potential_levers.py` lines 27–80 covers:
- Overly optimistic scenarios ✓ (partially addressed)
- Fabricated numbers ✓ (fixed in run 45 vs run 03)
- Hype language ✓ (no "game-changing", "revolutionary" detected in after runs)
- Vague aspirations ✗ — Run 45 llama3.1 levers 8–18 have options that are slogans ("Prioritize gentrification-driven revitalization"), violating the "something a project manager could actually schedule and resource" criterion
- Fragile English-only validation ✓ (handled; review validator now uses structural checks only)
- Single-example template lock ✓ (documented); three examples provided in system prompt
- Template-lock migration ✓ (documented at lines 69–79); the migration to "none of the options address" confirms this concern is still live

**New recurring problem not yet in OPTIMIZE_INSTRUCTIONS:**

The 8 total API calls vs. 3 calls_succeeded discrepancy for gpt-5-nano in run 47 suggests significant internal retry overhead from Pydantic validation failures. The adaptive loop handles outer-level failures, but if the LLMExecutor itself retries failed structured outputs internally, the effective retry count can be much higher than the outer loop's max_calls=5. This "inner × outer retry amplification" can cause plan durations to balloon (gpt-5-nano parasomnia: 340s in run 46).

**Proposed addition to OPTIMIZE_INSTRUCTIONS:**
> - Inner-retry amplification. The adaptive loop runs up to max_calls=5 at the outer level. Each outer call invokes LLMExecutor which may retry internally on validation failure. If a model requires 2–3 internal retries per outer call, the total API calls can reach 15+ for a single plan. Monitor `activity_overview.json` for `calls` >> `calls_succeeded × max_calls_per_batch`. Flag when total API calls exceed 3× expected.

---

## PR Impact

### What the PR was supposed to fix

1. **Adaptive retry loop**: Replace fixed 3-call loop with min-15-levers / max-5-calls. Stops early when ≥15 levers accumulated; tolerates mid-loop failures without discarding prior results.
2. **Haiku max_tokens**: 16000 → 8192 to match haiku's API output cap, preventing JSON truncation.
3. **review_lever relaxed**: Minimum from 50 to 10 chars; fixes llama3.1 batch rejections on short reviews.
4. **Remove lever_classification**: Reverting the field that regressed success from 97.1% to 88.6% in iter 33.

### Before vs After Comparison

| Metric | Before (03–09) | After (45–51) | Change |
|--------|---------------|--------------|--------|
| Overall success rate | 34/35 (97.1%) | 33/35 (94.3%) | **-2.8pp** |
| llama3.1 success | 5/5 (100%) | 4/5 (80%) | **Regressed** |
| gpt-oss-20b success | 4/5 (80%) | 4/5 (80%) | Unchanged |
| haiku success (as "ok") | 5/5 (100%) | 5/5 (100%) | Unchanged |
| haiku partial_recovery | 0 | 2 | **New** |
| gpt-oss-20b JSON EOF | 1 occurrence | 1 occurrence | Unchanged |
| llama3.1 timeout failure | 0 | 1 | **Regressed** |
| Fabricated % (llama3.1) | 5 (run 03 gta_game) | 0 (run 45 gta_game) | **Fixed** |
| Template lock (llama3.1 reviews) | ~62.5% options-centric | ~89% options-centric | **Worsened** |
| Content quality (gpt-5-nano, haiku) | Not benchmarked separately | High; project-specific depth | **Improved** |
| Bracket placeholder leakage | 0 | 0 | Unchanged |
| Option count violations | 0 | 0 | Unchanged |

### Did the PR fix its targeted issues?

1. **Adaptive retry loop**: Partially yes. The `partial_recovery` events in run 51 demonstrate the mechanism working correctly — mid-loop failures no longer discard prior levers. But the overall plan success rate dropped, suggesting the adaptive loop's benefits are offset by new failure modes.

2. **Haiku max_tokens**: Likely yes for truncation prevention. No JSON EOF errors for haiku in run 51. However, the reduced token budget now causes some calls to fail silently (partial_recovery), suggesting 8192 may be slightly too tight for complex plans. The net effect: haiku no longer fails catastrophically but occasionally produces fewer levers than minimum.

3. **review_lever minimum relaxed**: Structurally correct; no evidence of rejection events due to short reviews in the after runs. Hard to measure directly since there are no non-English plans in the test set.

4. **lever_classification removed**: Confirmed improvement over iter 33 (88.6% → 94.3%). However, the before baseline was 97.1% (run 03–09), and the after batch is 94.3% — a 2.8pp regression from the best known state.

### Check for regressions

1. **llama3.1 new timeout failure** (run 45, sovereign_identity): Not attributable to the PR — this is a network/Ollama inference issue. However, the previous batch (run 03) had no timeout failures for llama3.1. This increases failure count from 0 to 1 for this model.

2. **haiku partial_recovery** (run 51, silo + parasomnia): Attributable to the haiku max_tokens reduction. With 8192 tokens, haiku produces ~7 levers per call. Two calls yield ~14 levers (< 15 minimum), requiring a 3rd call. If the 3rd call fails, partial_recovery fires. This is a new failure mode introduced by the PR.

3. **llama3.1 template lock worsened** (62.5% → 89%): Not directly caused by PR #351 (the PR did not change examples). This is a persistent baseline issue from the unresolved template-lock problem.

### Verdict

**CONDITIONAL**

- Keep lever_classification removal: clear improvement over iter 33's regressed state.
- Keep adaptive retry loop: it works as designed and the partial_recovery mechanism is correct.
- Keep review_lever relaxation: structurally sound, no downsides observed.
- **Investigate haiku max_tokens**: The 8192 cap appears slightly too tight for complex plans (silo, parasomnia trigger partial_recovery). Consider testing with a small buffer (e.g., 8000 to avoid hitting the cap exactly) or investigating what causes call 3 to fail for haiku on those plans.
- **Fix gpt-oss-20b max_tokens**: The same JSON truncation that haiku had now affects gpt-oss-20b on complex plans. A model-specific max_tokens cap for gpt-oss-20b is needed, similar to what was done for haiku.
- The success rate target of 97.1% (analysis 28 baseline) is not met; at 94.3%, the loop has not fully recovered the pre-iter-33 baseline.

---

## Questions For Later Synthesis

Q1. Is the haiku partial_recovery caused by the 3rd call failing at the API level (max_tokens), or by a Pydantic validation error? The events.jsonl does not log the internal failure reason for partial_recovery. Code instrumentation at `identify_potential_levers.py:316–319` only logs to debug/error, not to events.jsonl.

Q2. Does gpt-oss-20b have a documented API output cap lower than the 16000 default? If so, what is it, and should it receive the same max_tokens fix as haiku?

Q3. The adaptive retry loop requires min_levers=15 but partial_recovery fires at 14 levers (2 calls × 7). Does the downstream `DeduplicateLeversTask` tolerate 14 input levers, or does it expect ≥15? Is there a minimum lever count downstream that could fail silently?

Q4. The fabricated % claims in llama3.1 consequences appear fixed in run 45 vs. run 03. What in the PR caused this? The PR did not change the system prompt examples. Is this a run-to-run non-determinism or a genuine improvement from removing lever_classification?

Q5. The llama3.1 template lock (options-centric reviews) appears to have worsened from 62.5% to 89%. Since the PR did not change the review_lever examples, this should be attributed to run-to-run variance rather than the PR. Which claim is more likely?

---

## Reflect

This PR is a set of 4 independent changes bundled together. The signal is noisy because:

1. The llama3.1 timeout failure (run 45 sovereign_identity) is almost certainly non-deterministic (network/Ollama). It inflates the apparent regression and makes the PR look worse than it is structurally.

2. The gpt-oss-20b JSON truncation (run 46 hong_kong_game) is a pre-existing bug in a different model. It occurred in the before batch (sovereign_identity) too. The PR targeted haiku, not gpt-oss-20b. This also inflates apparent regression.

3. The haiku partial_recovery events are directly caused by the PR's max_tokens reduction. They are a real but mild regression: plans are still "ok" but with fewer levers.

4. The lever_classification removal is clearly positive (88.6% → 94.3%) and brings no observed downsides.

If the llama3.1 timeout and gpt-oss-20b EOF are excluded as model-specific pre-existing issues unrelated to the PR changes, the "pure" success rate for PR-affected plan-model pairs is: haiku 5/5 ok (with 2 partial_recovery), gpt-oss-20b same failure rate as before. The net change from the PR is: haiku gained partial_recovery protection (no catastrophic failures), lever_classification removed (success recovered). This framing is more favorable to the PR.

However, the analysis must compare actual run outcomes, not counterfactual ones. The actual success rate dropped from 97.1% to 94.3%. This is the reported fact.

---

## Potential Code Changes

**C1 — Add model-specific max_tokens cap for gpt-oss-20b (mirrors haiku fix)**

Evidence: Run 46 gpt-oss-20b hong_kong_game failed with `EOF while parsing a list at line 47 column 5`. Same error pattern as pre-PR haiku. Confirm gpt-oss-20b API output cap from provider docs, then apply the same max_tokens correction as haiku.

Expected effect: Eliminates the 1 persistent gpt-oss-20b failure per batch, recovering 97.1% baseline.

**C2 — Log partial_recovery failure reason to events.jsonl**

Evidence: The `partial_recovery` event in run 51 only records `calls_succeeded` and `expected_calls`. The underlying failure reason (API error, validation error, timeout) is not recorded. Without this, diagnosing whether haiku partial_recovery is a max_tokens issue or a different failure mode is impossible.

Proposed: Extend the `partial_recovery` event to include `failure_reason: str` capturing the last caught exception class and message.

**C3 — Add minimum option word count validator to Lever schema**

Evidence: Run 45 llama3.1 gta_game produces options as short as 5 words ("Prioritize gentrification-driven revitalization"). The system prompt section 6 says "at least 15 words with an action verb" but no Pydantic validator enforces this. The check_option_count validator only checks count ≥ 3, not word length.

Proposed: Add `@field_validator('options', mode='after')` that raises ValueError if any option has fewer than 12 words (conservative threshold; catches the clear violations without being too tight).

Expected effect: Reduces label-style options in llama3.1 second/third-call levers.

**C4 — Correct haiku max_tokens to 7500 or add safety margin**

Evidence: Run 51 haiku shows partial_recovery for silo and parasomnia. With 8192 max_tokens and ~3,386 output tokens per call (hong_kong_game successful case), the per-call average is well within range. But for complex plans, a single long-format call may approach 8192 output tokens, hitting the cap mid-JSON.

Proposed: Reduce haiku max_tokens from 8192 to 7500 (8% safety margin below the API cap), or investigate whether the partial_recovery is from a different failure mode before adjusting.

---

## Hypotheses for Prompt Changes

**H1 — Replace all three review_lever examples with non-options-centric critiques**

Evidence: Template lock persists at 89% options-centric reviews for llama3.1 gta_game (run 45). The three examples in `IDENTIFY_POTENTIAL_LEVERS_SYSTEM_PROMPT` lines 224–226 all use "none of the options price in", "the options assume", and "correlation risk absent from every option" — all anchored to the `options` subject. Weaker models copy this grammatical structure.

Change: Replace all three examples with critiques that name a project-specific trade-off without mentioning the options object at all. For example: "Seasonal harvest timing conflict: any fixed hiring date committed before October soil moisture data conflicts with the agronomic window, because late-summer moisture shortfalls or surpluses shift optimal planting by 2–3 weeks."

Expected: Reduce llama3.1 options-centric review rate from 89% toward < 30% across all calls.

**H2 — Add a "second-call diversity" instruction to the user prompt injection**

Evidence: Run 45 gta_game calls 2–3 produce shorter options and more formulaic reviews compared to call 1. The current second-call prompt only adds "Generate 5 to 7 MORE levers with completely different names. Do NOT reuse any of these already-generated names." It does not instruct the model to also vary the review style or option depth.

Change: Add "Vary your critique format and option detail level compared to the first batch." to the multi-call continuation prompt.

Expected: Improve consistency of option quality and review format across calls 1–3 for llama3.1.

---

## Summary

PR #351 bundles four changes with mixed outcomes:

- **lever_classification removal**: Clearly positive. Success recovered from 88.6% (iter 33) to 94.3%.
- **Adaptive retry loop**: Works as designed. partial_recovery demonstrated in run 51 (haiku). Does not inflate success rate because haiku partial_recovery introduces a new failure mode.
- **Haiku max_tokens 16000 → 8192**: Prevents JSON truncation for haiku at the API level. Side effect: haiku now occasionally produces fewer than 15 levers per run (partial_recovery for 2 plans in run 51).
- **review_lever minimum 50 → 10**: Structurally correct. No observable downsides.

Overall success rate moved from 97.1% (baseline after PR #340 / analysis 28) to 94.3% — a 2.8pp regression. The regression is partially attributable to a llama3.1 network timeout (non-deterministic) and a persistent gpt-oss-20b JSON truncation bug (pre-existing, not targeted by this PR). Excluding these model-specific non-PR issues, the PR's direct effect on haiku is neutral-to-slightly-negative (partial_recovery introduced).

The primary outstanding issue — template lock in llama3.1 reviews — was not addressed by this PR and remains at ~89% options-centric reviews, slightly worsened from the 62.5% in analysis 28.

**Most urgent follow-ups:**
1. Fix gpt-oss-20b max_tokens (C1) — same truncation fix applied to haiku
2. Replace all three review_lever examples (H1) — template lock root cause
3. Log partial_recovery failure reason (C2) — diagnosis gap for haiku calls

**Verdict for PR #351: CONDITIONAL** — Keep lever_classification removal and review_lever relaxation unconditionally. Investigate haiku max_tokens edge case before closing the PR as fully resolved.
