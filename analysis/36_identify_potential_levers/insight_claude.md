# Insight Claude

## Scope

Analyzing runs `2/59–2/65` (after PR #354) against `2/52–2/58` (before, from analysis 35)
for the `identify_potential_levers` step.

**PR under evaluation:** PR #354 "fix: domain-diverse examples, anti-pattern prohibition, B1 partial_recovery"

Changes made (from PR description):
1. **Domain-diverse examples**: Replace urban-planning and insurance examples with medical
   (IRB/clinical-site sequential overhead) and game-dev (GPU migration hidden artist-hour cost).
   Three examples now span agriculture, medical, and technology.
2. **Explicit prohibition**: Add ban on "The options"/"These options"/"The lever"/"These levers"
   as `review_lever` grammatical subject to section 5.
3. **B1 fix**: Step-gate `partial_recovery` event to `identify_potential_levers` only — stops
   spurious events for `identify_documents`. Remove stale `expected_calls=3` constant.
4. **OPTIMIZE_INSTRUCTIONS**: Document structural homogeneity requirement.

**Model mapping:**

| Run (before) | Run (after) | Model |
|---|---|---|
| 2/52 | 2/59 | ollama-llama3.1 |
| 2/53 | 2/60 | openrouter-openai-gpt-oss-20b |
| 2/54 | 2/61 | openai-gpt-5-nano |
| 2/55 | 2/62 | openrouter-qwen3-30b-a3b |
| 2/56 | 2/63 | openrouter-openai-gpt-4o-mini |
| 2/57 | 2/64 | openrouter-gemini-2.0-flash-001 |
| 2/58 | 2/65 | anthropic-claude-haiku-4-5-pinned |

---

## Negative Things

1. **llama3.1 success rate regressed from 5/5 to 3/5.** Run 59 (llama3.1, after PR #354)
   failed on two plans:
   - **gta_game**: "1 validation error for DocumentDetails / levers.5.options / Value error,
     options must have at least 3 items, got 2" — the model returned only 2 options for lever 5.
   - **parasomnia**: 7 validation errors, all "review_lever is too short (2 chars); expected at
     least 10 [type=value_error, input_value='=>']" — the model produced `=>` (an arrow separator)
     for every review_lever in the batch. This is a parsing artifact: the model appears to have
     used a key-arrow-value format and only the arrow part got captured.
   Evidence: `history/2/59_identify_potential_levers/outputs.jsonl` (errors) and
   `history/2/59_identify_potential_levers/events.jsonl`.

2. **llama3.1 hong_kong: template lock REGRESSED from 0% to 100%.** In run 52 (before PR #354),
   hong_kong had 0% "the options" template lock — all reviews used domain-specific subjects.
   In run 59 (after PR #354), ALL 12 hong_kong reviews start with
   "The options [miss/overlook/neglect/fail]...". Examples:
   - "The options miss addressing the tension between preserving Hong Kong's cinematic DNA..."
   - "The options overlook the potential for the game to manipulate not just the protagonist's relationships..."
   - "The options neglect to consider the impact of the game's mechanics on the city itself..."
   This is a complete reversal of the improvement from PR #353 for the hong_kong plan.
   Evidence: `history/2/59_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`
   — all 12 review fields.

3. **llama3.1 silo: new multi-template lock replacing the old "the options" pattern.** In run 59
   silo (successful, 3/3 calls):
   - Levers 1–7 (1st LLM call): ALL follow "[Lever Name] - The core tension lies in balancing X
     with Y. A weakness this lever misses is Z." — a new formulaic opener.
   - Levers 8–14 (2nd call): "The silo's X creates/is Y..." pattern (~6 levers).
   - Levers 15–21 (3rd call): "The [focus/emphasis/reliance] on X overlooks/neglects Y." pattern.
   - One exact duplicate: levers 10 and 14 have identical review text ("The silo's reliance on
     government funding creates a dependency on external resources, making it vulnerable to
     changes in political priorities or budget allocations.").
   "The options" was eliminated, but was replaced by per-call template locking. The explicit
   prohibition appears to be redirecting llama3.1 to new repetitive patterns rather than
   producing diverse reviews.
   Evidence: `history/2/59_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`.

4. **llama3.1 sovereign_identity: new formulaic template in first LLM call.** Levers 1–6 in
   sovereign_identity (run 59) all follow "[Action] creates a tension between X and Y. However,
   this approach misses Z." Examples:
   - "Refactoring the MitID ecosystem to decouple from Apple/Google platform integrity signals
     creates a tension between preserving existing investments in asset re-profiling and
     certification, versus embracing open standards... However, this approach misses the
     complexity of establishing an entirely new fallback authentication path..."
   - "Influencing AltID procurement to include platform-neutral or fallback-capable access paths
     creates a tension between securing formal written responses from relevant authorities and
     navigating the complexities of institutional inertia and incumbent resistance. However,
     this approach misses the need for credible technical demonstrations..."
   All 6 first-call reviews follow this exact structure. "The options" is gone, replaced by a
   new formulaic opener.
   Evidence: `history/2/59_identify_potential_levers/outputs/20260308_sovereign_identity/002-10-potential_levers.json`
   levers 1–6.

5. **Overall plan-level success rate regressed.** Before: 35/35 = 100%. After: 33/35 = 94.3%.
   The two failures are both llama3.1. This is a net regression of -5.7pp.

6. **gpt-oss-20b (run 60) hong_kong: new formulaic template "[Name]: The tension lies between X;
   the options overlook Y."** While "the options" is no longer the grammatical *subject*, it
   appears consistently in the second clause. Examples:
   - "Director Alignment: The tension lies between authentic local vision and global marketability;
     the options overlook the risk of creative conflict when co‑directing..."
   - "Star Power Calibration: The core tension is balancing budget constraints with global market
     pull; the options miss the possibility of leveraging a dual‑market star..."
   - "IP Clearance Path: The tension is between creative control and financial risk; the options
     overlook the strategic benefit of a revenue‑sharing model..."
   All 10 first-call reviews follow this "[Name]: [tension]; the options [verb] Y" skeleton.
   The prohibition technically passed (subject is the lever name) but the output is still
   formulaic.
   Evidence: `history/2/60_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`.

7. **haiku partial recoveries unchanged at 2 plans.** Run 58 (before): hong_kong (2/3) and
   parasomnia (2/3). Run 65 (after): hong_kong (2/3) and parasomnia (2/3). The B1 fix confirms
   these are legitimate partial_recovery events for identify_potential_levers — not spurious
   `identify_documents` events. The underlying cause of haiku's partial recoveries remains
   unresolved.
   Evidence: `history/2/65_identify_potential_levers/events.jsonl` — two `partial_recovery` events.

---

## Positive Things

1. **B1 fix is confirmed working.** The partial_recovery event for run 65 (haiku) correctly
   includes `"expected_calls": 3` (dynamic, not the stale constant), and fires only for
   `identify_potential_levers`. Events are gated correctly. The haiku partial recoveries
   (hong_kong and parasomnia) appear in `events.jsonl` as expected.
   Evidence: `history/2/65_identify_potential_levers/events.jsonl` lines 5–6, 11–12.

2. **Runs 60–64 (5 cloud models) maintain perfect 5/5 success with 3/3 calls.** No errors,
   no partial recoveries for gpt-oss-20b, gpt-5-nano, qwen3-30b, gpt-4o-mini, gemini-flash.
   Evidence: `history/2/60_identify_potential_levers/outputs.jsonl` through
   `history/2/64_identify_potential_levers/outputs.jsonl`.

3. **gpt-5-nano (run 61) parasomnia shows strong domain-specific reviews.** The medical/IRB
   examples appear to have helped gpt-5-nano produce substantive, structured reviews for the
   medical domain. Sample:
   - "Core tension: balancing capital-intensive expansion with data-quality resilience; a weakness:
     none of the options explicitly address a depreciation or financing strategy to absorb capital
     risk, nor a contingency for safety staffing in surge scenarios."
   - "Core tension between open data validation and participant privacy; a weakness: lacks a
     strategy for dynamic consent management for future data reuse..."
   Reviews use "Core tension: X; a weakness: Y." format — compact, domain-specific, no
   fabricated percentages.
   Evidence: `history/2/61_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json`.

4. **gpt-oss-20b (run 60) gta_game reviews show no "The options" as subject.** Reviews are
   short, balanced, and non-formulaic compared to silo:
   - "Balancing integration overhead against scalability; options overlook the communication
     overhead required to coordinate microservices across large teams."
   - "Tension between speed and artistic fidelity; options ignore long-term maintenance of
     procedural tools and potential artist resistance."
   Neither "the options" nor "the lever" appears as grammatical subject.
   Evidence: `history/2/60_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`.

5. **haiku (run 65) hong_kong output quality remains high.** Despite partial recovery (2/3
   calls), the levers produced are substantive, with long and non-formulaic reviews. Example:
   "The tension between franchise recognition and creative differentiation cannot be resolved
   by simply adding another plot twist — audiences familiar with Fincher's film will spot
   structural echoes regardless. The options address the screenplay layer but neglect the
   directing and editing craft needed to execute the twist payoff..."
   Evidence: `history/2/65_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`.

6. **No LLMChatErrors for cloud models.** The plan-level errors in run 59 are Pydantic
   validation errors (schema violations), not JSON parse failures or network timeouts. This
   means the cloud models reliably produce valid JSON.

---

## Comparison

| Metric | Before (runs 52–58) | After (runs 59–65) | Change |
|--------|--------------------|--------------------|--------|
| **Plan-level success rate** | 35/35 = 100% | 33/35 = 94.3% | **-5.7pp REGRESSED** |
| **LLMChatErrors** | 0 | 0 | No change |
| **Pydantic validation failures** | 0 | 2 (gta_game options=2, parasomnia review='=>') | **+2 NEW FAILURES** |
| **llama3.1 plan errors** | 0 | 2 (gta_game, parasomnia) | **REGRESSION** |
| **haiku partial recoveries** | 2 (hong_kong, parasomnia) | 2 (hong_kong, parasomnia) | No change |
| **llama3.1 partial recoveries** | 1 (gta_game 2/3) | 0 | IMPROVED (plan failed instead) |
| **llama3.1 hong_kong "the options" lock** | 0% (0/17) | 100% (12/12) | **MAJOR REGRESSION** |
| **llama3.1 silo "the options" lock** | 0% (0/21) | 0% | No change |
| **llama3.1 silo new call-specific lock** | Low | 100% call 1 + per-call patterns | **NEW REGRESSION** |
| **gpt-oss-20b hong_kong lock** | Low (≤20%) | ~100% "[Name]: [tension]; options [verb]" | **NEW TEMPLATE** |
| **gpt-5-nano parasomnia quality** | Good | Strong "Core tension: X; weakness: Y" | **IMPROVED** |
| **haiku hong_kong content quality** | High | High | Maintained |
| **Fabricated % claims detected** | 0 (in run 52) | 0 | No change |

---

## Quantitative Metrics

### Plan-Level Outcome Summary

| Run | Model | Plans OK | Plans Error | Partial Recovery |
|-----|-------|----------|-------------|-----------------|
| 52 | llama3.1 | 5 | 0 | 1 plan (gta_game 2/3 calls) |
| 59 | llama3.1 | 3 | 2 (gta_game, parasomnia) | 0 |
| 53 | gpt-oss-20b | 5 | 0 | 0 |
| 60 | gpt-oss-20b | 5 | 0 | 0 |
| 54 | gpt-5-nano | 5 | 0 | 0 |
| 61 | gpt-5-nano | 5 | 0 | 0 |
| 55 | qwen3-30b | 5 | 0 | 0 |
| 62 | qwen3-30b | 5 | 0 | 0 |
| 56 | gpt-4o-mini | 5 | 0 | 0 |
| 63 | gpt-4o-mini | 5 | 0 | 0 |
| 57 | gemini-flash | 5 | 0 | 0 |
| 64 | gemini-flash | 5 | 0 | 0 |
| 58 | haiku | 5 | 0 | 2 plans (hong_kong, parasomnia 2/3) |
| 65 | haiku | 5 | 0 | 2 plans (hong_kong, parasomnia 2/3) |

### Template Lock Rate — llama3.1, review_lever field

| Plan | Before (run 52) | After (run 59) | Dominant pattern (after) |
|------|-----------------|----------------|--------------------------|
| silo | 0% (0/21) | 0% "the options" but 100% call-1 lock | "[Name] - The core tension lies in..." |
| hong_kong_game | 0% (0/17) | **100% (12/12)** | "The options miss/overlook/neglect/fail..." |
| sovereign_identity | ~0% | ~90% call-1 lock | "[Action] creates a tension between X and Y. However, this approach misses Z." |
| gta_game | ~78% "these options" | FAILED | n/a (validation error) |
| parasomnia | ~82% | FAILED | n/a (review_lever = '=>') |

Note: "The options" lock was 0% for hong_kong and silo in run 52 (after PR #353). PR #354
regressed hong_kong to 100% and introduced new call-specific lock patterns.

### Pydantic Failure Summary

| Run | Plan | Error type | Field | Value |
|-----|------|-----------|-------|-------|
| 59 | gta_game | options count | levers.5.options | 2 items (need ≥3) |
| 59 | parasomnia | review_lever length | levers.0–6.review_lever | '=>' (2 chars, need ≥10) |

### Field Length Comparison (silo plan, sampled)

Baseline averages (from analysis 35/27): avg_conseq=279, avg_review=152, avg_opts=453.

| Field | Baseline avg | Before (52/silo) | After (59/silo) | vs Baseline |
|-------|--------------|-----------------|-----------------|-------------|
| consequences | 279 chars | ~161 chars | ~265 chars | 0.95× |
| review | 152 chars | ~223 chars | ~235 chars | 1.55× |
| options (3 combined) | 453 chars | ~228 chars | ~270 chars | 0.60× |

Notes:
- Run 59 silo consequences are 0.95× baseline — near parity, no fabricated percentages.
- Run 59 silo reviews are 1.55× baseline — within the 2× warning threshold.
- Run 59 silo options are 0.60× baseline — somewhat short, some label-like entries persist.

---

## Evidence Notes

- **Run 59 hong_kong regression**: All 12 reviews in
  `history/2/59_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`
  start with "The options miss/overlook/neglect/fail..." — verbatim "The options" as grammatical
  subject despite the explicit prohibition added by PR #354.
- **Run 52 hong_kong improvement**: Zero "the options" reviews in
  `history/2/52_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json`
  (verified in analysis 35).
- **Run 59 parasomnia failure**: Log at
  `history/2/59_identify_potential_levers/outputs/20260311_parasomnia_research_unit/log.txt`
  shows `review_lever` fields received as '=>' (literal arrow separator, 2 chars).
- **Run 59 gta_game failure**: `events.jsonl` shows "options must have at least 3 items, got 2"
  for levers.5.options — the model skipped the third option for one lever.
- **Run 65 partial_recovery fix**: `history/2/65_identify_potential_levers/events.jsonl` shows
  `partial_recovery` events with `calls_succeeded: 2` and `expected_calls: 3` — the dynamic
  expected_calls field is correct, confirming the stale constant was removed.
- **gpt-5-nano parasomnia quality**: Verified in
  `history/2/61_identify_potential_levers/outputs/20260311_parasomnia_research_unit/002-10-potential_levers.json`
  — reviews follow "Core tension: X; a weakness: Y." pattern, domain-specific, no "the options".
- **gpt-oss-20b gta_game**: Verified in
  `history/2/60_identify_potential_levers/outputs/20250329_gta_game/002-10-potential_levers.json`
  — reviews are short and varied, no "the options" as subject.

---

## OPTIMIZE_INSTRUCTIONS Alignment

The PR added documentation of the structural homogeneity requirement to `OPTIMIZE_INSTRUCTIONS`.
Based on observed behavior:

1. **New gap: negative prohibition without positive examples.** The explicit prohibition ("do not
   use 'The options' as grammatical subject") tells smaller models what NOT to do, but without
   updated examples that demonstrate diverse alternatives, llama3.1 reverts to either:
   (a) the same prohibited pattern (hong_kong: 100% "The options" lock despite prohibition), or
   (b) alternative parsing artifacts (parasomnia: '=>' output).
   Proposed addition to OPTIMIZE_INSTRUCTIONS: *"Negative prohibitions are insufficient for
   smaller models (llama3.1-scale). A prohibition like 'do not start with X' must be paired
   with a positive example showing how to START differently in the SAME call — prohibiting a
   pattern without providing a positive alternative leads to malformed output or pattern reversion."*

2. **New gap: per-call template drift.** Each of the 3 LLM calls for a given plan develops its
   own template lock independently. PR #354 documented the multi-call problem but did not address
   it mechanically. The silo output (run 59) shows three distinct per-call patterns:
   - Call 1: "[Name] - The core tension lies in..."
   - Call 2: "The silo's X creates/is..."
   - Call 3: "The [focus/reliance] on X overlooks..."
   This confirms that changing examples in the system prompt changes the lock target, but does not
   eliminate lock. Proposed addition: *"Template lock re-forms independently per LLM call using
   whatever structural pattern appears most locally consistent. Call-specific example diversity is
   more effective than general example diversity: consider using a per-call instruction suffix that
   varies the target structure."*

3. **B1 fix alignment**: The removal of `expected_calls=3` constant is now confirmed working.
   OPTIMIZE_INSTRUCTIONS should document that `expected_calls` must be dynamic (derived from
   actual call count) to avoid false partial_recovery events for steps with different call counts.

---

## Hypotheses

**Prompt hypotheses:**

H1: The explicit prohibition against "The options"/"The lever" as grammatical subject is not
respected by llama3.1. The model's tendency to copy example structure overrides the text of the
prohibition. Removing the explicit prohibition and instead ensuring ALL examples use non-options
subjects (across all three example review fields) would be more effective than the prohibition alone.
Evidence: Run 59 hong_kong — 100% "The options" despite prohibition in prompt.
Expected effect: Removing prohibition but having domain-diverse examples WITHOUT "the options"
as subject should reduce lock for llama3.1 without producing parsing artifacts.

H2: The game-dev example (GPU migration, artist-hour cost) may itself contain "the options" or
"the lever" in its review_lever field, which llama3.1 is copying. If the example review_lever
begins with "The options [verb]", adding a prohibition won't fix the copy behavior — the example
must change.
Evidence: Indirect — the game-dev example specifically targets the hong_kong domain (entertainment/tech)
and hong_kong shows 100% lock in run 59 vs 0% in run 52. Run 52 used a different example set
without a game-dev example. Needs direct verification of the PR #354 example text.
Expected effect: If H2 is confirmed, replace the game-dev example's review_lever with one that
does NOT use "The options" as subject.

H3: The gta_game validation failure (2 options instead of 3) may be caused by the new game-dev
example structuring options differently (e.g., in a list with fewer items). If the example
shows 2 options, llama3.1 may generate 2 options.
Evidence: Indirect — requires reading the actual PR #354 prompt to verify option count in examples.

**Code hypotheses:**

C1: The `check_review_format` validator currently only checks minimum length (10 chars) and no
brackets. Adding a soft log (not a hard raise) when `review_lever` starts with "the options",
"these options", "the lever", or "these levers" (case-insensitive) would quantify template lock
rate in production without causing validation failures. This would produce observable metrics.

C2: The `=>` failure in run 59 parasomnia suggests the model generated a "key => value" formatted
output. Adding a validator check that flags `review_lever` values containing only punctuation or
arrow characters (e.g., `=`, `>`, `=>`, `->`) would catch this failure mode earlier and potentially
enable smarter retry logic (e.g., inject a "do not use arrow notation" reminder).

C3: The gta_game failure (2 options instead of 3) could be caught with a validator check before
the Pydantic schema. A pre-schema check could count options and add a warning, giving the
retry loop a chance to request a corrected output rather than exhausting retries.

---

## PR Impact

### What the PR was supposed to fix

PR #354 targeted the remaining issues from PR #353:
1. Template lock for parasomnia and gta_game domains (which PR #353's construction/agricultural
   examples didn't fix).
2. Explicit prohibition of "The options" as grammatical subject.
3. B1 code fix: spurious partial_recovery events for `identify_documents`.
4. OPTIMIZE_INSTRUCTIONS documentation.

### Before vs. After Comparison

| Metric | Before (runs 52–58) | After (runs 59–65) | Change |
|--------|--------------------|--------------------|--------|
| Plan success rate | 35/35 = 100% | 33/35 = 94.3% | **-5.7pp** |
| llama3.1 plan errors | 0 | 2 (gta_game, parasomnia) | **+2 REGRESSION** |
| haiku partial recoveries | 2 | 2 | No change |
| llama3.1 hong_kong "the options" lock | 0% | 100% | **MAJOR REGRESSION** |
| llama3.1 silo "the options" lock | 0% | 0% | No change |
| llama3.1 silo call-1 template lock | Low | 100% new template | **NEW REGRESSION** |
| gpt-5-nano parasomnia quality | Good | Strong | IMPROVED |
| gpt-oss-20b gta_game "the options" lock | Low | 0% as subject | MAINTAINED |
| B1 partial_recovery scoping | Not gated | Gated to `identify_potential_levers` | **FIXED** |

### Did the PR fix the targeted issues?

**No, and it caused regressions.**

1. **Template lock for parasomnia**: FAILED — parasomnia now produces a Pydantic validation
   error (review_lever='>' output) for llama3.1, not a template lock issue. The fix made things
   worse.

2. **Template lock for gta_game**: FAILED — gta_game now produces a Pydantic validation error
   (only 2 options) for llama3.1. The fix made things worse.

3. **Explicit prohibition**: INEFFECTIVE for llama3.1. hong_kong went from 0% "the options"
   (after PR #353, which worked) to 100% "the options" (after PR #354, which reverted it).
   The prohibition added complexity without measurable benefit.

4. **B1 fix**: CONFIRMED WORKING. The `partial_recovery` event is correctly gated and the
   dynamic `expected_calls` value is correct.

5. **Domain-diverse examples**: MIXED — the medical example appears to have helped gpt-5-nano
   for parasomnia quality, but the game-dev example may have triggered hong_kong regression
   for llama3.1.

### Regressions

1. llama3.1 success rate: 5/5 → 3/5 (−2 plans, both Pydantic failures)
2. llama3.1 hong_kong template lock: 0% → 100% (complete reversal)
3. llama3.1 silo: new call-specific template lock patterns (formulaic per-call openers)
4. gpt-oss-20b hong_kong: new formulaic "[Name]: [tension]; the options [verb]" template

### Verdict

**REVERT** — PR #354 introduces a net regression: the plan success rate dropped from 100% to
94.3%, the key hong_kong improvement from PR #353 was reversed (0% → 100% "The options" lock),
and two new Pydantic failure modes were introduced for llama3.1. The only unambiguously positive
change (B1 fix) should be cherry-picked into a separate, focused PR to avoid reverting it with
the rest of the changes.

The explicit prohibition change is the most likely culprit. Smaller models like llama3.1 are
not reliable at honoring negative prompt constraints ("do not use X"). When the prohibition
conflicts with the model's structural tendency to copy example patterns, the model either
ignores the prohibition (hong_kong: 100% "The options") or produces malformed output
(parasomnia: '=>'). The correct fix for template lock in smaller models is to change the
examples themselves (as PR #353 did successfully) rather than add prohibitions.

---

## Questions For Later Synthesis

1. Does the game-dev example in PR #354 itself use "The options" in its review_lever field?
   If yes, that explains why hong_kong (a game/film domain) regressed — llama3.1 is copying
   the example review structure.

2. Why does the explicit prohibition work for cloud models (gpt-5-nano, gpt-oss-20b) but not
   for llama3.1? Is this a scale-dependent instruction-following failure?

3. The B1 fix should be preserved. What is the cleanest way to cherry-pick it without the
   problematic example/prohibition changes? (Separate PR vs. revert-then-forward-apply.)

4. Should future prompt experiments for template lock focus on example diversity (changing
   example content) rather than prohibitions (adding negative instructions)?

5. The haiku partial recoveries (hong_kong and parasomnia) persist across both PR #353 and
   PR #354. What is causing exactly 2 out of 3 calls to fail for haiku on these specific plans?
   Is it output length? Is it a specific schema field?

---

## Reflect

PR #354 attempted two distinct fixes simultaneously: (a) domain-diverse examples to address
parasomnia/gta_game template lock and (b) an explicit prohibition to prevent "The options" as
grammatical subject. The evidence shows that fix (a) may have helped some cloud models for
those domains but introduced new structural patterns, while fix (b) was harmful for llama3.1
— causing either reversion to prohibited patterns or parsing artifacts.

The key lesson is that PR #353 worked precisely *because* it changed the example structure
rather than prohibiting a pattern. PR #354 undid the example change that made PR #353 work
for hong_kong, and added a prohibition that llama3.1 cannot reliably honor.

The correct path forward is:
1. Revert PR #354's example and prohibition changes.
2. Cherry-pick the B1 fix into a standalone PR.
3. If domain-diverse examples are still desired, add the medical/game-dev examples *in addition
   to* (not replacing) the examples that worked for hong_kong and silo in PR #353, verifying
   that none of the new example review fields use "The options" as subject.

---

## Potential Code Changes

- **B1**: Keep the `partial_recovery` step-gating fix (step-gating partial_recovery event to
  `identify_potential_levers` and removing `expected_calls=3` constant). This is confirmed
  working and correct.

- **C1**: Add soft logging for template lock detection (log a warning when `review_lever` starts
  with "the options"/"the lever" — do not raise). This makes lock rate observable in production.

- **C2**: Add a validator check for degenerate `review_lever` values (e.g., values that are
  pure punctuation or arrow symbols like `=>`, `->`, `::`). Log a warning or raise to trigger
  retry with a corrected prompt.

- **C3**: Add a pre-validation options count check to produce a more informative error message
  when a model returns fewer than 3 options, enabling targeted retry logic.

---

## Summary

PR #354 produced a net regression across all three of its prompt changes:

1. **Domain-diverse examples** (medical + game-dev): Mixed results — gpt-5-nano parasomnia
   quality improved, but llama3.1 hong_kong reverted to 100% "The options" lock (from 0% in
   PR #353). The game-dev example may itself contain the prohibited pattern.

2. **Explicit prohibition** ("The options"/"The lever" as subject): Did not work for llama3.1.
   hong_kong went from 0% to 100% lock; parasomnia produced malformed `=>` output failing
   Pydantic validation.

3. **B1 fix** (step-gate partial_recovery): Confirmed working — the only positive change in
   the PR.

Overall:
- **Success rate**: 100% → 94.3% (−2 plans, both llama3.1)
- **New failures**: gta_game (2 options instead of 3), parasomnia (`=>` as review_lever)
- **Template lock**: hong_kong regressed from 0% to 100%; new formulaic patterns in silo and
  sovereign_identity first calls
- **B1 fix**: Working correctly

**Recommended action**: REVERT PR #354's prompt changes. Cherry-pick the B1 fix separately.
Do not add explicit prohibitions to the system prompt for template lock — change the examples
instead. Verify that any future game-dev/medical examples do not use "The options" as subject
in their review_lever fields.
