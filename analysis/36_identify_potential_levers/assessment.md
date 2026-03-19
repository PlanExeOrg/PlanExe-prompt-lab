# Assessment: fix: domain-diverse examples, anti-pattern prohibition, B1 partial_recovery

## Issue Resolution

**PR #354 targeted four issues:**

1. **Template lock for parasomnia and gta_game** — the domain-monoculture problem left open by PR #353. New examples were to span agriculture (existing), medical (IRB/clinical-site sequential overhead), and game-dev (GPU migration hidden artist-hour cost).

2. **Explicit prohibition** — add a ban on "The options"/"These options"/"The lever"/"These levers" as `review_lever` grammatical subject in section 5.

3. **B1 code fix** — step-gate `partial_recovery` events to `identify_potential_levers` only; remove stale `expected_calls=3` constant.

4. **OPTIMIZE_INSTRUCTIONS** — document structural homogeneity requirement.

**Outcome by issue:**

| Issue | Outcome |
|-------|---------|
| Template lock (parasomnia/gta_game) | **FAILED** — both plans now produce Pydantic validation errors for llama3.1 rather than template lock. The underlying pattern was not eliminated, it was worsened. |
| Explicit prohibition | **FAILED for llama3.1** — hong_kong lock reversed from 0% (after PR #353) to 100% "The options" despite prohibition. Prohibition confirms S1: naming the banned phrases in the prompt increases their probability mass for small models. Cloud models unaffected. |
| B1 step-gating fix | **CONFIRMED WORKING** — `history/2/65_identify_potential_levers/events.jsonl` shows `partial_recovery` events scoped to `identify_potential_levers` with dynamic `expected_calls: 3`. |
| OPTIMIZE_INSTRUCTIONS documentation | **CONFIRMED** — structural homogeneity requirement documented. Accurate but the PR did not prevent the same problem it documented. |

**Residual symptoms:**
- llama3.1 hong_kong: 100% "The options miss/overlook/neglect/fail…" lock, directly verified in `history/2/59_identify_potential_levers/outputs/20260310_hong_kong_game/002-10-potential_levers.json` (levers 1, 2, 3, 5, 6, 7 all open with "The options").
- llama3.1 silo: new per-call template lock — call 1 uses "[Name] - The core tension lies in balancing X with Y. A weakness this lever misses is Z." (7/7 first-call levers follow this pattern, confirmed in `history/2/59_identify_potential_levers/outputs/20250321_silo/002-10-potential_levers.json`).
- llama3.1 gta_game and parasomnia: hard plan failures (Pydantic), not just template lock.

---

## Quality Comparison

Models appearing in both batches: llama3.1, gpt-oss-20b, gpt-5-nano, qwen3-30b, gpt-4o-mini, gemini-2.0-flash, haiku-4-5 (7 models × 5 plans = 35 executions each).

| Metric | Before (runs 52–58) | After (runs 59–65) | Verdict |
|--------|--------------------|--------------------|---------|
| **Success rate** | 35/35 = 100% | 33/35 = 94.3% | **REGRESSION −5.7pp** |
| **LLMChatErrors** | 0 | 0 | UNCHANGED |
| **Pydantic validation failures** | 0 | 2 (gta_game: 2 options; parasomnia: `=>` review_lever) | **NEW FAILURES** |
| **llama3.1 plan errors** | 0 | 2 (gta_game, parasomnia) | **REGRESSION** |
| **haiku partial recoveries** | 2 (hong_kong 2/3, parasomnia 2/3) | 2 (hong_kong 2/3, parasomnia 2/3) | UNCHANGED |
| **llama3.1 partial recoveries** | 1 (gta_game 2/3) | 0 (plan failed instead) | NOT AN IMPROVEMENT |
| **Bracket placeholder leakage** | 0 | 0 | UNCHANGED |
| **Option count violations** | 0 | 1 (gta_game levers.5 got 2 items) | **REGRESSION** |
| **Template lock — llama3.1 hong_kong** | 0% (0/17 "the options") | 100% (12/12 "The options…") | **MAJOR REGRESSION** |
| **Template lock — llama3.1 silo "the options"** | 0% (0/21) | 0% | MAINTAINED |
| **New per-call template lock — silo call 1** | Low | 100% "[Name] - The core tension lies in…" | **NEW REGRESSION** |
| **Template lock — llama3.1 sovereign_identity call 1** | ~0% | ~90% "[Action] creates a tension between X and Y. However, this approach misses Z." | **NEW REGRESSION** |
| **New formulaic "[Name]: [tension]; options [verb]" — gpt-oss-20b hong_kong** | Low (≤20%) | ~100% first call | **NEW TEMPLATE** |
| **gpt-5-nano parasomnia review quality** | Good | Strong ("Core tension: X; a weakness: Y.") | IMPROVED |
| **haiku hong_kong content quality** | High | High (despite partial recovery) | MAINTAINED |
| **Fabricated % claims in consequences** | 0 | 0 | UNCHANGED |
| **Marketing-copy language** | Low | Low | UNCHANGED |
| **Consequences length vs baseline (silo)** | 0.58× baseline (161/279) | 0.95× baseline (265/279) | IMPROVED |
| **Review length vs baseline (silo)** | 1.47× baseline (223/152) | 1.55× baseline (235/152) | SLIGHT INCREASE (within 2× threshold) |
| **Options length vs baseline (silo)** | 0.50× baseline (228/453) | 0.60× baseline (270/453) | SLIGHT IMPROVEMENT (still short) |
| **Cross-call duplication** | Present | Present | UNCHANGED |
| **Over-generation (>7 levers/call)** | Haiku routinely 8+ | Haiku routinely 8+ | UNCHANGED (handled by downstream dedup) |
| **B1 step-gating fix** | Not gated | Correctly gated | **FIXED** |

**Notes on OPTIMIZE_INSTRUCTIONS alignment:**

PR #354 added the structural homogeneity requirement to OPTIMIZE_INSTRUCTIONS. However, the PR itself violated it: all three new examples share the "apparent benefit → hidden undermining cost in unexpected dimension" adversarial structure (code review S3). More importantly, the game-dev example (GPU migration) introduces a domain that directly overlaps with `hong_kong_game` and `gta_game` test plans — a template leakage vector the OPTIMIZE_INSTRUCTIONS should have flagged. The PR documented the rule without checking compliance.

Two new gaps exposed by this PR that should be added to OPTIMIZE_INSTRUCTIONS:
1. *"Explicit prohibitions are insufficient for smaller models (llama3.1-scale). Naming the banned phrase in the prohibition increases its salience. Fix the examples instead."*
2. *"The example domain must not overlap with any test plan domain. Game/entertainment examples will be copied verbatim by small models when generating game/entertainment plan reviews."*

---

## New Issues

1. **Prohibition backfire (S1).** Naming the banned phrases ("The options", "The lever") in the prohibition text increases their probability mass for small models. llama3.1 hong_kong went from 0% "The options" lock (PR #353, no prohibition) to 100% lock (PR #354, prohibition added). The correlation is unambiguous. Cloud models (gpt-5-nano, gpt-4o-mini, etc.) follow the prohibition correctly; llama3.1-scale models do not.

2. **Domain collision (S2).** The game-dev example (GPU migration, artist-hour cost) overlaps with `hong_kong_game` and `gta_game` test plans. llama3.1 activates the most domain-similar example as a structural template. PR #353 (different examples, no gaming domain) achieved 0% "The options" lock on hong_kong; PR #354 (game-dev example added) reverted to 100%. This is the primary causal vector for the hong_kong regression.

3. **New per-call template lock in silo (S3).** Three distinct formulaic patterns appeared — one per LLM call — in run 59 silo: "[Name] - The core tension lies in…" (call 1), "The silo's X creates/is…" (call 2), "The [focus/reliance] on X overlooks…" (call 3). Each call develops its own lock independently, inheriting the shared "hidden cost" rhetorical structure from the examples.

4. **Batch atomicity triggers plan failure on single bad lever (B2, pre-existing but triggered).** Pydantic validates `DocumentDetails` atomically. When one lever in a 5–7 lever batch fails (gta_game: 2 options; parasomnia: `=>` review_lever), the entire batch is rejected. If this occurs on the first call (`len(responses)==0`), the plan fails immediately with no partial recovery. Both run 59 failures stem from this: a single malformed lever killed the full batch. The new examples made this failure mode more likely to trigger for llama3.1.

5. **`expected_calls=3` still hardcoded (B3).** The PR description states the "stale `expected_calls=3` constant" was removed, but code review confirms it was only moved inline at runner.py:523 — still a literal not derived from `min_levers`. The step-gating (B1) works; the latent coupling to `min_levers=15` is still unresolved.

6. **gpt-oss-20b acquired a new formulaic template for hong_kong.** Run 60 (gpt-oss-20b) hong_kong first-call reviews follow "[Name]: The tension lies between X; the options overlook Y." — technically prohibition-compliant (subject is lever name) but still formulaic. This is a new pattern not present in run 53.

---

## Verdict

**NO**: PR #354 is a net regression. Plan success rate dropped from 100% to 94.3% (−2 plans). The key improvement from PR #353 (hong_kong "The options" lock: 0%) was reversed to 100%. Two new Pydantic failure modes were introduced for llama3.1. New per-call template lock patterns appeared in silo and sovereign_identity.

The only unambiguously correct change — the B1 step-gating fix — should be cherry-picked into a separate, focused PR before reverting the rest of the changes.

**What to preserve (cherry-pick to standalone PR):**
- runner.py:517–519 step-gate: `if step == "identify_potential_levers" and pr.calls_succeeded is not None and pr.calls_succeeded < 3`
- The OPTIMIZE_INSTRUCTIONS addition for structural homogeneity (the text is accurate even if the PR violated its own rule).

**What to revert:**
- The game-dev example (`review_lever` at `identify_potential_levers.py:230`).
- The explicit prohibition bullet ("NO starting review_lever with 'The options'…" at line 239).

---

## Recommended Next Change

**Proposal:** Revert the explicit prohibition and replace the game-dev example with a non-gaming, non-test-domain example that uses a structurally distinct rhetorical form from the other two examples.

**Evidence:**
- The hong_kong 0% → 100% regression is directly attributable to (a) S1: the prohibition naming "The options" increases its salience, and (b) S2: the game-dev example gives llama3.1 a domain-adjacent template to copy. Both factors are confirmed by the contrast between PR #353 (no prohibition, no game-dev example → 0% lock) and PR #354 (prohibition added, game-dev example added → 100% lock).
- The synthesis from analysis 36 confirms both agents agree: direction 1 (revert prohibition and game-dev example) is the single highest-impact action. Evidence is strong (runs 52 vs 59, same model, same plan, single variable changed).
- gpt-5-nano parasomnia quality improved slightly with the medical example — this gain is worth preserving if the replacement is done carefully (add medical example *in addition to* rather than replacing the working PR #353 examples).

**Verify in next iteration:**
- **Primary:** Does llama3.1 hong_kong return to 0% "The options" lock after reverting prohibition and game-dev example? Read `002-10-potential_levers.json` for hong_kong across all 3 llama3.1 calls.
- **Primary:** Does llama3.1 silo maintain 0% "The options" lock AND eliminate the new "[Name] - The core tension lies in…" per-call template? Check all 21 silo levers.
- **Primary:** Does plan success rate return to 100%? Watch gta_game and parasomnia for llama3.1.
- **Secondary:** If a medical example replaces the game-dev example, verify it does NOT use "The options" or "The lever" as grammatical subject in its review_lever text. Verify its rhetorical structure differs from the "X but Z reverses the gain" pattern of the remaining two examples.
- **Secondary:** Does gpt-5-nano parasomnia maintain the "Core tension: X; weakness: Y" quality improvement? If this was driven by the medical example specifically, it may regress if the medical example is removed.
- **Haiku partial recoveries:** haiku had 2 partial recoveries (hong_kong, parasomnia) in both PR #353 and PR #354 runs. After B1 fix is confirmed in a standalone PR, verify whether these are true call failures or early-success completions (2 calls × 8+ levers = 16 ≥ min_levers=15). Read haiku's output files to check lever count per call.
- **Domain check:** Confirm the replacement example's domain does not overlap with silo (agricultural sci-fi), hong_kong_game (film/game), gta_game (video-game), parasomnia (medical research), or sovereign_identity (digital identity/policy).

**Risks:**
- A replacement example that uses a gaming-adjacent domain (e.g., "simulation", "player experience") will produce the same domain-collision effect as the game-dev example. Domain check is mandatory before landing.
- If the rhetorical structure of the replacement is still "hidden cost / adversarial reversal," secondary per-call template lock will persist in silo call 1 even after the game-dev example is removed. S3 (structural homogeneity) needs to be addressed alongside domain diversity.
- Reverting the prohibition could allow "The options" lock to re-emerge in models that were previously contained by it (gpt-oss-20b, gpt-5-nano). Monitor whether cloud models show any increase in "The options" as subject after the revert.

**Prerequisite issues:**
- B1 standalone cherry-pick should land before or in parallel with the revert, so it is not lost in the rollback.
- B2 (partial batch salvage) is a correct structural fix and should be implemented before the next domain-diverse example attempt, to prevent single-lever validation failures from killing entire plans.

---

## Backlog

**Resolved by PR #354 (B1 fix only — keep regardless of revert):**
- B1 false partial_recovery for `identify_documents`: correctly gated to `identify_potential_levers`. Confirmed working in run 65 events.jsonl. This fix must be cherry-picked into a standalone PR before reverting PR #354.

**Introduced by PR #354 (revert removes these):**
- hong_kong 100% "The options" lock regression: reverted by removing game-dev example and prohibition.
- silo/sovereign_identity new per-call template lock: reverted by removing game-dev example and prohibition.

**Carry-forward from analysis 35 (unchanged):**
- **Template lock (parasomnia, gta_game):** ~82% and ~78% for llama3.1 (before PR #354). Root cause: domain monoculture + structural homogeneity of examples (S3). Next action: replace game-dev example with a non-test-domain example using a distinct rhetorical structure. Do NOT add explicit prohibition.
- **B2 (batch atomicity):** Pydantic validates `DocumentDetails` atomically. A single bad lever discards all others in the batch. gta_game and parasomnia plan failures in run 59 are direct consequences. Fix: per-lever validation instead of batch validation. Medium effort. Do before next domain-diverse example attempt.
- **B3 (`expected_calls` still hardcoded literal):** runner.py:523 still has `expected_calls=3` as a literal; `min_levers=15` in `identify_potential_levers.py:268` is not mechanically linked. Latent maintenance risk. Fix: define `MIN_LEVERS = 15` at module level and import in runner.py.
- **S3 (structural homogeneity of examples):** All three examples share "apparent benefit → hidden cost" adversarial structure. Replacement example must use a genuinely different rhetorical form. Address alongside domain diversity.
- **I1 (soft template-lock validator):** Add logged warning in `check_review_format` for "the options"/"the lever" openers. Makes lock rate visible without affecting success rate. Low risk, low effort. Bundle with B2 PR.
- **I2 (degenerate review_lever detection):** Add regex check for pure-punctuation values (`=>`, `->`, etc.) with actionable error message. Catches the parasomnia failure mode earlier. Low risk. Bundle with B2 PR.
- **S1/I5 (`lever_index` dead field):** Generated but never transferred to `LeverCleaned`. Wastes tokens. Cleanup PR.
- **S2/I6 (`strategic_rationale` dead field):** ~100 words per call, never consumed downstream. Verify then remove. ~10,500 wasted words/iteration.
- **S4/I2 (option word-count validator):** 15-word minimum in section 6 is unvalidated. llama3.1 silo options still average ~7 words (label-like). Soft warning for options under 10 words.
- **Haiku partial recoveries (hong_kong, parasomnia):** Persistent across PR #353 and PR #354 (2/3 calls both times). Root cause unresolved. Investigate after B2 implementation: are failures on specific levers or entire calls? Is output length the trigger?
- **Per-call example diversity (OPTIMIZE_INSTRUCTIONS):** Template lock re-forms independently per LLM call. A per-call instruction suffix (e.g., "start your review with the lever's financial mechanism", "start with the institutional constraint") may diversify review structure more effectively than global example diversity. Deferred experiment.
